#!/usr/bin/env python3
# ============================================================
# audit_ledger.py — カバレッジ台帳の重複検出（事後監査）
# ============================================================
# 各 domains/<分野>/_ledger.jsonl 内で「実質的に重なるエントリ」を
# 機械検出する。/learn のテーマ選定ゲート(モデル判断)をすり抜けた
# 重複を拾う最終防衛線。
#
# 検出シグナル（どちらかを満たすペアを「重複候補」とする）:
#   (1) タグ交差: 識別性の高いキーワードが 3 語以上一致
#       （ドメイン内で高頻度=汎用なタグは除外して数える）
#   (2) タイトル類似: タイトルの文字 bigram Jaccard が閾値以上
#       （英/日のタグ表記ゆれを越えて拾うための冗長系統）
# 連結成分(union-find)でクラスタ化して報告する。
#
# 使い方:
#   python3 scripts/audit_ledger.py                # 全ドメインを監査
#   python3 scripts/audit_ledger.py golf piano     # 指定ドメイン
#   python3 scripts/audit_ledger.py --new 2026-06-03   # 当日エントリが
#       既習と衝突したクラスタのみ表示。衝突あれば exit 1（daily_run用）
# ============================================================

import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOMAINS_DIR = PROJECT_DIR / "domains"
DOMAINS = ["music", "piano", "golf", "anatomy", "house-hunting", "deutsch", "other"]

# 閾値（検証で調整済み）
TAG_OVERLAP_MIN = 3        # 識別タグの一致語数
TITLE_JACCARD_MIN = 0.42   # タイトル文字bigram Jaccard
COMMON_DF_RATIO = 0.30     # この割合超のドメイン内タグは「汎用」として識別から除外

# 内容のない汎用タグ（学習メタ・言語レベル・冠詞等）。識別集合から常に除外する。
# これらだけで一致しても重複の証拠にならない（例: #ドイツ語 #日常会話）。
GENERIC_TAGS = {
    "日常会話", "日常フレーズ", "日常表現", "日常", "会話", "フレーズ", "口語",
    "ネイティブ表現", "ネイティブ", "表現", "慣用句", "スラング",
    "ドイツ語", "deutsch", "umgangssprache", "slang", "formal", "neutral",
    "telc", "b1", "b1以上", "b1plus", "b2", "a2", "der", "die", "das",
}

NORM_STRIP = re.compile(r"[（）()\[\]【】「」『』—–\-・/／、,，。.\s　…~〜|｜：:;#*＝=＋+]+")


def norm(s: str) -> str:
    return NORM_STRIP.sub("", s).casefold()


def bigrams(s: str):
    s = norm(s)
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else ({s} if s else set())


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_ledger(domain: str):
    path = DOMAINS_DIR / domain / "_ledger.jsonl"
    recs = []
    if not path.exists():
        return recs
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def audit_domain(domain, new_date):
    recs = load_ledger(domain)
    n = len(recs)
    if n < 2:
        return []

    # ドメイン内タグの文書頻度 → 汎用タグを識別集合から除外
    df = {}
    norm_kw = []
    for r in recs:
        kws = {k.casefold() for k in r.get("keywords", [])}
        norm_kw.append(kws)
        for k in kws:
            df[k] = df.get(k, 0) + 1
    common = {k for k, c in df.items() if c / n > COMMON_DF_RATIO} | GENERIC_TAGS

    distinctive = [kws - common for kws in norm_kw]
    title_bg = [bigrams(r["title"]) for r in recs]

    uf = UnionFind(n)
    edges = {}  # (i,j) -> (tag_overlap_count, title_jaccard, shared_tags)
    for i in range(n):
        for j in range(i + 1, n):
            shared = distinctive[i] & distinctive[j]
            tag_ov = len(shared)
            tj = jaccard(title_bg[i], title_bg[j])
            # (a)識別タグ3語一致 (b)タイトル高類似 (c)タグ2語+タイトル中類似の合わせ技
            if (tag_ov >= TAG_OVERLAP_MIN
                    or tj >= TITLE_JACCARD_MIN
                    or (tag_ov >= 2 and tj >= 0.28)):
                uf.union(i, j)
                edges[(i, j)] = (tag_ov, tj, shared)

    # クラスタ集約
    clusters = {}
    for idx in range(n):
        root = uf.find(idx)
        clusters.setdefault(root, []).append(idx)
    clusters = {r: ix for r, ix in clusters.items() if len(ix) >= 2}

    out = []
    for ix in clusters.values():
        ix.sort(key=lambda k: recs[k]["date"])
        # クラスタ内で最も強いシグナルの共有タグを代表に
        best_shared = set()
        for (i, j), (_, _, sh) in edges.items():
            if uf.find(i) == uf.find(ix[0]):
                best_shared |= sh
        if new_date and not any(recs[k]["date"] >= new_date for k in ix):
            continue
        out.append({
            "domain": domain,
            "size": len(ix),
            "dates": [recs[k]["date"] for k in ix],
            "titles": [recs[k]["title"] for k in ix],
            "shared": sorted(best_shared),
        })
    out.sort(key=lambda c: c["size"], reverse=True)
    return out


def main():
    args = sys.argv[1:]
    new_date = None
    if "--new" in args:
        i = args.index("--new")
        new_date = args[i + 1]
        del args[i:i + 2]
    targets = args or DOMAINS

    all_clusters = []
    for d in targets:
        all_clusters.extend(audit_domain(d, new_date))

    mode = f"（--new {new_date}: 当日エントリの衝突のみ）" if new_date else ""
    print(f"=== カバレッジ台帳 重複監査 {mode}===")
    total_entries = 0
    for c in all_clusters:
        total_entries += c["size"]
        print(f"\n■ [{c['domain']}] {c['size']}件が重複候補  共有タグ: {', '.join(c['shared'][:8])}")
        for date, title in zip(c["dates"], c["titles"]):
            print(f"    {date}  {title}")

    print(f"\n=== {len(all_clusters)} クラスタ / 延べ {total_entries} エントリが重複候補 ===")
    if new_date and all_clusters:
        print("!! 当日エントリが既習と衝突しています（要確認）", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
