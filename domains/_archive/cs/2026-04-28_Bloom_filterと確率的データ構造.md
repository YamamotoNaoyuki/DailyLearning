# Bloom Filter — 偽陽性を許す確率的メンバーシップ
**日付**: 2026-04-28
**分野**: cs
**タグ**: #bloom_filter #確率的データ構造 #ハッシュ #メンバーシップ #LSM_tree #cache

## 学んだこと

### 1. Bloom Filter の基本構造——「いない」と確実に言える装置

Bloom Filter (Burton Howard Bloom, 1970) は **「ある要素が集合に含まれているか」**を問い合わせる**確率的データ構造**。特徴は:

- **要素を実際には保存しない** ——ビット配列だけを保持
- **空間効率が極めて高い** ——1要素あたり 約10ビットで誤り率 1%
- **偽陽性 (false positive) はあるが偽陰性 (false negative) はない**——「**いる**」と言われたら本当はいないかもしれないが、「**いない**」と言われたら本当にいない

#### 構造
- **m ビット**の配列 (初期は全 0)
- **k 個の独立なハッシュ関数** $h_1, h_2, ..., h_k$ : それぞれ要素を $[0, m)$ 区間にマップ

#### 操作
- **挿入 (insert)**: 要素 $x$ について、 $h_1(x), h_2(x), ..., h_k(x)$ の位置のビットを 1 にする
- **問い合わせ (query)**: 要素 $x$ について、すべての位置 $h_i(x)$ が 1 ならば**「含まれる可能性あり」**、1 つでも 0 なら**「含まれない」(確定)**

要素は決して**取り出せない**——ハッシュは一方向。**削除も基本不可**(削除版は Counting Bloom Filter)。

### 2. 偽陽性率の数学

m ビットの配列、k 個のハッシュ、n 個の要素を挿入したとき、**特定のビットが0のままの確率**:

$$P(\text{bit} = 0) = \left(1 - \frac{1}{m}\right)^{kn} \approx e^{-kn/m}$$

クエリで全 k 個のビットがすべて 1 となる確率 (=偽陽性率):

$$\varepsilon \approx \left(1 - e^{-kn/m}\right)^k$$

この式から、与えられた m, n に対する**最適な k**:

$$k_{\text{opt}} = \frac{m}{n} \ln 2 \approx 0.693 \cdot \frac{m}{n}$$

このとき**最適偽陽性率**は:

$$\varepsilon_{\text{opt}} = (0.5)^k = (0.5)^{(m/n)\ln 2}$$

#### 直感的に
- **k が小さすぎる**と、ビットが立たないので偽陽性は低いが**ハッシュ衝突で1つのビットが偶然立つ確率**が支配
- **k が大きすぎる**と、各クエリで多くのビットを見るので**確率的にすべて立っている確率**が増加
- 中間に**最適値**がある——典型的に **k = 7〜10**

#### 1% 偽陽性なら 9.6 ビット/要素
偽陽性率 1% を達成するには:
- $\varepsilon = 0.01$
- 必要 $m/n = -\ln(0.01) / (\ln 2)^2 \approx 9.585$

つまり **要素1つにつき約 10 ビット**で 1% 誤り率。**要素のサイズ (例えば100バイト) と無関係**——これが Bloom Filter の威力。

### 3. 厳密な解析と修正——理論の盲点

**伝統的な式 $\varepsilon \approx (1 - e^{-kn/m})^k$ は近似**。Bose, Guo らの 2008 年の論文で、**実際の偽陽性率はこの値より高い**ことが証明された。理由:

伝統的な解析は「**各ビットが独立に 0/1 を取る**」という仮定を使うが、**実際にはビット間に弱い相関**がある (同じ要素の k 個のビットは同時に立つ)。**真の偽陽性率は伝統的式の strict lower bound**であり、$k \geq 2$ では伝統式と真の値の差が観察される。

**実用上は伝統式で十分**だが、**真の最適 k は伝統式より僅かに小さい**ことが知られている。これは**「広く使われている近似式に系統的バイアスがある」**例で、理論研究の継続的価値を示す。

### 4. 変種——Bloom Filter ファミリー

#### Counting Bloom Filter
ビットを**カウンタ**(通常 4 ビット)に置き換え、削除をサポート。挿入で +1、削除で -1。代償は**メモリが 4 倍**。

