# NP完全性とCook-Levin定理 — 計算困難性の境界線

**日付**: 2026-04-26
**分野**: cs（計算理論）
**タグ**: #計算量理論 #NP完全性 #Cook-Levin #SAT #還元 #PvsNP

## 学んだこと

### 1. P, NP, coNP の精密定義 — 検証者観点が本質

**P** = 決定性Turing機械で多項式時間判定可能な言語クラス。
**NP** = 非決定性Turing機械（NTM）で多項式時間判定可能。等価な「検証者」定義（Edmonds 1965 が暗黙、Cook 1971 が明示）が現代的：

> $L \in \mathrm{NP} \iff \exists$ 多項式時間検証機 $V$, 多項式 $p$ s.t.
> $x \in L \iff \exists w, |w|\le p(|x|), V(x,w)=1$

「$w$（証拠/certificate）」の存在で判定する。**「NP = Non-deterministic Polynomial」であり「Non-Polynomial」ではない**——名前の誤解は計算量理論で最も流布した誤読。

NTMの「並列推測」と検証者観の等価性は、NTMの受理計算経路を $w$ に符号化すれば自明。Cookの原論文はNTM定義を採用、Karpの論文はもはや検証者観で書かれており、**70年代前半にパラダイムが移った**。

**coNP** = NPの補集合クラス。$\overline L \in \mathrm{NP}$ となる $L$ の集合。SAT $\in$ NP、TAUT（恒真式判定）$\in$ coNP。NP=coNP は P=NP より弱い予想だが、こちらも未解決で広く偽と信じられている。多項式階層 PH の崩壊が連鎖する。

### 2. Karp還元 vs Cook還元 — 完全性の正しい粒度

**Karp還元（多項式時間多対一還元 $\le_p^m$）**: $f$ が多項式時間計算可能で $x\in A \iff f(x)\in B$。Karp 1972 の標準化。

**Cook還元（多項式時間Turing還元 $\le_p^T$）**: $A$ が $B$ を神託として多項式時間で解ける。Cook 1971 の元の定義。

**なぜKarp還元が完全性の標準か**: Cook還元は強すぎてクラス区別を潰す——例えば SAT $\le_p^T$ TAUT が成り立つ（NPとcoNPを Cook 還元で区別できない可能性）。Karp還元は方向性を保ち、**NP, coNP, PSPACE 等のクラスが還元で閉じる**。完全性概念がクラス特異的になるのは Karp の細粒度のおかげ。

両者の差は、**NPとcoNPの非対称性を保つか潰すか**で顕在化する。理論研究では Karp が標準、実用議論（特定問題が多項式時間か）では Cook で十分。

### 3. NP困難性 vs NP完全性

- **NP-hard**: NPの全問題が Karp 還元する。NPに属するとは限らない。
- **NP-complete (NPC)**: NP-hard かつ NPに属する。

停止問題（決定不能）は**NP-hardだがNP外**の典型。EXPTIME完全な問題（一般化チェスのn×n盤面）も NP-hard だがNPに入っていると信じられていない。「NPC」は**NPの中の最難クラス**を意味し、ある問題がNPCならば P=NP $\iff$ その問題が P。

### 4. Cook-Levin定理 (1971/1973) — SAT が NP-完全

**定理（Cook 1971 STOC; Levin 1973独立、ソ連でロシア語誌）**: SAT は NP-完全。

**証明構造（Tableau法）**: NTM $M$ と多項式時間境界 $p(n)$ を取り、$M$ が $x$ を受理するか否かを CNF 式 $\phi_{M,x}$ の充足可能性に帰着する。

計算履歴を $p(n)\times p(n)$ の表（tableau）として表現：
- 行 $i$ = 時刻 $i$ のテープ全体スナップショット
- セル数 = $O(p(n)^2)$ で多項式

ブール変数群（各 $O(p(n)^2)$ 個）：
- $x_{i,j,s}$: 時刻 $i$、セル $j$ の記号が $s$
- $y_{i,k}$: 時刻 $i$ の状態が $k$
- $z_{i,j}$: 時刻 $i$ にヘッドがセル $j$

CNF節群：
1. **整合性**: 各 $(i,j)$ で $x_{i,j,s}$ がちょうど一つ真（one-hot encoding）
2. **初期配置**: 行0で入力 $x$ を符号化
3. **遷移正当性**: 連続2行間の差分は $M$ の遷移関数の許す範囲——「$2\times 3$ ウィンドウ」を全位置で許容遷移にマッチさせる節（局所性が鍵）
4. **受理**: 最終行のどこかに受理状態が出現

