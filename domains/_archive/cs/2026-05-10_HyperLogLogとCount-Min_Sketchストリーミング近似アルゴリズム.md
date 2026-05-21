# HyperLogLog と Count-Min Sketch — ストリーミング近似アルゴリズム
**日付**: 2026-05-10
**分野**: cs
**タグ**: #HyperLogLog #CountMinSketch #StreamingAlgorithms #Probabilistic #Flajolet #Cormode

## 学んだこと

### ストリーミングモデルの問題設定
ストリーミングモデルでは、無限長のデータ列 $a_1, a_2, \ldots$ が一度ずつ流れ、**メモリは O(polylog n)** に制限される。このモデルで以下の問いに答える:
1. **Count-distinct (cardinality)**: 異なる要素が何種類あるか?
2. **Frequency estimation**: 要素 $x$ が何回出現したか?
3. **Heavy hitters**: 最頻要素 (top-k) は?
4. **Quantile estimation**: 中央値・90 パーセンタイルは?

正確解は要素を全保存する必要がありメモリ O(n)。**これを O(polylog n) で近似する**のがストリーミングアルゴリズム。HyperLogLog (1) と Count-Min Sketch (2,3) は最も成功した実装。

### HyperLogLog (HLL) の発明史と核心アイデア
1984 年の **Flajolet–Martin (FM) アルゴリズム** が出発点: ハッシュ値 $h(x) \in \{0,1\}^L$ の **末尾連続 0 ビット数** $\rho(h(x))$ を取り、その最大値 $R = \max \rho$ を観測すれば、カーディナリティ $n \approx 2^R$ と推定できる。理由: $\rho \geq k$ となる確率は $2^{-k}$ なので、$n$ 個の要素から最大 $\rho$ を取れば期待値は $\log_2 n$。

しかし FM は分散が大きすぎる ── **1 つのハッシュで運悪く高い $\rho$ が出ると推定値が爆発**する。1985 年の **LogLog** (Durand & Flajolet) は要素を $m$ バケットに分け、各バケットで $\rho$ の最大値を独立に取り、**算術平均** を取った。さらに 2007 年の **HyperLogLog** (Flajolet, Fusy, Gandouet, Meunier) は算術平均ではなく **調和平均 (harmonic mean)** を使うことで分散を最小化:

$$
\hat{n} = \alpha_m m^2 \left(\sum_{j=1}^{m} 2^{-M_j}\right)^{-1}
$$

ここで $M_j$ はバケット $j$ の最大 $\rho$、$\alpha_m$ は数値定数 (約 0.7213 for m=16384)。

**メモリ**: バケット数 $m = 2^{14}$ (16384) なら各 5-6 ビットで合計 **約 12 KB**。**精度**: 標準誤差 $\approx 1.04 / \sqrt{m} \approx 0.81\%$。これで**カーディナリティが 1 兆でも 10 兆でも誤差 1% 程度**。Redis、Google BigQuery、AWS Redshift などで実装され、ユニークビジター計測の事実上の標準。

### Count-Min Sketch (CMS) の構造
2003 年の **Cormode & Muthukrishnan**。$d$ 個の独立ハッシュ関数 $h_1, \ldots, h_d : U \to [w]$ を持ち、$d \times w$ の整数配列 $C$ を保持する。

**更新** (要素 $x$ の出現): 各 $i = 1, \ldots, d$ について $C[i, h_i(x)] \mathrel{+}= 1$.

**クエリ** (要素 $x$ の頻度推定): $\hat{f}(x) = \min_{i} C[i, h_i(x)]$.

**理論保証**: パラメータを $w = \lceil e/\epsilon \rceil$, $d = \lceil \ln(1/\delta) \rceil$ と取れば、確率 $1 - \delta$ で誤差 $\leq \epsilon \cdot N$ ($N$ は総出現数)。**特徴**: 推定値は**常に過大** (overestimate)。理由は他要素のカウントが衝突で加算されるから。**過小はない**ことが正確性保証の鍵 ── 「最低でもこれだけは出現した」が保証される。

**メモリ**: $\epsilon = 0.001$ (0.1% 誤差), $\delta = 0.01$ (99% 信頼) なら $w = 2719$, $d = 5$ で**約 54 KB**。実用的に小さい。

### 設計対比 — HLL と CMS
| | HyperLogLog | Count-Min Sketch |
|---|---|---|
| 解く問題 | 異なり数 (cardinality) | 個別要素の頻度 |
| ハッシュ数 | 1 個 (バケット分割) | $d$ 個 (独立) |
| 統計値 | 最大 $\rho$ + 調和平均 | 最小値 |
| 誤差バイアス | なし (両側) | 常に過大 |
| メモリ | $O(\log \log n)$ per bucket | $O(d \times w)$ |
| 集合演算 | union 容易 (max), intersection 困難 | 重み付け加算で union |

両者ともに**「データを直接保存せず、構造を記録する」確率的データ構造**。ロスレスではないが、**情報理論的に最適**な圧縮率 (HLL の場合 Munro-Paterson 1980 の下限に漸近一致)。

### 実装上のチューニング
**HLL Sparse Encoding**: バケットの大半が 0 の状態 (要素少数時) を、ペアのリストで疎表現。Redis HLL は 16384 バケットの dense (12 KB) と 約 3 KB の sparse を**自動切り替え**。
**HLL++** (Heule et al. 2013, Google): 小カーディナリティでの bias 補正、sparse 表現の効率化、64 ビットハッシュへの拡張。Google BigQuery が採用。
**HyperLogLogLog** (Karppa & Pagh 2022): HLL を**さらに圧縮**して同じ精度を約 70% のメモリで達成。バケット内の最大値の差分を Golomb-Rice 符号化。
**Conservative Update for CMS** (Estan & Varghese): 更新時にカウンタを最小値の合のみ増やす変種で、過大誤差を約 3 倍削減。実用的な最適化。