#### Cuckoo Filter
2014 年提案、**ビット代わりに小さなフィンガープリント (例: 12 ビット)** を保存。**削除可能**かつ Bloom より**高速・高密度**。実装が複雑だが、現代システムでは Bloom より好まれる。

#### Quotient Filter
**メモリ局所性 (cache friendly)** を改善した変種。**ハッシュ計算回数を削減**して CPU キャッシュにやさしい。

#### Scalable Bloom Filter
**動的にサイズ拡張**できる Bloom 群。各 sub-filter を**容量超過時に追加**し、偽陽性率を約束水準で維持。

#### Stable Bloom Filter
**ストリーミングデータ**用。古いビットを確率的に消去し、**最新のメンバーシップのみ追跡**する。

### 5. 実用——どこで使われているか

#### LSM ツリー (LevelDB, RocksDB, Cassandra)
**SSTable ごとに Bloom Filter を保持**——「このキーがこのファイルに無い」と即答できる。**ディスク I/O を劇的に削減**——LSM の性能の根幹。

#### Web ブラウザ
- **Chrome の Safe Browsing** ——危険 URL データベース (数百万件) を Bloom Filter で全クライアントに配布。**偽陽性は確認後の精密検査**で除外
- **Firefox の Tracking Protection** も同様

#### CDN・分散キャッシュ
- **Akamai、Cloudflare** のキャッシュ層で「**この URL は キャッシュにあるか**」の高速判定
- 偽陽性なら origin にフォールバック——許容範囲

#### データベース
- **PostgreSQL の Bloom インデックス**——多列クエリの高速プリスクリーン
- **Apache Spark** のジョイン最適化——シャッフル削減

#### ネットワーク
- **BGP のルーティング**で「**このプレフィックスを観測したか**」の追跡
- **DDoS 検出**——既知の悪性 IP の高速判定

#### 暗号通貨
- **Bitcoin の SPV (Simplified Payment Verification)** クライアントが、**自分の関連トランザクションを Bloom Filter で要求**——ノードに具体的住所を晒さずプライバシーを保つ (ただし**プライバシー保護効果は弱い**——後続研究で否定的)

### 6. ハッシュ関数の選択——独立性の要件

理論的には**k 個の独立な一様ハッシュ関数**が必要だが、**実装上は 2 個のハッシュで k 個を生成**するテクニックが標準:

$$h_i(x) = h_a(x) + i \cdot h_b(x) \mod m$$

これは Kirsch & Mitzenmacher (2008) によって**理論的に偽陽性率に有意な影響を与えない**ことが示された。実装で**MurmurHash3、xxHash、CityHash** が好まれる——**速度と分布の質**で。**暗号学的ハッシュ (SHA-256)** は分布は完璧だが**遅すぎ**、Bloom Filter には不要。

## 気づき・洞察

### 「不可逆性」が圧縮を生む
Bloom Filter は**要素を取り出せない**(不可逆)が、その代わり**極めてコンパクト**——情報理論的には**メンバーシップ判定に必要な最小ビット数 (lower bound: 1.44 bits/要素 for 1% error)** に近い。**「何ができないか」を選ぶことで「何ができるか」を最大化**する設計思想——**意図的な能力削減 (intentional crippling)** が空間効率を生む。これは**「全機能のシステムは無機能のシステム」**というオッカム的設計原則の数理化。

### 「偽陽性を許す」という哲学的決断
Bloom Filter は**「決して間違えない」を諦める**ことで効率を獲得する。これは**統計学・機械学習の中心思想**——確率的判断は決定的判断より柔軟で実用的。**「100% 正しい」を要求する設計は実装可能性を破壊**することがある——**「99% で十分、残り 1% は別系統で処理」**という階層化が大規模システムの基本パターン。Bloom Filter はこの**「許容誤差を持つ第一階フィルタ」**の祖型。

### ハッシュの「独立性要件」の弱さ
理論は k 個の独立ハッシュを要求するが、**実用は 2 個で十分**——これは**「数学的厳密性 vs 工学的近似」**の典型的乖離。Kirsch & Mitzenmacher の貢献は、**「厳密な理論要件を緩めても性能はほぼ落ちない」**ことの証明——**「理論は工学的に過剰に厳しい仮定をしがち」**。理論と実装の橋渡しには**「弱化定理 (weakening theorems)」**の研究が決定的。