**節数は $O(p(n)^c)$ で多項式**。$M$ が $x$ を受理 $\iff$ $\phi_{M,x}$ が充足可能。多項式時間で構築できるから Karp 還元が成立。

**非自明性**: Turing機械の遷移という「動的計算」を、命題論理という「静的構造」へ完全に圧縮できる点。**局所性（遷移は近傍3セルのみに依存）**が CNF への翻訳を可能にする。これがなければ節サイズ爆発で多項式時間に収まらない。

**歴史**: Cook はトロント大、1971年 STOC 発表。Levin はモスクワ、ソ連の検閲下で独立に 1973 年 Russian Annals of Discrete Mathematics に「Universal Sequential Search Problems」として発表（6つの問題が同時にuniversalとして列挙）。Karp 1972 が同年に **21の問題リスト**でNPCの一般性を爆発させた。3人で「Cook-Karp-Levin」の三柱。

### 5. 哲学的含意 — なぜ SAT が普遍なのか

SAT がNPCということは、**「効率的に検証可能な探索問題はすべて論理充足可能性に帰着する」**。命題論理は最小限の表現力（ANDとNOTのみ）で全NPを符号化できる。論理推論そのものが計算困難性の境界線にいる。

「探す」と「論理を満たす」が等価——**Curry-Howard対応の計算量版**とも見える（前回 Hindley-Milner の記事を参照）。

### 6. Karpの21問題 (1972) — NPC連鎖反応

Karpは SAT から 0/1整数計画、頂点被覆、クリーク、ハミルトン閉路、3彩色、部分和、分割、フィードバック頂点集合等21問題への還元を一気に提示。**「ガジェット還元」**：論理変数や節を意図する問題のサブグラフ片で表現する技法。

例: **3SAT $\to$ 頂点被覆**: 各変数に2頂点（リテラル対）、各節に3頂点（リテラル対応）の三角形ガジェット。一致リテラル間に辺。$k=n+2m$ の被覆 $\iff$ 充足割当。

例: **3SAT $\to$ ハミルトン閉路**: 「変数選択ガジェット（左右経路で T/F）」+「節ガジェット（3経路の少なくとも1つを通る制約）」。ガジェット還元は**計算量理論版の compiler design**。

### 7. 3SAT が普遍出発点の理由

任意のCNFは3SATに変換可能：長い節 $(\ell_1\lor\ell_2\lor\cdots\lor\ell_k)$ を補助変数 $y_i$ で
$$(\ell_1\lor\ell_2\lor y_1)\land(\bar y_1\lor\ell_3\lor y_2)\land\cdots$$
のチェーンに分解。サイズ線形増加で同値。

**3SAT は「最小限に豊か」**: 2SATは多項式時間（含意グラフのSCC判定）、3SATで一気にNPC。「3」が計算困難性の閾値。ほぼ全てのNPC証明は3SATから出発する——ガジェット設計が3変数節相手なら局所的・組合せ的になる。

### 8. P vs NP — 暗号を超える射程

- **公開鍵暗号**: P=NP なら一方向関数が存在しない（Impagliazzo's Algorithmica）
- **NP-中間問題**: P≠NP のとき、NP \ P かつ非NPC な問題が存在（Ladner 1975）。候補：**Graph Isomorphism**（Babai 2016 で準多項式 $\exp((\log n)^{O(1)})$）、**素因数分解**、**離散対数**
- **最適化と機械学習**: 多くの学習問題は NPC（最適決定木、最小回路、最尤割当）。実務で経験論的に解けているが理論保証は弱い
- **数学**: 任意の効率検証可能な定理探索（Cook の元論文の動機が theorem proving）

### 9. Berman-Hartmanis 同型予想 (1977)

「全 NPC 問題は多項式時間同型 ($p$-isomorphic)」予想。すなわち、NPCは唯一の構造クラスで表面上の違いはエンコーディングの差だけ、という強い主張。

帰結: もし予想真なら全NPCは**密度（長さnのyes-instance数）が同じオーダー**で、**疎集合（多項式密度）はNPCになりえない**——既知NPC全てが指数密度を持つことと整合。Mahaney 1982 が「P≠NP なら疎NPC不在」を証明（Mahaney の定理）。ランダム神託に対しては予想が**偽**（Kurtz-Mahaney-Royer 1995）——絶対的真偽は未解決。

### 10. Ladner定理 (1975) — NP中間の存在

P≠NP ならば NP \ P で非NPC な無限階層が存在。証明はdiagonalization：可算列挙された機械を順次「殺す」言語を構成。**「中間」は一般的現象**で、NPCとPの間に無限のグラデーションがある。

