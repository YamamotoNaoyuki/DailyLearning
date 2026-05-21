# Burrows-Wheeler変換とFM-index：圧縮全文検索の設計哲学
**日付**: 2026-05-15  
**分野**: cs  
**タグ**: #BWT #FMindex #SuffixArray #DataCompression #StringMatching #bzip2 #bioinformatics

## 学んだこと

### Burrows-Wheeler 変換（BWT）の中心アイデア

1983 年に David Wheeler が考案し、1994 年に Burrows と Wheeler の共著論文として発表された変換アルゴリズム。**文字列を可逆的に並べ替えて、同じ文字が連続した「ラン」になりやすい形に変える**。これだけだと「並び替えで何が嬉しいのか」が見えないが、後段の **MTF (Move-to-Front) + ハフマン or 算術符号化** と組み合わせることで、汎用テキストで gzip を上回る圧縮率を達成する。bzip2 (1996) はまさにこの設計で実用化された。

### BWT の構成手順

入力 T = "BANANA$"（$ は終端記号、辞書順最小）

1. **全ての循環シフトを生成**:
```
BANANA$
ANANA$B
NANA$BA
ANA$BAN
NA$BANA
A$BANAN
$BANANA
```

2. **辞書順にソート（Burrows-Wheeler matrix）**:
```
$BANANA
A$BANAN
ANA$BAN
ANANA$B
BANANA$
NA$BANA
NANA$BA
```

3. **最終列（L列）を取り出す**: `ANNB$AA` ← これが BWT(T)

逆変換は L 列と F 列（最初の列、L 列をソートしたもの）の対応関係から **LF mapping** を使って一意に復元できる。これが BWT の魔法：**並べ替えても情報を失わない**。

### なぜ BWT 後の文字列は圧縮されやすいか

英語のような自然言語では、同じ文字の前にはしばしば同じ文字が来る（"th" の前は空白か "e"、"qu" の前は母音）。BWT は「**ある文脈で出現する文字を集める**」変換なので、結果として同じ文字が連続する傾向が強くなる。例えば英語テキストでは BWT 後に "the th th th" のような「the」関連の文字が固まる。

これにより：
- **Run-Length Encoding (RLE)** で効率的に圧縮できる
- **MTF**（最近使った文字ほど短い符号）が効く（同じ文字が連続するから「最近使った」のヒット率が高い）
- **算術符号化**で情報理論の限界（エントロピー）に迫れる

### Suffix Array との関係：BWT は実は suffix array から計算できる

辞書順ソートしたシフトを「$ までで打ち切る」と、それは元文字列の **suffix array（接尾辞配列）** に他ならない：

```
$BANANA  → suffix #6: $
A$BANAN → suffix #5: A$
ANA$BAN → suffix #3: ANA$
ANANA$B → suffix #1: ANANA$
BANANA$ → suffix #0: BANANA$
NA$BANA → suffix #4: NA$
NANA$BA → suffix #2: NANA$
```

つまり suffix array = [6, 5, 3, 1, 0, 4, 2]。BWT[i] = T[SA[i] - 1]（mod n）として計算できる。SA は線形時間 O(n) で構築できる（SA-IS, DC3 等）ので、BWT も実用的に O(n) で構築できる。

### FM-index：圧縮しながら全文検索

2000 年に Paolo Ferragina と Giovanni Manzini が発表した FM-index は、BWT を「**圧縮されたまま検索可能な索引**」に変える設計。**「圧縮 + 索引」を同時に達成する**という、それまで不可能だと思われていた組み合わせを実現した。

FM-index の構成要素：
1. **BWT(T)** = L 列
2. **C 配列**: C[c] = T に含まれる「c より辞書順で小さい文字」の総数
3. **Occ(c, k)** 関数: L[0..k] における c の出現回数
4. **Sampled suffix array**: 位置復元のため、SA の一部だけ保存（典型: 32要素ごと）

これらの合計サイズは、**元データの圧縮形に近い**（厳密にはエンピリカル・エントロピー H_k の n+o(n) ビット程度）。

### Backward Search アルゴリズム

パターン P = "ANA" を T = "BANANA" から検索する場合：

**通常の検索（forward）**: 左から右に走査 → O(n) または接尾辞木の O(|P|)
**FM-index の backward search**: **パターンを後ろから処理** → O(|P|) で範囲を絞る

具体的には、BWM の行範囲 [sp, ep] を保持しながら、パターンの最後の文字から順に：

```
for i = |P|-1 downto 0:
    c = P[i]
    sp = C[c] + Occ(c, sp - 1) + 1
    ep = C[c] + Occ(c, ep)
    if sp > ep: pattern not found
```

LF mapping の本質：BWM 上で「L 列の c から、対応する F 列の c に飛ぶ」と、それは「c がパターンの末尾にある接尾辞群」に対応する。これを繰り返すことで、パターン全体を含む接尾辞範囲が得られる。

### Occ(c, k) の効率実装：Wavelet Tree

素朴に Occ を毎回数えると O(n) かかってしまい、O(|P|n) に膨れる。これを定数時間にするための工夫：

- **Block-wise rank**: BWT を一定サイズのブロックに分割し、各ブロックの累積カウントを保存（典型: 512ビットブロック）
- **Wavelet Tree**: 多文字アルファベットを二分木に再帰的に分解し、各ノードで bitmap rank を行う。空間 n log σ + o(n log σ) ビットで O(log σ) クエリ
- **RLBWT (Run-Length BWT)**: BWT 上のラン構造を活用し、空間を r（ラン数）に比例するレベルまで圧縮

### 位置の復元：Sampled Suffix Array + LF Mapping