### LSM ツリーと Bloom の共生関係
LSM ツリー (LevelDB, RocksDB) は**ディスク書き込みは速いが読み出しは遅い**——複数 SSTable を全部見る必要がある。**Bloom Filter が「ここには無い」を即答**することで、**LSM の致命的弱点が補完**される。**「片方の弱点を片方が補う相補的設計」**は、CPU キャッシュ + DRAM、HBM + CXL、L1 + L2 + L3 など階層設計の基本——**異なる時間スケールの技術を組み合わせて全体を最適化**する。

### 「世界の不確実性を構造に組み込む」
Bloom Filter は**「答えは確率的」**と最初から認める。これは**現代システムの傾向**——RAID は disk failure を、TCP は packet loss を、TEE は side channel を、確率的に予期して設計に組み込む。**「決定論を諦める設計」が大規模システムの安定性を作る**——19世紀的「機械的決定論」から21世紀的「確率論的レジリエンス」へのパラダイム転換の小さな具現。

## 他分野との接続

- **cs (LSMツリー、CPUキャッシュ)**: Bloom Filter は LSM の「**ディスク到達前のフィルタ**」——CPU キャッシュが「**メモリ到達前のフィルタ**」であるのと階層的に同型
- **cs (MVCC とスナップショット分離)**: 「**最新版だけ正しく扱えば古い版は許容**」という MVCC の哲学は、「**正解は確実に正解、間違いは部分的に許容**」の Bloom と精神的に同型
- **cs (Shannon 情報理論)**: Bloom Filter のメンバーシップ判定の最小ビット数 1.44 bits/要素は、Shannon の符号化定理が示す**情報のエントロピー下限**に対応
- **tech (CXL のメモリ階層)**: HBM → DRAM → CXL.mem → SSD の階層は、**速度違いの記憶装置でフィルタリング**する設計——Bloom と同じ「**段階的ふるい**」思想
- **piano (運指の最適化)**: Bloom の最適 k 計算と、**運指選択の最適化**は同型——目的関数 (誤り率/演奏質) を最小化する離散選択
- **golf (Slope Rating の係数 5.381)**: 経験的に決定された定数 (5.381) と、**Bloom の最適 k = 0.693 × m/n** はどちらも**理論と現実の橋渡し定数**
- **anatomy (筋紡錘の一次・二次線維)**: 神経系も**「速いが粗いシグナル」**と**「遅いが精密なシグナル」**の階層——Bloom (高速・粗) と精密検索 (低速・正確) の階層と同型
- **bread (フランス粉の T 分類)**: 灰分1指標で品質を要約するのと、Bloom で**メンバーシップを 10 ビットに圧縮**するのは**情報圧縮思想**で同型
- **other (鳥のナビゲーション)**: 鳥が**地磁気・太陽位置で「だいたいの方角」を判定し詳細は地形で確認**する階層判断は、**Bloom + 精密検索**の階層と同型

## 次に深掘りしたいこと
- **Cuckoo Filter** の詳細な構造とパフォーマンス比較
- **Bloom Filter のキャッシュ局所性の改善**——Blocked Bloom Filter の実装
- **HyperLogLog** との対比——基数推定 (cardinality estimation) との違い
- **Count-Min Sketch**——頻度推定の確率的構造
- **Locality-Sensitive Hashing (LSH)**——類似度探索における Bloom 的思想
- **Bloom Filter と暗号プライバシー**——Private Set Intersection との関係
- **Lock-free な並行 Bloom Filter** の実装課題
- **NIST の Bloom Filter 解析論文** (2020) の修正アルゴリズム
- 実プロダクション (RocksDB, Cassandra) での**最適化テクニック**

## 参考ソース
- Bloom, Burton H. "Space/Time Trade-offs in Hash Coding with Allowable Errors" (CACM 1970) — 原論文
- Wikipedia "Bloom filter" — 数式と変種の総説
- Mitzenmacher & Upfal *Probability and Computing* (2nd ed., 2017) — 教科書 ch.5
- Bose, P. et al. "On the false-positive rate of Bloom filters" (Information Processing Letters 2008)
- Kirsch & Mitzenmacher "Less Hashing, Same Performance" (2008) — 2-hash 法
- Eli Bendersky "Bloom filters" (2025 blog) — 実装解説
- "A New Analysis of the False-Positive Rate of a Bloom Filter" (NIST tsapps)
- Fan, Bin et al. "Cuckoo Filter: Practically Better Than Bloom" (CoNEXT 2014)
- Pages.cs.wisc.edu "Bloom Filters - the math" (Cao 講義ノート)
- Number Analytics "The Ultimate Guide to Bloom Filter Optimization"