候補（NPCともPとも信じられていない）:
- **Graph Isomorphism**: Babai 2016 STOC で $\exp(O((\log n)^c))$（準多項式）。NPCなら多項式階層が第二レベルに崩壊（Boppana-Håstad-Zachos）——強い証拠で「NPCではない」と信じられている。
- **整数因数分解**: Shor 1994 で BQP（量子多項式）。古典でも準指数 GNFS。NPC なら NP=coNP となり崩壊が起こる。
- **離散対数**: 因数分解と類似の位置。

### 11. NPC = 実用上困難 は微妙

**最悪ケース vs 平均ケース**: NPCは worst-case 概念。平均ケース困難性（Levin 1986）は別物。Impagliazzo's Five Worlds (1995) — Algorithmica / Heuristica / Pessiland / Minicrypt / Cryptomania — のうち我々は最後 Cryptomania にいると信じる。

**ランダム3SATの相転移 (Mitchell-Selman-Levesque 1992 AAAI)**: 節/変数比 $\alpha$ が約 **4.267**（n→∞）で「ほぼ全充足可能」から「ほぼ全充足不能」に相転移。**最困難領域は相転移点近傍**——統計物理的現象。

**SATソルバー革命**: CDCL（Conflict-Driven Clause Learning, Marques-Silva-Sakallah 1996 GRASP）+ VSIDS heuristic + restarts + MiniSat (2003) アーキテクチャ。**SAT競技 KISSAT, CaDiCaL** が数百万変数の工業インスタンス（CPU検証、bug finding、planning）を秒で解く。理論最悪と実務乖離の最大の例。

**近似困難性 (PCP定理 1992 Arora-Lund-Motwani-Sudak-Szegedy)**: NP $=$ PCP$(O(\log n), O(1))$——証明を定数ビット読むだけで $O(\log n)$ ランダム性で確率検証可能。**Håstad 2001 (J.ACM)**: MAX-3SAT は 7/8 + ε に NP-困難で近似不能、これは厳密最適（7/8 を達成する単純アルゴリズムが存在）。

### 12. 実務的処方箋

NPC 問題に直面したら：
- **SAT/SMTソルバー**: Z3 (Microsoft, de Moura-Bjørner 2008)、CVC5、CDCLバックエンド
- **ILP**: CPLEX, Gurobi（branch-and-cut + cutting planes）
- **近似アルゴリズム**: PTAS / FPTAS / 定数近似（PCP境界内）
- **パラメータ複雑性 (Downey-Fellows 1999)**: パラメータ $k$ で FPT（$f(k)\cdot \mathrm{poly}(n)$）。W階層が NP内の細粒度
- **ヒューリスティクス**: 局所探索、シミュレーテッドアニーリング、遺伝的、MCMC

### 13. P vs NP がなぜ難しいか

- **相対化障壁 (Baker-Gill-Solovay 1975)**: 神託 $A$ で $\mathrm{P}^A=\mathrm{NP}^A$、別 $B$ で $\mathrm{P}^B\ne\mathrm{NP}^B$。**相対化する技法では証明不能**——対角化のような神託に閉じた論法は不十分。
- **自然証明障壁 (Razborov-Rudich 1994/1997 JCSS, Gödel賞2007)**: 構成的・大規模性質に基づく回路下界証明は、強い擬似乱数関数の存在仮定下で**P/poly に対する超多項式下界を与えない**。パリティ $\notin$ AC⁰ を含む既存技法が NP に届かない理由を説明。
- **代数化障壁 (Aaronson-Wigderson 2009)**: 算術化技法も同様に届かない。
- **Geometric Complexity Theory (Mulmuley 2000s-)**: 表現論・代数幾何で永久式 vs 行列式型問題に挑む長期プログラム。GCTI–GCTIV 等。50-100年スパン研究と本人が宣言。

### 14. 量子の角度

**BQP vs NP**: 不明だが NPC $\subseteq$ BQP は信じられていない。**Grover 1996** は SAT に $O(\sqrt{2^n})$ の二次加速のみ——量子でも指数。**Shor 1994** は因数分解を BQP に置くが、因数分解は **NP-中間と信じられている**（NP-完全ではない可能性が高い）。

**BQP は NP に含まれない可能性も**: 計算量論的には BQP と NP は包含不明。NP-完全性が量子コンピューティングで崩れない理由。

## 気づき・洞察