パターンマッチ位置を出力するには、BWT 内の行番号から元テキストの位置を求める必要がある。SA を全部保存すると O(n log n) ビットになり圧縮が台無し。

解決：**SA を 1/k 間引いて保存**し、未保存位置からは LF mapping を繰り返し適用して「サンプル位置に到達するまで戻る」。各位置の復元は O(k) ステップ、全体で O(occ × k) 時間。k = 32 程度で実用十分。

### バイオインフォマティクスでの大成功

ヒトゲノム（30億塩基）を fasta テキストとして保持すると 3GB。BWT + FM-index にすると **約 1-2GB** に収まり、しかも：

- 短いシーケンシングリード（100-150 bp）の検索が **数ミリ秒**
- メモリ常駐できる（昔は不可能だった）
- 並列化が容易

これを利用した read aligner：
- **Bowtie**（Langmead et al., 2009）：最初の FM-index ベース read aligner
- **BWA（Burrows-Wheeler Aligner）**：Heng Li, 2009. BWA-MEM が現在のデファクト
- **HISAT2**: スプライス対応版

NGS（次世代シーケンシング）時代の到来は、FM-index の存在によって可能になったと言っても過言ではない。

### 拡張：双方向 FM-index と RLBWT

- **Bidirectional FM-index**: パターンを左右どちらにも伸ばせる。ロングリードや近似検索で有用
- **RLBWT (Run-Length BWT)**: ハプロタイプデータのような繰り返しの多い文字列に対し、空間を r-bit（ラン数に比例）に圧縮
- **r-index**（Gagie, Navarro, Prezza, 2018）: 反復配列の極限圧縮

これらにより、ペタバイト級のゲノムコレクション（PanGenome）への索引付けが現実的になりつつある。

## 気づき・洞察

**「変換 + 索引 + 圧縮」の同時達成は不可能と思われていた**。情報理論的には、エントロピー限界に達した圧縮データはランダムビットに見えるはずで、その上で構造的検索ができるとは思えなかった。FM-index はこの直感を覆し、**「圧縮された表現は元データの全ての構造を持つ」**ことを示した。これは情報理論と計算可能性の境界を押し広げた歴史的成果。

**「逆順に処理する」発想の力**。BFS/DFS、動的計画法、検索アルゴリズム全般で「素朴に前から処理する」ものを「後ろから処理する」と劇的に効率化できる場合がある。Backward search はその典型で、forward では指数的に分岐する探索が後ろからだと範囲の単調絞り込みになる。

**接尾辞構造の普遍性**。Suffix array, suffix tree, BWT, FM-index は同じ「接尾辞全体の構造」を異なる視点で表現したもの。それぞれ得意分野が違う：
- Suffix tree: 構造的検索、最長共通部分列
- Suffix array: 省メモリ、シンプル
- BWT/FM-index: 圧縮 + 検索

**Wavelet Tree は「アルファベットの分割統治」**。一見特殊な構造に見えるが、本質は「多値関数を二分木で表現する」一般技法。多倍長計数、レンジクエリ、k番目最小値検索などにも応用される。

## 他分野との接続

- **tech / Apache Arrow**: [[Apache_Arrowと列指向ゼロコピー・データ交換]] の列指向ストレージは「カラム内で同じパターンが出る」前提に立つ。BWT も「コンテキスト内で同じ文字が出る」前提に立つ。**冗長性を発見して圧縮する設計**として同根
- **music / シベリウス第7**: 単一楽章交響曲が「主題の冗長性を圧縮して新しい形式を作る」のに対し、BWT は「テキストの冗長性を圧縮して新しい表現を作る」。**冗長性の発見と再表現**として同型
- **piano / フーガ**: 主題の様々な変形（反転、拡大、ストレット）を一つの胚種から導出するのは、BWT が「全ての回転シフトから一つの並び替えを導出する」のと類似
- **anatomy / 神経分類**: Erlanger-Gasser 分類は「神経線維を機能と速度で分類する」が、これは線維の本質的属性（直径・ミエリン）の「索引化」。BWT も文字の本質的属性（コンテキスト）で並び替える
- **bread / DDT 計算**: BWT が「データの構造を活かして圧縮する」のと、DDT が「複数温度源を加重平均で統合する」のは、**情報の本質を一つの数式に集約する**という意味で類似

## 次に深掘りしたいこと

- r-index と pan-genome 索引付けの最新技術
- LZ77/LZ78 系（gzip）と BWT 系（bzip2, zstd?）の圧縮率・速度比較
- Wavelet Matrix（Wavelet Tree の改良版）の構造
- BWA-MEM の seed-and-extend 戦略の詳細
- Compressed suffix tree と LZ-index の比較
- 量子コンピューティングでの文字列検索（Grover algorithm）への接続

## 主要参考ソース
- [Wikipedia: Burrows–Wheeler transform](https://en.wikipedia.org/wiki/Burrows%E2%80%93Wheeler_transform)
- [Wikipedia: FM-index](https://en.wikipedia.org/wiki/FM-index)
- [Ben Langmead: BWT and FM Index Lecture Notes (JHU)](https://www.cs.jhu.edu/~langmea/resources/lecture_notes/bwt_and_fm_index.pdf)
- [Ferragina & Manzini: Opportunistic Data Structures with Applications (2000)](https://dl.acm.org/doi/10.1109/SFCS.2000.892127)
- [Bioinformatics Lecture Notes: BWT and FM-index](https://mpop.gitbook.io/bioinformatics-lecture-notes/string-indexing/the-burrows-wheeler-transform-and-the-fm-index)
- [Alex Bowe: FM-Indexes and Backwards Search](https://www.alexbowe.com/fm-index/)
