#!/usr/bin/env python3
"""
fetch_x.py — config/x_accounts.txt のアカウントの直近ツイートを取得して
data/x/YYYY-MM-DD.json に保存する（デイリーレポートの「今日のX」セクション用）。

使い方:
    python3 scripts/fetch_x.py [YYYY-MM-DD]   # 省略時はローカル今日

- API: twitterapi.io  (GET https://api.twitterapi.io/twitter/user/last_tweets、ヘッダ X-API-Key)
  レスポンスは {status, code, msg, data:{pin_tweet, tweets:[...]}, has_next_page, next_cursor}
- 認証キー: 環境変数 TWITTERAPI_IO_KEY（無ければ config/.env から読む）
- 取得範囲: 実行時刻から過去 WINDOW_HOURS 時間（デフォルト24h）
- リプライは last_tweets のデフォルト挙動どおり含めない。RT・引用は含める。固定ツイート(pin)は無視
- アカウント単位のエラーは握りつぶして続行し、出力 JSON は必ず書く。
  ハードエラー（キー未設定／日付不正）のときだけ非ゼロ終了
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS_FILE = ROOT / "config" / "x_accounts.txt"
ENV_FILE = ROOT / "config" / ".env"
OUT_DIR = ROOT / "data" / "x"

API_BASE = "https://api.twitterapi.io"
ENDPOINT = "/twitter/user/last_tweets"
WINDOW_HOURS = 24
MAX_PAGES_PER_USER = 10         # 1ページ ~20件。10ページで上限 ~200件。古いページに当たれば自動で止まる安全弁
REQUEST_TIMEOUT = 30
USER_AGENT = "DailyLearning-fetch_x/1.0 (+https://github.com/YamamotoNaoyuki/DailyLearning)"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COST_PER_1K_TWEETS = 0.15       # twitterapi.io の概算（表示用のみ）
UTC = dt.timezone.utc


# --- 設定読み込み ------------------------------------------------------------
def load_api_key() -> Optional[str]:
    key = os.environ.get("TWITTERAPI_IO_KEY")
    if key and key.strip():
        return key.strip()
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TWITTERAPI_IO_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def read_accounts() -> List[str]:
    if not ACCOUNTS_FILE.is_file():
        return []
    out: List[str] = []
    seen = set()
    for raw in ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        handle = line.split()[0].lstrip("@")
        if handle and handle.lower() not in seen:
            seen.add(handle.lower())
            out.append(handle)
    return out


# --- API ---------------------------------------------------------------------
def api_get(path: str, params: Dict[str, str], key: str) -> Dict[str, Any]:
    url = API_BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"X-API-Key": key, "Accept": "application/json", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            body = ""
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body}") from None


# --- ツイートの整形 ----------------------------------------------------------
def parse_created_at(s: str) -> Optional[dt.datetime]:
    if not s:
        return None
    s = s.strip()
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except ValueError:
        pass
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _bigger_avatar(url: str) -> str:
    # pbs.twimg.com の profile_images は "_normal.jpg" → "_bigger.jpg" で少し高解像度
    return re.sub(r"_normal(\.\w+)(\?.*)?$", r"_bigger\1", url) if url else url


def _author(o: Dict[str, Any]) -> Dict[str, Any]:
    a = o.get("author") or o.get("user") or {}
    return {
        "userName": a.get("userName") or a.get("screen_name") or a.get("username") or "",
        "name": a.get("name") or "",
        "avatar": _bigger_avatar(a.get("profilePicture") or a.get("profile_image_url_https") or ""),
        "verified": bool(a.get("isBlueVerified") or a.get("isVerified")),
    }


def _urls(o: Dict[str, Any]) -> List[Dict[str, str]]:
    out = []
    for u in (o.get("entities") or {}).get("urls") or []:
        tco = u.get("url") or ""
        exp = u.get("expanded_url") or u.get("expandedUrl") or ""
        if tco and exp:
            out.append({"tco": tco, "expanded": exp, "display": u.get("display_url") or u.get("displayUrl") or exp})
    return out


def _media(o: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    raw = None
    for src in ("extendedEntities", "extended_entities", "entities"):
        v = o.get(src)
        if isinstance(v, dict) and v.get("media"):
            raw = v["media"]
            break
    for m in raw or []:
        if not isinstance(m, dict):
            continue
        mtype = (m.get("type") or "photo").lower()
        img = m.get("media_url_https") or m.get("media_url") or m.get("preview_image_url") or ""
        link = m.get("expanded_url") or m.get("expandedUrl") or m.get("url") or ""
        if not img:
            continue
        items.append({"type": mtype, "image": img, "link": link})
    return items


def _slim_min(o: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(o.get("id") or o.get("id_str") or ""),
        "text": o.get("text") or o.get("full_text") or o.get("fullText") or "",
        "createdAt": o.get("createdAt") or o.get("created_at") or "",
        "url": o.get("url") or o.get("twitterUrl") or "",
        "author": _author(o),
        "urls": _urls(o),
        "media": _media(o),
    }


def slim_tweet(t: Dict[str, Any]) -> Dict[str, Any]:
    out = _slim_min(t)
    out["isReply"] = bool(t.get("isReply"))
    out["inReplyToUsername"] = t.get("inReplyToUsername") or ""
    out["lang"] = t.get("lang") or ""
    out["counts"] = {
        "like": t.get("likeCount") or 0,
        "retweet": t.get("retweetCount") or 0,
        "reply": t.get("replyCount") or 0,
        "quote": t.get("quoteCount") or 0,
    }
    rt = t.get("retweeted_tweet") or t.get("retweetedTweet")
    if isinstance(rt, dict):
        out["retweet_of"] = _slim_min(rt)
    qt = t.get("quoted_tweet") or t.get("quotedTweet")
    if isinstance(qt, dict):
        out["quote_of"] = _slim_min(qt)
    return out


def _ts(o: Dict[str, Any]) -> dt.datetime:
    return parse_created_at(o.get("createdAt", "")) or dt.datetime.min.replace(tzinfo=UTC)


# --- 1アカウント分の取得 -----------------------------------------------------
def fetch_user(handle: str, key: str, cutoff: dt.datetime) -> Dict[str, Any]:
    tweets: List[Dict[str, Any]] = []
    profile: Dict[str, Any] = {}
    cursor = ""
    pages = 0
    err: Optional[str] = None
    while pages < MAX_PAGES_PER_USER:
        try:
            data = api_get(ENDPOINT, {"userName": handle, "cursor": cursor}, key)
        except Exception as e:  # noqa: BLE001
            err = str(e)
            break
        if str(data.get("status") or "").lower() not in ("success", "ok", ""):
            err = data.get("msg") or data.get("message") or f"API status={data.get('status')!r}"
            break
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        page = inner.get("tweets") or data.get("tweets") or []
        stop = False
        for t in page:
            if not isinstance(t, dict):
                continue
            au = _author(t)
            if not profile and (au.get("userName", "").lower() == handle.lower()):
                profile = au
            cat = parse_created_at(t.get("createdAt") or t.get("created_at") or "")
            if cat is not None and cat < cutoff:
                stop = True
                break
            tweets.append(slim_tweet(t))
        pages += 1
        if stop or not data.get("has_next_page"):
            break
        cursor = data.get("next_cursor") or data.get("nextCursor") or ""
        if not cursor:
            break
        time.sleep(0.3)
    tweets.sort(key=_ts, reverse=True)
    return {
        "handle": handle,
        "name": profile.get("name", ""),
        "avatar": profile.get("avatar", ""),
        "verified": bool(profile.get("verified")),
        "tweets": tweets,
        "error": err,
        "pages_fetched": pages,
    }


# --- メイン ------------------------------------------------------------------
def main(argv: List[str]) -> int:
    pos = [a for a in argv[1:] if a and not a.startswith("-")]
    date = pos[0] if pos else dt.date.today().isoformat()
    if not DATE_RE.match(date):
        sys.exit(f"エラー: 日付は YYYY-MM-DD 形式で（受け取った値: {date!r}）")

    key = load_api_key()
    if not key:
        sys.exit("エラー: TWITTERAPI_IO_KEY が未設定です（環境変数 or config/.env）。")

    handles = read_accounts()
    if not handles:
        print(f"警告: {ACCOUNTS_FILE} にアカウントがありません。空の {date}.json を書きます。", file=sys.stderr)

    now = dt.datetime.now(UTC)
    cutoff = now - dt.timedelta(hours=WINDOW_HOURS)

    accounts_out: List[Dict[str, Any]] = []
    total = 0
    errors = 0
    for h in handles:
        res = fetch_user(h, key, cutoff)
        n = len(res["tweets"])
        total += n
        if res["error"]:
            errors += 1
            print(f"  ! @{h}: {res['error']}", file=sys.stderr)
        else:
            print(f"  @{h}: {n} 件", file=sys.stderr)
        accounts_out.append(res)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date,
        "fetched_at": now.isoformat(),
        "window_hours": WINDOW_HOURS,
        "source": "twitterapi.io",
        "include_replies": False,
        "accounts": accounts_out,
    }
    out_path = OUT_DIR / f"{date}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    cost = total * COST_PER_1K_TWEETS / 1000.0
    print(
        f"→ {out_path.relative_to(ROOT)} : {len(handles)} アカウント / {total} 投稿 "
        f"/ 概算 ${cost:.4f}（エラー {errors} 件）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