- **「論理 = 計算困難性の核」という哲学**: SAT がNPCであることは、Boolean論理の最小表現力で全NP探索が表現できることを意味する。論理は単なる言語ではなく**計算複雑性の物差し**。
- **障壁の三重壁**: 相対化・自然証明・代数化と「P vs NP に届かない技法」の特徴付けが進む。**「なぜ難しいか」自体が研究対象**になるメタ理論段階。
- **理論最悪と実務の乖離は機能的**: NPCは「最悪の入力で困難」と言うだけで、**現実の入力分布**は通常もっと易しい。CDCLソルバーの成功はこの乖離を産業利用する。最悪ケース理論が**敵対的設計（暗号）**に、平均ケース理論が**実務最適化**に適する役割分担。
- **完全性概念は還元粒度に依存する**: Karp還元という「正しい粗さ」を選んだから NPC が意味を持つ。理論設計の中立性ではなく**意図的な選択**。
- **NPC問題群は「同じ問題」**: Berman-Hartmanis 同型予想が真なら、SAT・TSP・3-彩色は表面上違って見えるが本質同一。実務の還元発見はこの同型を都度再発見している。

## 他分野との接続

- **Hindley-Milner型推論**（前々回 cs）: HMの最悪 DEXPTIME-complete (Mairson 1989) も NPC級困難の親戚。**型検査 ≒ 充足可能性**——型推論は論理推論。
- **公開鍵暗号 RSA/ECC**（cs）: P vs NP は公開鍵暗号の存在前提。Impagliazzo の Cryptomania 世界の住人として暗号は機能する。
- **ロックフリーCAS**（cs）: コンセンサス階層の不可能性結果と P vs NP の不可能性結果は、**「何ができないか」の構造的特定**という同じ知的モチーフ。
- **正規表現とオートマトン**（cs）: バックトラッキング正規表現の NPC性（後方参照で 3-SAT 符号化）を以前のエントリで触れた——Cook-Levin の応用例そのもの。
- **Shannon情報理論**（cs）: Kolmogorov 複雑性 vs 計算複雑性は**「情報量」と「計算量」の双対**——前者は「記述に必要なビット数」、後者は「処理に必要なステップ数」。
- **物理学・化学**: 蛋白質折りたたみ・スピングラス基底状態は NPC。**自然は P=NP を解いていない**——準安定状態に落ちる。
- **AlphaFold / 機械学習**: NPC問題に学習ヒューリスティクスで実用解を出す現代の処方箋。理論保証なしに実務勝利。

## 次に深掘りしたいこと

- **PCP定理の証明**: Dinur 2007 の組合せ的簡素化版（gap amplification by powering）
- **Toda の定理 (1991)**: PH ⊆ P^{#P}——カウンティングがPH全てを含む
- **Levinの平均ケース完全性** — distNPの形式化、TilingやBounded Halting の平均NPC
- **Geometric Complexity Theory** の現状: 永久式 vs 行列式の進展
- **Aaronson 2005 "NP-complete Problems and Physical Reality"**: 物理計算モデルでの NPC アプローチ
- **Fine-grained complexity**: SETH, 3SUM予想を出発点にした多項式時間内の困難性階層
- **Unique Games Conjecture (Khot 2002)** と最適近似不可能性の境界
- **PPAD / TFNP 階層**: ナッシュ均衡計算（Daskalakis-Goldberg-Papadimitriou 2009）の位置

## 主要文献

- **Cook, S.A. (1971)** "The Complexity of Theorem-Proving Procedures", STOC '71, pp.151-158（原典）
- **Levin, L. (1973)** "Universal Sequential Search Problems", Problems of Information Transmission 9(3) ロシア語、英訳広く流布
- **Karp, R. (1972)** "Reducibility Among Combinatorial Problems", Complexity of Computer Computations, pp.85-103（21問題）
- **Ladner, R. (1975)** "On the Structure of Polynomial Time Reducibility", J.ACM 22(1)
- **Berman & Hartmanis (1977)** "On Isomorphisms and Density of NP and Other Complete Sets", SIAM J. Comput. 6(2)
- **Mitchell, Selman, Levesque (1992)** "Hard and Easy Distributions of SAT Problems", AAAI
- **Impagliazzo, R. (1995)** "A Personal View of Average-Case Complexity", Structure in Complexity Theory '95
- **Razborov & Rudich (1997)** "Natural Proofs", JCSS 55(1)（Gödel賞2007）
- **Håstad, J. (2001)** "Some Optimal Inapproximability Results", J.ACM 48(4)
- **Babai, L. (2016)** "Graph Isomorphism in Quasipolynomial Time", STOC '16, arXiv:1512.03547
- **Sipser, M.** *Introduction to the Theory of Computation* (3rd ed.)
- **Arora & Barak** *Computational Complexity: A Modern Approach* (2009)
- **Garey & Johnson** *Computers and Intractability: A Guide to the Theory of NP-Completeness* (1979) — NPCバイブル
