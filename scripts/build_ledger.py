#!/usr/bin/env python3
# ============================================================
# build_ledger.py — カバレッジ台帳のバックフィル / 追記
# ============================================================
# 各 domains/<分野>/ の日次エントリ(YYYY-MM-DD_*.md)を走査し、
# 機械可読な「カバレッジ台帳」 domains/<分野>/_ledger.jsonl を生成する。
#
# 台帳は /learn のテーマ選定時に既習トピックを O(1) で照合するための
# 軽量インデックス。1エントリ = 1 JSON 行。
#
#   {"date","title","slug","keywords":[...],"depth","sources_tier","related":[...]}
#
# keywords は本文の「**タグ**: #...」行（キュレーション済み正規化タグ）を主に、
# 無ければファイル名トークンで補完する。
#
# 使い方:
#   python3 scripts/build_ledger.py            # 全ドメインを再構築
#   python3 scripts/build_ledger.py music golf # 指定ドメインのみ
#
# 冪等。既存の depth / sources_tier / related は可能な限り保持する。
# ============================================================

import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOMAINS_DIR = PROJECT_DIR / "domains"

# 学習対象ドメイン（_archive は除外）
DOMAINS = ["music", "piano", "golf", "anatomy", "house-hunting", "deutsch", "other"]

ENTRY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$")
TAG_LINE_RE = re.compile(r"^\*\*タグ\*\*\s*[:：]\s*(.+)$")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
HASHTAG_RE = re.compile(r"#([^\s#　]+)")

# ファイル名/タイトルを分割する区切り文字
SPLIT_RE = re.compile(r"[_・/／（）\(\)、,\s　—–\-〜~|｜:：]+")

# マッチに使わない汎用トークン（ノイズ）。語としては台帳に残すが照合の主役にしない。
# （audit_ledger 側でも df ベースで汎用タグを落とすので、ここは最小限）
NOISE_TOKENS = {
    "の", "と", "た", "を", "は", "が", "に", "で", "へ",
    "md", "について", "とは", "仕組み", "基礎", "入門", "技法", "科学", "歴史", "world",
}


def parse_entry(path: Path):
    """1エントリ .md からメタデータを抽出する。"""
    m = ENTRY_RE.match(path.name)
    if not m:
        return None
    date, stem = m.group(1), m.group(2)

    title = stem
    tags = []
    text_head = ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:  # pragma: no cover
        print(f"  ! 読み込み失敗 {path.name}: {e}", file=sys.stderr)
        text = ""

    for line in text.splitlines()[:15]:
        tm = TITLE_RE.match(line)
        if tm and title == stem:
            title = tm.group(1)
        gl = TAG_LINE_RE.match(line.strip())
        if gl:
            tags = HASHTAG_RE.findall(gl.group(1))
    text_head = text

    # ファイル名トークン（タグの補完源）
    file_tokens = [t for t in SPLIT_RE.split(stem) if t]

    # keywords = タグ（主）＋ ファイル名トークン（補完）。順序保持で重複排除。
    seen = set()
    keywords = []
    for kw in tags + file_tokens:
        k = kw.strip()
        if not k:
            continue
        low = k.lower()
        if low in seen:
            continue
        if low in NOISE_TOKENS:
            continue
        seen.add(low)
        keywords.append(k)

    return {
        "date": date,
        "title": title,
        "slug": stem,
        "keywords": keywords,
        "depth": "",          # intro / deepening — 新規エントリが /learn で埋める
        "sources_tier": "",   # tier1 / tier2 / blog — 同上
        "frontier_consumed": [],
        "related": [],
        "has_tags": bool(tags),
    }


def load_existing(ledger_path: Path):
    """既存台帳を slug -> record で読み込み（depth等の手動補強を保持するため）。"""
    existing = {}
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                existing[rec.get("slug", rec.get("date"))] = rec
            except json.JSONDecodeError:
                continue
    return existing


def build_domain(domain: str):
    ddir = DOMAINS_DIR / domain
    if not ddir.is_dir():
        print(f"  ! ドメインが存在しない: {domain}", file=sys.stderr)
        return 0
    ledger_path = ddir / "_ledger.jsonl"
    existing = load_existing(ledger_path)

    records = []
    for path in sorted(ddir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        rec = parse_entry(path)
        if rec is None:
            continue
        # 既存の手動補強（depth/sources_tier/frontier_consumed/related）を引き継ぐ
        prev = existing.get(rec["slug"])
        if prev:
            for f in ("depth", "sources_tier", "frontier_consumed", "related"):
                if prev.get(f):
                    rec[f] = prev[f]
        records.append(rec)

    records.sort(key=lambda r: (r["date"], r["slug"]))
    with ledger_path.open("w", encoding="utf-8") as f:
        for rec in records:
            out = {k: rec[k] for k in
                   ("date", "title", "slug", "keywords", "depth",
                    "sources_tier", "frontier_consumed", "related")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    no_tags = sum(1 for r in records if not r["has_tags"])
    note = f"（タグ行なし {no_tags}件はファイル名から補完）" if no_tags else ""
    print(f"  {domain:14s}: {len(records):3d} エントリ -> {ledger_path.relative_to(PROJECT_DIR)} {note}")
    return len(records)


def main():
    targets = sys.argv[1:] or DOMAINS
    total = 0
    print("=== カバレッジ台帳の構築 ===")
    for d in targets:
        total += build_domain(d)
    print(f"=== 完了: 計 {total} エントリ ===")


if __name__ == "__main__":
    main()