### 応用例
- **HLL**: Google Analytics ユニークユーザー数、Twitter のフォロワー差分、Facebook の DAU/MAU 統計、Reddit のユニーク投票者集計、ネットワークトラフィック分析 (異なる送信元 IP 数)。
- **CMS**: Google AdSense クリック頻度推定、Cisco のフロー分析 (heavy hitters 検出 → DDoS 緩和)、Cassandra/ScyllaDB の hot key 検出、ML 特徴量カウンティング (TensorFlow の `count_table` 内部実装)、自然言語処理の n-gram 頻度 (Google の Web 1T 5-gram 大規模データ)。

## 気づき・洞察

### 「正確を諦めることで巨大スケールに到達」
古典的アルゴリズム理論は worst-case complexity を最小化する設計を追求した。だがビッグデータ時代には**「計算可能な近似」が「不可能な厳密解」より価値がある**。HLL と CMS は **誤差を確率的に保証することで O(polylog) 空間に到達**した。これは**「絶対精度から確率精度への転換」**であり、機械学習の確率的勾配降下 (SGD) と同じ哲学転換。

### Harmonic Mean の優位性
HLL が算術平均 (LogLog) より調和平均で分散を減らす理由は深い。**調和平均は外れ値 (極端に大きな値) の影響を受けにくい**。$2^{-M_j}$ という指数減衰量に対して調和平均を取ることは、$M_j$ そのものに対しては log-mean を取ることに近い。**統計的推定量の選択がメモリ効率を決定する**好例。

### Min vs Max の対称性
HLL は max を取る、CMS は min を取る ── 一見対称だが背後の原理は異なる。HLL の max は **「観測した最も希少な事象の珍しさ」を活用** (希少な要素の出現確率が cardinality と相関)。CMS の min は **「衝突による過大推定の最小化」** (複数推定の min は偽陽性を減らす)。**最大と最小はそれぞれ異なる情報を抽出する**。

### Bloom Filter ファミリーとの関係
**Bloom Filter** (1970) → 集合所属判定。**Cuckoo Filter** (2014) → 削除可能な Bloom。**HyperLogLog** (2007) → 異なり数。**Count-Min Sketch** (2003) → 頻度推定。**Quotient Filter** (2012) → SSD 効率的な Bloom。**MinHash** (1997) → Jaccard 類似度。これらは**「ハッシュベース確率的圧縮」**ファミリーの異なる用途への展開。各々がトレードオフを別の場所に置いた美しい設計空間。

## 他分野との接続

- **bread (並列発酵プロセス)**: 4 種類の独立な発酵プロセス (酵母・LAB・プロテアーゼ・アミラーゼ) の独立性は、HLL の独立バケットと類比的。**独立な部分の統合で全体を推定**。
- **anatomy (固有受容感覚)**: 筋紡錘 (位置) と GTO (張力) の sensor fusion は、HLL のバケット平均と同じ「複数の独立観測の統合」。**冗長な観測を統合することで誤差を圧縮**。
- **piano (Invisible Rotation の合成)**: 指運動と前腕回旋の合成で速度限界を超えるのは、HLL の harmonic mean が分散を圧縮するのと類比的。**独立要素の合成で単独限界を超える**。
- **golf (DECADE / Strokes Gained)**: 個別ショットの統計を集計してプレーヤー総合スコアを推定するのは、CMS の頻度カウントから集約統計を作るのと同型。**個別観測から全体傾向を抽出**。
- **tech (Rekor transparency log)**: Rekor は Bloom filter で entry の高速検索を行う。**確率的データ構造が分散システムの実用解**。
- **music (Shostakovich の引用)**: 第 8 番が過去作の主題を「圧縮表現」として埋め込むのは、HLL がストリームを圧縮表現で要約するのと類比的。**情報の選択的保存**。

## 次に深掘りしたいこと

- **t-digest** (Ted Dunning 2013) ── パーセンタイル推定の確率的データ構造。CMS と異なる原理 (centroid clustering)。
- **Theta Sketches** (Apache DataSketches) ── HLL より union/intersection 共に高速な集合演算用スケッチ。
- **Differential Privacy との関係** ── HLL/CMS のノイズはプライバシー保護に転用可能か (RAPPOR, Apple iOS の telemetry)。
- **Quantum streaming algorithms** ── 量子ビットを使ったストリーミング近似の理論限界。
- **HyperLogLog の bias** が小カーディナリティで大きい理由を harmonic mean の数値解析で深く理解する。

---

**主要参考ソース**:
- [Flajolet, Fusy, Gandouet, Meunier (2007) "HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm" (PDF)](https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf)
- [Wikipedia: HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog)
- [Redis: Count-Min Sketch — The Art and Science of Estimating Stuff](https://redis.io/blog/count-min-sketch-the-art-and-science-of-estimating-stuff/)
- [Karppa & Pagh (2022) "HyperLogLogLog: Cardinality Estimation With One Log More" (arXiv)](https://arxiv.org/pdf/2205.11327v1)
- [Wikipedia: Count-distinct problem](https://en.wikipedia.org/wiki/Count-distinct_problem)
