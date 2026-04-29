# コンピュータサイエンス 分野サマリー

**エントリ数**: 18
**最終更新日**: 2026-04-29

## 蓄積された知識

### MESIキャッシュ整合性とメモリ整合性モデル（2026-04-30）
- **Coherence vs Consistency の階層**: coherence = 同一アドレスの複数キャッシュ整合（MESIが扱う）、consistency = 異なるアドレス間の操作順序保証（memory model が扱う）。**両者は独立しつつ依存する** 多層保証
- **MESI 4状態**: Modified (唯一所有・dirty)、Exclusive (唯一所有・clean、E→M は局所遷移可で性能向上)、Shared、Invalid。Illinois protocol (1984) 由来、x86/ARM/RISC-V 採用
- **拡張**: MOESI (AMD, Owner で書き戻しコスト削減)、MESIF (Intel, Forward 指定キャッシュが応答役)
- **Snooping vs Directory**: Snooping は O(N²)、distributed directory（Intel Mesh Interconnect、AMD Infinity Fabric）が現代主流。L3 スライスがアドレス範囲のディレクトリを保持
- **False Sharing**: 64バイト粒度の MESI が論理独立変数を物理依存に変える性能罠。`alignas(64)`、`__cacheline_aligned`、Java `@Contended`、Rust `CachePadded<T>` で対処
- **Memory Model 階層**: SC (Lamport 1979, 学術標準) → TSO (x86/SPARC, store→load の並び替えのみ許す) → WMO (ARM/RISC-V/POWER, ほぼ全並び替え許可)。Apple M1 のRosetta TSO mode は技術判断ではなく**社会的判断** (legacy x86 ソフトウェア保護)
- **C++11 memory_order**: seq_cst / acquire / release / acq_rel / consume / relaxed。release-acquire ペアリング = mutex の基盤、lock-free データ構造の核心
- **Data race UB の天才**: race を起こすプログラムを未定義動作と決めることでコンパイラ最適化を許容しつつ、正しく同期されたコードはハードウェア差異から守られる。Java は "out-of-thin-air values" 禁止でより安全側
- **Russ Cox 整理**: hardware memory model と language memory model は別レイヤー、両者の "happens-before" 関係を正しく対応付けるのが言語仕様の核心

### Reed-Solomon と Erasure Coding（2026-04-29）
- **問題設定**: n=k+m 個のブロックのうち**任意の k 個**で復元可能な MDS 性質を持つ符号。複製 3x→1.4x へストレージ効率を桁違いに改善 (k=10, m=4)
- **数学的本質**: k 個のデータシンボルを多項式 P(x) の係数とし n 点で評価。ラグランジュ補間で**任意の k 点から多項式を一意再構成**可能。この代数的性質が MDS の根拠
- **Galois Field GF(2⁸)**: バイトを既約多項式 mod の多項式環として演算。**加算 = XOR**、乗算は対数表/逆対数表で高速化、乗法逆元が常に存在。AES と同じ代数構造
- **行列表現**: Vandermonde または Cauchy 行列を生成行列 G、`G·d = c` で systematic code 生成。復号は欠落していない k 行で部分行列の逆元計算
- **ハードウェア最適化**: SSSE3 PSHUFB / AVX2 VPSHUFB で SIMD GF 乗算、PCLMULQDQ で carry-less multiplication。klauspost/reedsolomon (Go) や Intel ISA-L の実装で**数十倍の性能差**
- **LRC (Locally Repairable Codes)**: Microsoft Azure (2012)、ローカルグループ + ローカルパリティ + グローバルパリティ。1 ノード故障の修復に k 個ではなく数個で済む。**修復帯域**最適化
- **実装事例**: Backblaze RS-17-3、AWS S3 (推定 14+4 程度、11 nines)、HDFS RS-6-3/10-4、Ceph (RS/LRC/SHEC plugin)、Storj/Filecoin
- **Fountain codes vs RS**: RS = MDS で n 固定、Fountain = 確率的で長さ無制限。ストレージは RS が好まれる
- **抽象化の力**: 同じ Reed-Solomon が CD・QR コード・深宇宙通信・分散ストレージで使われる。"erasure" という抽象が物理的に異なる失敗モードを統一的に扱う

### Bloom Filter と確率的データ構造（2026-04-28）
- **基本構造**: Burton H. Bloom 1970。m ビット配列 + k 個のハッシュ関数。挿入で k ビットを 1 に、クエリは全 k ビットが 1 なら「含まれる可能性」、1つでも 0 なら「含まれない (確定)」。**偽陽性あり、偽陰性なし**——「いない」と確実に言える非対称性
- **数学**: 偽陽性率 ε ≈ (1 - e^{-kn/m})^k、最適 k = (m/n) ln 2 ≈ 0.693 m/n。**1% 誤りで 9.6 ビット/要素**——要素サイズと無関係。Bose-Guo 2008 で「伝統式は strict lower bound」と判明、真の値はやや高い
- **変種**: Counting BF (削除可、4倍メモリ)、Cuckoo Filter (Fan 2014, フィンガープリント、削除可、Bloom より高密度)、Quotient/Scalable/Stable BF。実装は MurmurHash3/xxHash + Kirsch-Mitzenmacher 2-hash テクニック (h_i = h_a + i*h_b)
- **応用**: **LSM ツリー (LevelDB/RocksDB/Cassandra)** の SSTable ごとに保持し読み I/O 削減 (LSM 性能の根幹)、Chrome Safe Browsing/Firefox Tracking、Akamai/Cloudflare キャッシュ、PostgreSQL Bloom インデックス、Bitcoin SPV (プライバシーは弱い)
- **設計哲学**: 「**不可逆性が圧縮を生む**」「**偽陽性を許す**」のは情報理論的に最小ビット数 1.44 bits/要素 (1% error) に近い。**100% 正確を諦めて効率を取る**——確率的レジリエンス設計の祖型

### MVCC とスナップショット分離（2026-04-27）
- **2PL の限界**: 読み手と書き手が相互ブロックする並行制御の構造的問題。OLTP では致命的
- **MVCC の核心**: 書き込みは新バージョンを作成、古い版は読み手のために保持。**読み手は書き手をブロックしない、書き手は読み手をブロックしない**。Bernstein-Goodman 1981 が理論基盤、InterBase 1984 が初の本格実装、PostgreSQL 1994、Oracle 7 (1992)
- **PostgreSQL 実装**: 各タプルが xmin/xmax/cmin/cmax/ctid を持つ。UPDATE は新タプル INSERT + 古タプル xmax 設定（物理的に消去しない）。トランザクション開始時に snapshot {xmin, xmax, xip[]} を取得、可視性判定で「自分の snapshot に見えるか」を毎タプルで判定
- **Snapshot Isolation (SI)**: 各トランザクションが開始時 snapshot のみ参照。Read は途中の他コミットを無視、Write は first-committer-wins。Berenson 1995 が ANSI 不備指摘し独立カテゴリ化
- **Write Skew = SI の落とし穴**: doctors-on-call 例。同じ行への競合は検出するが、異なる行への論理依存は検出しない。SI と Serializable の本質的差異
- **SSI (Serializable Snapshot Isolation)**: Cahill 2008 PhD。rw-conflict graph を実行時に追跡、Dangerous Structure 検出で abort。PostgreSQL 9.1 (2011) で実装、商用DBで本格 Serializable がスケールする初の例
- **VACUUM 問題**: 死んだタプル累積でディスク・I/O・XID wraparound リスク。autovacuum が回収。Uber が 2016年に PostgreSQL → MySQL 移行した理由の一つ
- **Oracle vs PostgreSQL**: Oracle は UNDO segment（読み手保護、ORA-01555 リスク）、PostgreSQL は inline 死蔵 + VACUUM（書き手保護）。**実装トレードオフが対照的**
- **Spanner TrueTime**: 分散 SI を GPS+原子時計で実現（誤差7ms以下）。external consistency 達成。**ハードウェアで時間の不確実性を有界化**

### NP完全性とCook-Levin定理（2026-04-26）
- **P, NP, coNP の精密定義**: NP は「Non-deterministic Polynomial」であり「Non-Polynomial」ではない。NTM定義 ≡ 検証者定義 ($\exists w\le p(n), V(x,w)=1$)。Edmonds 1965 暗黙、Cook 1971 明示
- **Karp還元 vs Cook還元**: Karp ($\le_p^m$ 多対一) が完全性の標準。Cook ($\le_p^T$ Turing) は強すぎてNPとcoNPを区別できない可能性。**Karp の細粒度がNP, coNP, PSPACE を還元で閉じさせる**
- **NP-hard ≠ NP-complete**: NP-hard は NP外でもよい（停止問題、EXPTIME完全な一般化チェス）。NPC = NP-hard ∧ NP内 = NPの中の最難クラス
- **Cook-Levin定理 (1971/1973)**: SAT は NPC。**Tableau法**で証明——NTM の $p(n)\times p(n)$ 計算履歴を CNF に翻訳。変数 $x_{i,j,s}, y_{i,k}, z_{i,j}$、節は (1)整合性 one-hot、(2)初期配置、(3)$2\times 3$ ウィンドウ遷移正当性、(4)受理。**遷移の局所性**が多項式翻訳を可能にする鍵
- **歴史**: Cook 1971 STOC（トロント大）、Levin 1973独立（モスクワ、ロシア語誌）。Karp 1972 が21問題リストでNPC連鎖反応を起こす
- **哲学的含意**: SAT が NPC = 「効率的に検証可能な探索問題はすべて論理充足可能性に帰着」。**論理推論そのものが計算困難性の境界線**。最小表現力（AND/NOT）で全NPを符号化できる驚き
- **3SAT が普遍出発点**: 2SAT は P（含意グラフSCC）、3SAT で一気にNPC——「3」が困難性閾値。長い節を補助変数 $y_i$ でチェーン分解（線形サイズ）。ガジェット還元は局所組合せ的になり設計しやすい
- **Karpの21問題の還元playbook**: ガジェット = 論理変数や節を意図する問題のサブグラフで表現。3SAT→頂点被覆（変数2頂点+節三角形）、3SAT→ハミルトン閉路（左右経路ガジェット）
- **Berman-Hartmanis 同型予想 (1977)**: 全NPCは多項式時間同型 ($p$-isomorphic)。表面差はエンコーディングだけ。帰結: 疎集合（多項式密度）はNPCになりえない（Mahaney 1982）。ランダム神託で偽（Kurtz-Mahaney-Royer 1995）、絶対真偽未解決
- **Ladner定理 (1975)**: P≠NP なら NP \ P で非NPC な無限階層が存在（NP-中間）。対角化で証明。候補: **Graph Isomorphism**（Babai 2016 で準多項式 $\exp(O((\log n)^c))$、NPC なら多項式階層が第二レベルに崩壊するため非NPC が信じられる）、**素因数分解**（Shor で BQP）、**離散対数**
- **NPC = 実用困難 は微妙**: (1) 最悪 vs 平均ケース乖離、(2) **ランダム3SAT相転移 (Mitchell-Selman-Levesque 1992)** 節/変数比 ≈ 4.267 で最困難領域、(3) **CDCLソルバー革命** (GRASP 1996, MiniSat 2003, Z3, KISSAT) で工業数百万変数を秒で解く、(4) **PCP定理 1992** + **Håstad 2001** で MAX-3SAT は 7/8+ε にNP-困難で近似不能、これは厳密最適
- **Impagliazzo's Five Worlds (1995)**: Algorithmica / Heuristica / Pessiland / Minicrypt / Cryptomania の5世界モデル。我々は Cryptomania にいると信じる（公開鍵暗号成立）
- **実務処方箋**: SAT/SMT (Z3, CVC5)、ILP (CPLEX, Gurobi)、近似 (PCP境界内、PTAS/FPTAS)、**パラメータ複雑性 (Downey-Fellows 1999)** でFPT、ヒューリスティクス
- **障壁の三重壁**: (1) **相対化 (Baker-Gill-Solovay 1975)**——神託で両方向、(2) **自然証明 (Razborov-Rudich 1994/1997, Gödel賞2007)**——擬似乱数関数が存在すれば自然証明はP/poly超多項式下界を出せない、(3) **代数化 (Aaronson-Wigderson 2009)**。**「なぜ難しいか」自体が研究対象**のメタ理論段階
- **Geometric Complexity Theory (Mulmuley)**: 表現論・代数幾何で永久式 vs 行列式に挑む50-100年プログラム
- **量子角度**: NPC ⊄ BQP と信じる。**Grover (1996)** SAT に二次加速のみ ($O(\sqrt{2^n})$)、量子でも指数。**Shor (1994)** は因数分解をBQPに置くが因数分解はNP-中間と信じられる（NPCなら NP=coNP 崩壊）
- **核心洞察**: (1) **論理 = 計算困難性の物差し**（Boolean最小表現力でNP全てを表す）、(2) **完全性は還元粒度に依存**（Karp の細かさを意図的選択）、(3) **NPC問題群は同型予想下で「同じ問題」**、(4) 最悪ケース理論は敵対的設計（暗号）に、平均ケース理論は実務最適化に役割分担、(5) 障壁の特定が現代複雑性理論の主戦場

### Shannon 情報理論とエントロピー符号化（2026-04-25）
- **Shannon 1948 "A Mathematical Theory of Communication"**: 情報量 $I(x) = -\log_2 p(x)$、エントロピー $H(X) = -\sum p \log p$、相互情報量、通信路容量。20世紀最重要数学論文のひとつ
- **情報源符号化定理**: i.i.d. 情報源で平均符号長の下限は $H(X)$、任意に近づけるが越えられない。"典型的集合" の論法で証明
- **Huffman 1952**: 可変長 prefix code、高頻度記号に短い符号、同じ分布での平均符号長最小を保証。ただし確率が $2^{-k}$ 以外では最適に達しない
- **算術符号化 (1976 Rissanen/Pasco)**: メッセージ全体を [0,1) の実数として符号化、区間の逐次分割、任意にエントロピーに近づける。H.264/HEIC/JPEG 2000 の中核
- **極端非一様例**: $p=\{0.99, 0.01\}$、$H=0.08$ bit、Huffman 1.0 bit（12倍）、Arithmetic 0.08（一致）
- **Asymmetric Numeral Systems (ANS, 2014 Duda)**: 算術符号化の情報効率 + テーブルルックアップの速度。zstd/Brotli/LZFSE で採用、21世紀のブレークスルー
- **"圧縮 = 予測"**: 次記号を高確率で予測できれば情報量低く短符号化。LLM (Chinchilla 70B) + 算術符号化が Gzip を超える圧縮率 (Delétang 2023)
- **波及**: 機械学習 (交差エントロピー、KL)、統計力学 (Jaynes 1957)、Information Bottleneck、暗号 (完全秘匿性 Shannon 1949)、Landauer 原理 (1 bit 消去に kT ln2)
- **最大エントロピー原理** (Jaynes): 制約下で最もエントロピー高い分布を選ぶ——無情報から正規分布等が導かれる統計推論の原則

### Hindley-Milner型推論とlet多相（2026-04-24）
- **HM型システムの位置づけ**: ラムダ計算＋パラメトリック多相、Hindley 1958（組合せ論理）・Milner 1978（ML）・Damas 1984（形式化）、ML/OCaml/Haskell/F#/Elmの理論基盤
- **4つの性質**: (1)推論可能——型注釈不要で principal type を自動発見、(2)健全——型付きプログラムは実行時型エラーなし、(3)完全——型付け可能なら推論成功、(4)最一般性保証
- **型 vs 型スキーム**: `Int -> Bool`（型）vs `∀a. a -> a`（型スキーム、量化された型変数を持つ）、let束縛変数のみ型スキーム可（let多相）
- **Algorithm W**: 新型変数導入→AST走査で型方程式収集→単一化で解く→let束縛時に一般化→使用時にインスタンス化、Robinsonの統一化（1965）が核
- **単一化（unification）**: 2型を等しくする最一般代入、occurs checkで循環型拒否、`unify(a, a->b)`は失敗
- **一般化の微妙さ**: 環境に束縛されていない型変数のみ∀で量化、環境中の自由変数は他との制約関係を持つため量化できない
- **let多相の決定可能性**: ラムダ引数を単相型に制限することで推論を決定可能に、System F（Girard-Reynolds 1972）は強力だが推論決定不能
- **理論と実務のギャップ**: 最悪DEXPTIME（Mairson 1989）、実際のプログラムでは線形に近い、百万行を合理的時間で処理
- **W vs M**: Algorithm W（ボトムアップ）とAlgorithm M（トップダウン）、現代処理系は両者のハイブリッド＋局所型推論、Scala/Kotlin/TypeScriptは部分型があるためHM拡張
- **HMの拡張**: value restriction（ML、副作用両立）、型クラス（Haskell、制約付き多相）、GADT、higher-rank polymorphism、row polymorphism、Liquid types
- **Curry-Howard対応**: 型=命題・プログラム=証明、HMは「プログラムから命題を自動抽出」、System F/Coqは逆方向（命題を書いて証明項を作る）
- **HMの限界**: 型エラーが"離れた場所"で表面化（推論が最一般型を選ぶ→意図と乖離）、Haskell初学者の苦闘の一因

### ロックフリーデータ構造とCAS・ABA問題（2026-04-23）
- **mutexの構造的限界**: クリティカルセクション中のスレッド停止(プリエンプト/ページフォルト/GC)が他スレッド全てを無限阻害。優先度逆転・デッドロック・コンボイ効果の根
- **進捗条件の階層(Herlihy 1991, JPDC)**: Wait-free(全スレッド有界ステップ) > Lock-free(system-wide progress) > Obstruction-free(isolated実行で進む) > Blocking。**表現力ではなく耐故障性の階層**
- **CAS(Compare-And-Swap)**: atomic RMW命令。x86 `LOCK CMPXCHG`(MESI Modified遷移)、ARM/RISC-V LL/SC(`LDXR/STXR`, `LR/SC`)。uncontended 10-40サイクル、cross-socket ~100ns
- **Treiber stack(1986, IBM)**: `push`はCASで安全。`pop`には**ABA問題**が潜む
- **ABA問題**: T1が`top=A`観測→プリエンプト→T2がpop(A)/push(C)/pop(D)/push(新A同アドレス)→T1のCAS(&top, A, A.next)が成功して破綻。**「ポインタ同一性 ≠ 状態同一性」**。GC言語は自動回避
- **ABA解決策**: (1) **タグ付きポインタ**(CMPXCHG16B、64bit tagで事実上安全)、(2) **Hazard Pointers**(Michael 2004、スレッドごとに参照中ポインタをpublish、portableだが20-50%オーバヘッド)、(3) **Epoch-Based Reclamation**(Fraser 2004、クリティカルセクション停止でunbounded memory、crossbeam-epoch基盤)、(4) **RCU**(Linux kernel、read性能ネイティブポインタloadレベル、write/reclaim重い、read-heavy支配)
- **Michael-Scott queue(1996, PODC)**: lock-free FIFO、`java.util.concurrent.ConcurrentLinkedQueue`の基盤。**cooperative helping**(他スレッドが詰まったtail更新を自分が代行)が lock-free progress の本質
- **メモリモデル**: x86-TSO(強、store→load以外は順序保持)vs ARM/POWER(弱、全並び替え可)。C++11 `memory_order_relaxed / acquire / release / acq_rel / seq_cst`。典型ペア `store(release) + load(acquire)` → happens-before確立
- **線形化可能性(Herlihy & Wing 1990, TOPLAS)**: 各操作が「invocation-response間の単一時点で瞬間効果」+ **real-time order整合**。Sequential consistencyより強い。**compositional**(部品を組合せても成立)
- **Consensus Hierarchy(Herlihy 1991)**: 通常register=consensus number 1、FIFO queue/stack=2、**CAS/LL-SC=∞**。CAS の universality = 現代CPUがCASを持つ理論的正当化
- **FLP impossibility(1985)**: 非同期分散+1故障+決定性の合意は不可能。共有メモリ版(Herlihy)とは設定違うが「非同期性と耐故障性の緊張」の同主題
- **性能**: uncontended CAS 10-40ns(mutex 25-50nsと大差なし)、contended CASは O(N²) retry爆発→exponential backoff必須、cache line ping-pong(MESI thrashing)、false sharing防止に `alignas(64)`
- **実世界**: JVM(`j.u.c.atomic`, `ConcurrentLinkedQueue`)、Linux kernel(RCU massive, 数万コールサイト)、Rust(`std::sync::atomic` + crossbeam)、**RocksDB MemTable lock-free skip list**(LSM前回記事とつながる)、Memcached/Redis
- **使わない判断**: 低競合(mutex同等+単純)、複雑不変条件(TM/mutex)、非クリティカルパス。「Lock-free ≠ 自動的に速い」
- **核心洞察**: (1) 進捗条件は耐故障性の階層、(2) **メモリ回収こそが本質問題**(GCはロックフリーの隠れた土台)、(3) CASユニバーサリティが命令セット設計を正当化、(4) **ヘルプパターン**(他スレッドの詰まりを自分が解消しながら進む collectivism)

### LSMツリーとログ構造化ストレージ（2026-04-21）
- **B木の限界とLSMの動機**: B木はランダムなインプレース更新が必須で、HDDシーク（~10ms、シーケンシャルの約1000倍）と SSD write amplification（NAND P/Eサイクル寿命消耗）の両方でボトルネック化。書き込み支配ワークロード（時系列DB, KVS, ログ集約）では致命的
- **LSMの核心（O'Neil et al. 1996, Acta Informatica）**: インプレース更新を放棄し追記のみに。全ディスク書き込みをシーケンシャル化
- **構造**: MemTable（メモリ内ソート済、skip list/赤黒木）→ WAL（耐障害性）→ Immutable SSTable（キー順ソート、スパースindex付き）→ 指数的サイズのLevel階層（典型 T=10）→ Compactionで下層へ
- **SSTable (Sorted String Table)**: 不変のキー順ソートファイル。ブロック分割、末尾にインデックス・Bloom Filter・メタデータ。不変性が並行性・耐障害性・スナップショット全てを単純化
- **Compaction 3戦略のトレードオフ**:
  - **Size-Tiered (Cassandra)**: 同サイズSSTableを複数集めてマージ。write amp低 O(log N)、read amp高、space amp悪（最悪2倍）
  - **Leveled (LevelDB/RocksDB)**: L1以下でキー範囲非重複の不変条件。read amp最小、space amp小（~1.1倍）、write amp大（~5L where L=レベル数）
  - **Hybrid (RocksDB実装)**: L0 Tiered + L1以下Leveled。小レベルでは書き込み優先、大レベルでは空間効率優先
- **RUM Conjecture (Athanassoulis 2016)**: Read/Update/Memory amplification の3つを同時最適化不能。CAP定理と並ぶ「不可能性の三角形」。B木（読み最適）、LSM（書き最適）、Hash（点最適）を統一的に説明
- **定量**: RocksDB Leveled で WA≈20-30/RA≈1-2/SA≈1.1、Tieredで WA≈5-10/RA≈10+/SA≈1.5-2
- **Bloom Filter**: m bit配列+k個ハッシュ、最適 k=(m/n)ln2 で FPR=(1-e^(-kn/m))^k。RocksDB デフォルト10 bits/key で1% FPR。存在しないキーのディスク読みを実質ゼロ化、数百倍高速化
- **Ribbon Filter (Dillinger 2021)**: Bloomの後継、同FPRで30%メモリ削減（7 bits/key for 1%）。構築コスト高いため長生きする大レベルのみ適用
- **SSD時代でもLSMが優位な理由**: (1) NAND P/Eサイクル寿命を物理書込削減が直接延ばす、(2) FTL内GCと協調、(3) シーケンシャル書き込みはQD=1でも数倍高速
- **実システム**: LevelDB (Google, Dean/Ghemawat 2011), RocksDB (Meta 2012, MyRocks/TiKV/CockroachDB/Flink/Kafka Streams基盤), Cassandra/ScyllaDB（分散）, HBase (BigTable実装), ClickHouse MergeTree（OLAP特化）
- **WAL パターンの共通性**: LSM の WAL = Raft のログレプリケーション = B木の redo log ＝「操作を先にログし後で状態反映」

### CPUパイプラインと分岐予測（2026-04-20）
- **パイプライン深度の最適化点**: 5段RISC → Pentium 4 Prescott 31段（失敗）→ 現代 Golden Cove/Zen 5 の 14-19段 + スーパースケーラ幅 6-8 uop/cycle。深度×幅×予測精度の3変数最適化
- **ハザード三分類**: 構造（資源競合・Harvard型分離で解決）、データ（RAW/WAR/WAW・フォワーディングで1cycle化）、制御（分岐予測の存在理由）
- **分岐予測進化**: 2-bit saturating (Smith 1981, 80-90%) → 2-level adaptive/gshare (Yeh & Patt 1991, 95%+) → **TAGE** (Seznec 2006, 幾何級数履歴長+部分タグマッチ, CBP優勝) → **Perceptron** (Jiménez & Lin 2001, 履歴長に線形資源)
- **現代プロセッサ**: Intel Golden Cove = 3レベルBTB・128+エントリ・2 taken branch/cycle。AMD Zen 5 = **2-ahead TAGE** (Seznec 1996の30年越しの工業化)。ARM Neoverse V2 = 12K BTB + 8-table TAGE
- **Tomasulo (1967)**: Reservation Station + CDB + Register Renaming (論理16本→物理224本) + ROB (Zen 5で448、Golden Coveで512)。"in-order issue, out-of-order execute, in-order commit"で精密例外と投機実行を両立
- **Spectre/Meltdown (2018-01)**: μarch状態≠arch状態の抽象化漏れが30年越しに露呈。Meltdown=ユーザ空間からカーネル投機読出 (Intel/Apple)、Spectre=予測器訓練による越境投機 (全OoO CPU)
- **緩和策コスト**: KPTI 5-30%、Retpoline 4-8% (OLTP)、IBPB/STIBP (コンテキスト切替・SMT兄弟スレッド間の予測器分離)
- **分岐ミスペナルティ**: 現代CPUで15-20cycle、IPC=4なら60-80命令分損失。予測精度95%でも1000命令中750cycleロス — 予測器にトランジスタ数万を割く経済的根拠
- **コード側対策**: cmov等のbranch-free化、PGOによるBBレイアウト、__builtin_expect/[[likely]] (予測器訓練ではなくコード配置に効く)
- **投機幅**: Golden Cove ~512命令窓、BOOM 128程度。ROB/PRFサイズが投機深度上限

### 公開鍵暗号 — RSA と ECC（2026-04-17）
- **公開鍵暗号史**: Diffie-Hellman 1976（鍵交換概念）、RSA 1977（IFP）、Koblitz/Miller 1985（ECC、ECDLP）の系譜
- **RSA 数学**: N=pq（典型2048-4096b）, e=65537が標準, d=e⁻¹ mod φ(N)。CRT 復号で4倍高速化。安全性は GNFS（準指数 L_N[1/3]）の困難性
- **楕円曲線の代数**: y²=x³+ax+b 上の点の加法は無限遠点 O を含む群を成す。点の k倍算は Double-and-add で O(log k)
- **ECDLP**: 「P=kG から k を求める」最良汎用は Pollard's rho、O(√n)。指数より大幅高速な手法は未知
- **鍵長効率**: 128bit安全性で RSA 3072 vs ECC 256（12倍）、256bit で RSA 15360 vs ECC 512（30倍）
- **主要曲線**: NIST P-256（WebAuthn 標準だが NSA 関与疑惑あり）、secp256k1（Bitcoin、y²=x³+7）、Curve25519（Bernstein, 安全性・性能・実装シンプルさで最良、Signal/TLS1.3/SSH/WireGuard 採用）、Ed25519（EdDSA、決定論的署名）
- **サイドチャネル攻撃**: タイミング・電力消費・電磁波からの鍵漏洩。RSA は CRT 操作時間差（Bleichenbacher）、ECC は条件分岐 unsafe double-and-add。Curve25519 は constant-time 容易な設計
- **ECDSA k 値再使用の致命性**: PlayStation 3（2010）が k 固定で完全クラック。Ed25519 は決定論的で構造的に排除
- **量子脅威と PQC**: Shor アルゴリズムで RSA・ECC は多項式時間で破られる。NIST 2024年標準化＝ML-KEM（旧 Kyber, 鍵交換）、ML-DSA（旧 Dilithium, 署名）、SLH-DSA（旧 SPHINCS+）。「Harvest Now, Decrypt Later」攻撃に長期機密データは PQC 対応必要
- **ハイブリッド PQC**: TLS の X25519+ML-KEM 鍵交換が Cloudflare/Google で2024-2025展開。20年に一度の暗号インフラ大転換が進行中

### 正規表現とオートマトン（2026-03-24）
- Kleeneの定理 (1956): 正規表現・NFA・DFAの三者が等価であることの証明。RE→NFA（Thompson's construction）、NFA→DFA（べき集合構成）、DFA→RE（状態除去法）の3変換で成立
- Thompson's Construction (1968): RE を O(m) 状態の NFA に変換。各部分NFAが「単一開始・単一受理」の不変条件を維持し、ε遷移で合成
- べき集合構成: n状態NFA → 最悪 2^n 状態DFA。指数爆発は不可避（「末尾からn番目が1」の言語）。遅延構成で実用化
- ポンピング補題: ピジョンホール原理によりDFA中のループを検出。正規でないことの証明に使う必要条件（十分条件はMyhill-Nerode定理）
- Chomsky階層: Type 3（FA）⊂ Type 2（PDA）⊂ Type 1（LBA）⊂ Type 0（TM）。表現力↑ ↔ 計算効率↓・決定可能性↓
- 正規表現エンジンの二大パラダイム: Thompson NFAシミュレーション O(mn) vs バックトラッキング O(2^n)。後方参照の利便性がバックトラッキング普及の歴史的要因
- RE2 (Russ Cox / Google): Thompson NFAに基づく線形時間保証。後方参照を意図的に不サポート。lazy DFA construction でメモリ制御。Go, Code Search, Bigtable で採用
- 後方参照のNP完全性 (Aho 1990): 後方参照で3-SATをエンコード可能。PCREの「正規表現」は名前に反してType 3を超えた表現力
- 字句解析パイプライン: RE → Thompson NFA → べき集合構成 → Hopcroft最小化 → 遷移テーブル。lex/flex がこの全段階を自動化
- 最長一致規則: DFAシミュレーションで「最後に受理状態を通過した位置」を記録することで実現

### 仮想メモリとページング（2026-03-23）
- 歴史的動機: Atlas Computer (1962, Kilburn) の「one-level store」がオーバーレイの手動管理を排除。メモリ管理の責任をプログラマからシステムに移す抽象化
- アドレス変換: VPN→PFN のマッピングをページテーブルで管理。PTEにPresent/R-W/Accessed/Dirty等のメタデータ
- TLB: アドレス変換の専用キャッシュ。エントリ数少（64-2048）のためフルアソシアティブ。ミスペナルティ大（ページテーブルウォーク）。Meta報告で実行サイクルの約20%がTLBミス処理
- x86-64の4レベルページテーブル: CR3→PML4→PDPT→PD→PT。各レベル9ビット×512エントリ。疎なアドレス空間で未使用領域のテーブルを割り当てない — メモリ使用量がO(使用ページ数)に
- 5レベルページテーブル（LA57, Ice Lake以降）: 48ビット→57ビット仮想アドレス。256TiB→128PiB。Linux 4.14でサポート
- 逆ページテーブル: 物理フレーム数に比例するサイズ（PowerPC, IA-64）。ハッシュによる検索で空間局所性破壊、共有メモリ複雑化が欠点
- ページ置換: OPT（Bélády, 理論的下限）、LRU（高コスト）、Clock/Second-Chance（参照ビットによるLRU近似、針の巡回が適応的時間窓）、Working Setモデル（Denning 1968）
- スラッシング: ワーキングセット合計 > 物理メモリで正のフィードバックループ発生。TCP輻輳崩壊と同構造。多重度制御で防止
- デマンドページング: アクセス時に初めてロード（lazy evaluation）。プリページングは先読みで初期フォルト軽減
- Copy-on-Write: fork()でページを共有し書き込み時にコピー。読み取り専用PTEでトラップを発生させるハードウェア機構の「目的外使用」
- メモリマップドファイル: mmap()でファイルを仮想アドレス空間にマッピング。共有ライブラリ・実行バイナリのロードに使用。ページキャッシュとの統合
- Huge Pages: 2MB/1GBページでTLBカバレッジ512倍以上。THP（透過的）とhugetlbfs（明示的）。内部フラグメンテーション・連続物理メモリ確保がトレードオフ
- ASLR: 仮想メモリの柔軟性をセキュリティに活用。コード/データ/ヒープ/スタックの配置ランダム化。PaX (2001) → OpenBSD 3.4 → Linux/Windows
- TLBシュートダウン: マルチコアでページテーブル変更時にIPI送信で全コアのTLBを無効化。1-5μs/コア。ASID/PCIDでコンテキストスイッチ時のフラッシュ回避

### Raftコンセンサスアルゴリズム（2026-03-22）
- Raft誕生の動機: Paxosの難解さが誤実装を量産。Ongaro & Ousterhout (2014) が「理解可能性」を明示的設計目標として再設計
- 設計手法: 問題の分解（リーダー選挙・ログレプリケーション・安全性）と状態空間の縮減（強いリーダーによるデータフロー一方向化）
- リーダー選挙: term（論理時計）で時間を構造化。Election Restrictionにより最新ログ保持者のみがリーダーに — Paxosと違いログ修復フェーズ不要
- ログレプリケーション: 過半数への複製でコミット。Log Matching Propertyでログの一貫性保証。不整合時はリーダーのログで上書き
- Leader Completeness Property: コミット済みエントリは以降の全リーダーのログに含まれる。Figure 8問題（前termエントリのコミット判定の微妙さ）
- メンバーシップ変更: Joint consensus（2フェーズ）またはsingle-server changes（1台ずつ）。後者はetcd等で採用
- ログコンパクション: 独立スナップショット取得。遅延フォロワーへのInstallSnapshot RPC
- Paxosとの差: ログにホールなし、リーダー必須、理解可能性重視。steady-state性能は同等
- 線形化可能性を提供。CAPのCP系。LeaseRead/ReadIndexでstale read防止
- 実装: etcd (Go), raft-rs/TiKV (Rust), CockroachDB (Multi-Raft), Consul

### TCP輻輳制御アルゴリズム（2026-03-21）
- 1986年の輻輳崩壊: NSFNETで32Kbps→40bps。正のフィードバックループ（ロス→再送→さらなる輻輳）による「共有地の悲劇」。Van Jacobsonが1988年にエンドホストのみの分散制御で解決
- AIMD（加法的増加・乗法的減少）: Chiu & Jain (1989) が公平かつ効率的な均衡への収束の必要十分条件であることを幾何学的に証明。「見えざる手」のネットワーク版
- アルゴリズム系譜: Tahoe（cwnd=1リセット）→ Reno（Fast Recovery、パイプライン維持）→ NewReno（partial ACK処理改善）→ CUBIC（三次関数、RTT独立性、凹凸プロファイル）→ BBR（モデルベース）
- CUBICの設計: W(t) = C(t-K)^3 + W_max。ウィンドウ成長をRTTではなく実時間の関数にすることでRTT不公平を構造的に解消。W_max付近での凹増加（慎重）とW_max超過後の凸増加（積極探索）
- パラダイム変遷: Loss-based（事後的・バイナリ）→ Delay-based/Vegas（予兆的だが攻撃的フローに負ける囚人のジレンマ）→ Model-based/BBR（BtlBw×RTpropの最適動作点を明示的に推定）
- BBRの問題: RTT不公平、CUBICとのinter-protocol公平性がbuffer深度依存。BBRv2/v3でも未解決
- データセンターCC: DCTCP（ECNマーキング率から輻輳程度を多ビット推定）、DCQCN（RoCEv2向けPFC+ECN）。閉じた環境で全ノード統制可能な前提
- QUICによるCC のユーザースペース化: カーネルのアップデートサイクル（年）→アプリのデプロイサイクル（日）でのCCアルゴリズム進化

### CPUキャッシュとメモリ階層（2026-03-20）
- メモリウォール問題: CPU性能向上率（年60%）vs DRAM（年7%）の乖離が数百倍に。Wulf & McKee (1995) が定式化
- キャッシュ階層の設計はサイズ vs レイテンシのトレードオフ。L1の32KBは物理的配線長（光速の壁）が規定。L1のデータ/命令分離はパイプラインの構造的ハザード回避
- キャッシュラインが64バイトなのは、DRAMバースト転送サイズ・空間局所性・タグオーバーヘッド・false sharing影響の4変数最適化点
- 結合度は8-way以上でフルアソシアティブに近いミス率。置換ポリシーはPseudo-LRUやRandomがLRUに迫る — 結合度が高ければポリシーの差は消える
- Write-Back + Write-Allocateが主流。メモリバス帯域幅が最も制約の厳しいリソース
- MESIプロトコルのE状態は「自分だけが持つ」ことの知識でwrite時のバストランザクションを省略。スヌーピング（~16コア）→ ディレクトリベース（64+コア）のスケーラビリティ遷移
- False sharing: 論理的に独立なデータが同一キャッシュラインに載ることで発生。alignas(64)やper-CPUデータ構造で回避
- Cache-oblivious algorithms (Frigo et al. 1999): キャッシュパラメータを知らずに全階層で漸近的最適。再帰的分割統治がパターン
- B木のノードサイズ最適化とキャッシュライン設計は「転送単位あたりの有用データ密度最大化」という同一原理のスケール違い

### B木とデータベースインデックス（2026-03-19）
- B木の存在意義はディスクI/Oコストモデルに根差す: ファンアウト最大化により木の高さを劇的に低減（BST: 20レベル → B木: 3レベル for 100万要素）
- B+木は内部ノードからデータを排除しファンアウトをさらに向上。葉ノード間の双方向リンクリストで範囲クエリを最適化
- B木 vs LSM木はRUM予想（Read/Update/Memory amplification）のトレードオフ: 読み取り最適化 vs 書き込み最適化。両立は不可能
- クラスタードインデックスはデータの物理配置を決定（テーブルあたり1つ）、セカンダリインデックスはブックマークルックアップが必要
- カバリングインデックスとINCLUDE句でIndex-Only Scanを実現。複合インデックスはプレフィックスルールに従う
- 現代の変種: Bw-tree（ロックフリー）、フラクタル木（バッファ付きノード）、ART（メインメモリ向け基数木）
- 実装比較: InnoDB（クラスタードB+木必須）、PostgreSQL（ヒープ+インデックス分離、MVCC対応）、SQLite（テーブルB+木+インデックスB木）

## カバー済み領域

| 領域 | エントリ数 |
|------|-----------|
| アルゴリズム・データ構造 | 1 |
| オペレーティングシステム | 1 |
| コンピュータネットワーク | 1 |
| データベース | 2 |
| コンパイラ・言語処理系 | 0 |
| 分散システム | 2 |
| 計算理論 | 2 |
| コンピュータアーキテクチャ | 2 |
| セキュリティ | 1 |
| ストレージシステム | 1 |
| 並行性・同期 | 1 |

## キーコンセプト

- **外部記憶モデル**: 計算量をディスクI/O回数で測る。ハードウェアの物理特性がデータ構造設計を決定する
- **ファンアウト最大化**: B木系の設計思想の核。ノードサイズをディスクページに合わせ、分岐因子を最大化して木の高さを最小化
- **RUM予想**: 読み取り増幅・書き込み増幅・空間増幅の3つを同時に最適化することはできない
- **クラスタードインデックス**: データの物理配置とインデックス順序を一致させ、範囲クエリのシーケンシャルI/Oを実現
- **転送単位への最適化**: キャッシュライン(64B)、ディスクページ(4KB)、ネットワークMTU(1500B) — あらゆるレイヤーでハードウェアの転送粒度にデータを最適化する通底パターン
- **局所性の二原則**: 時間的局所性（最近のデータは再利用される）と空間的局所性（近傍データもアクセスされる）がメモリ階層設計の根拠
- **単純さの優位**: ハードウェア設計では複雑さのコスト（面積・電力・タイミング）が性能効果を上回ることが多い
- **エンドツーエンド分散資源配分**: TCP輻輳制御はネットワーク内部に知性を置かず、エンドホストの局所観測（RTT、ロス）のみで公平な資源配分に収束させる。AIMDがその必要十分条件
- **暗黙的 vs 明示的シグナル**: ロス（暗黙的・普遍的）→ 遅延（暗黙的・予兆的）→ ECN（明示的・精密）。情報の豊かさとデプロイメント容易性のトレードオフ
- **制御のフィードバック遅延**: RTTが輻輳制御の安定性を根本的に制約。高BDPネットワークでの制御困難性はフィードバック遅延の問題
- **理解可能性は設計目標になる**: 正しいが理解できないアルゴリズムは正しく実装できない。Raftは問題の分解と状態空間縮減で理解可能性と効率性を両立
- **制約が自由をもたらす**: Raftの「最新ログ保持者のみリーダー」制約はPaxosより厳しいが、ログ修復不要にし実装を単純化。自由度の削減が正当性推論を容易にする
- **操作ログ先行書き込みパターン**: WAL（B木）とRaftのログレプリケーションは「操作を先にログし、後で状態に反映する」同一パターン。耐障害性の根幹
- **リソース仮想化の三位一体**: CPU（タイムシェアリング→プロセス）、メモリ（仮想メモリ→アドレス空間）、ディスク（ファイルシステム→ファイル）。物理リソースの制約を抽象化で隠蔽する共通パターン
- **遅延評価パターン**: デマンドページング、CoW、mmapの遅延マッピング — 「必要になるまでコストを遅延」がOS設計に普遍的に現れる
- **正のフィードバックループによる崩壊**: スラッシング（メモリ）と輻輳崩壊（ネットワーク）は同一構造。共有リソースの過剰使用→性能劣化→さらなる過剰使用。防止にはフィードバック制御（ワーキングセット/AIMD）
- **ハードウェア機構の創造的転用**: PTEの権限ビットをCoWやdirty tracking に活用。設計時に想定されなかった用途が抽象化層から創発される
- **宣言と実行の等価性**: 正規表現（宣言的）とオートマトン（実行的）の等価性がKleeneの定理で数学的に保証。SQL/クエリ計画、HTML/レンダリングと同じパターンだが、等価性の証明がある点が特異
- **非決定性の圧縮力**: NFA→DFA変換の指数爆発は、非決定性が本質的に計算記述をコンパクトにする能力を持つことの証拠。P≠NP予想と同構造
- **表現力と決定可能性のトレードオフ**: Chomsky階層の各レベルで表現力を得るたびに決定可能な性質を失う。正規言語は等価性判定可能、文脈自由言語では不能
- **数学的精緻さと実装の責任のトレードオフ**: RSA（直感的・教育的）から ECC（複雑・効率的）への移行。鍵長 1/10 と性能優位が決定的で、現代暗号インフラは ECC 中心に再構築された
- **Curve25519 の設計哲学**: 「実装者を信用しない設計」。あらゆる入力で constant-time 実装可能、nothing up my sleeve、scalar 検証不要。「数学的に安全」より「現実に安全」を優先する転換
- **不可逆な未来計画としての PQC 移行**: 量子コンピュータの実用化時期は不明だが、実用化即座に既存暗号崩壊。この非対称性ゆえ「10年がかりの移行」が現在進行中
- **マルチスケール履歴活用**: TAGEの幾何級数履歴長は「どの時間スケールの相関が効くか事前不明」問題へのマルチバンド対応。FFT/CNNの多層受容野と同構造
- **抽象化漏れとしてのサイドチャネル**: Spectre/Meltdownは「ISAの逐次意味論」と「μarchの投機」の間の抽象化漏れ。キャッシュ/予測器/TLBは観測可能で副作用を残す現実が30年経って露呈
- **投機機構の普遍性**: 分岐予測・キャッシュ・TCP輻輳制御・GC write barrier・TAGE予測 — 全てが「過去観測から未来推測、外れたらロールバック」の同一パターン。性能を得るために不確実性に賭け、ハザード時に代償を払う構造
- **インプレース更新排除の生産性**: LSM, Event Sourcing, Git, 関数型、Rust所有権 — 自己課した「不変性」という一つの制約が、並行性・耐障害性・スナップショット・レプリケーション全てを連鎖的に単純化する。制約が自由をもたらすパターンの最強例
- **compactionとGCの構造的同型性**: LSM compaction = Mark-Compact GC（生データを集めて古領域解放）、レベル階層 = 世代別GC、tombstone = 弱参照。両者はストレージとメモリという異なる階層で同じ問題を解く双子のアルゴリズムファミリー
- **ハードウェア特性が複数世代で有効なデータ構造**: LSMはHDDのシーク回避で設計され、SSDのP/Eサイクル寿命・FTL GC・シーケンシャル書き込み優位性にも整合。「追記のみ」という抽象的性質が複数世代のストレージに残存する理由
- **確率的早期リジェクトパターン**: Bloom/Ribbon/Cuckoo Filter, count-min sketch, 分岐予測のBTB, TLB - 全て「正確性の一部を速度と引き換える」設計。Negative検出を高速化する確率的構造はCS全体に浸透
- **進捗条件は耐故障性の直交軸**: Wait-free/Lock-free/Obstruction-free/Blocking の階層は「表現力」ではなく「スレッド停止に対する免疫強度」の階層。従来の性能軸と独立な設計次元
- **メモリ回収はGCとロックフリーの共通の核**: ハザードポインタ=分散並行GC、RCU grace period=並行mark、LSM compaction=Mark-Compact GC。ストレージ/メモリ/ロックフリーの3スケールで同一問題が出現
- **CAS のユニバーサリティ**: Herlihyの consensus hierarchy で CAS が ∞-consensus オブジェクトであることが、現代全CPUが CAS を持つ理論的正当化。命令セット設計への数学的ガイダンスが機能した稀なケース
- **ヘルプパターン(cooperative helping)**: MS-queue の tail ヘルプ、RCU、分散合意の Byzantine helping — 「他人が詰まったら自分が代行」。individualism ではなく collectivism が lock-free progress の本質
- **不可能性結果は設計指針**: FLP、Herlihy consensus hierarchy、CAP、RUM予想 — 全て「何を諦めるか」を示す。ネガティブ結果がポジティブ設計を駆動するパターン

## 未解決の疑問

- QUICの損失検知と輻輳制御 (RFC 9002): TCPとの差異、接続マイグレーション時の輻輳状態の扱い
- AQM（Active Queue Management）: RED, CoDel, PIEとCCアルゴリズムの相互作用
- Bufferbloat問題とCoDel/fq_codelのデプロイ状況
- TCPペーシングとNICハードウェアオフロード（TSO, GRO）の関係
- マルチパスTCP (MPTCP): 複数経路間の輻輳制御の結合問題
- WALとクラッシュリカバリの仕組み（B+木のin-place更新との整合性）
- バッファプール管理とページ置換アルゴリズム（LRU-Kなど）
- クエリオプティマイザのインデックス選択コストモデル
- Learned Index（機械学習ベースのインデックス）の実用化状況
- Copy-on-Write B+木によるMVCC実現（LMDB/BoltDB）
- Myhill-Nerode定理: 正規言語の必要十分条件。ポンピング補題の弱点を補完
- 正規言語の閉包性: 和・連接・閉包・補集合・交差に対する閉包と、文脈自由言語との差異
- Glushkov構成: ε遷移のないNFAを直接生成するThompson's constructionの代替手法
- 決定性プッシュダウンオートマトンとLR構文解析: 文脈自由言語の決定的部分クラスとコンパイラの関係
- Hyperscan: IntelのSIMDベース高性能正規表現エンジンの設計
- VIPT キャッシュ設計: TLBアクセスとL1キャッシュの並列化、エイリアシング問題
- NUMAアーキテクチャ: ソケット間のメモリアクセスレイテンシ非対称性
- GPUメモリ階層: scratchpad、コアレスドアクセス、CPUとの設計思想の違い
- Cache-oblivious B木の実装と実用事例
- Paxos原論文の正確な理解: Single-Decree PaxosとMulti-Paxosの構造
- ビザンチン障害耐性（BFT）: PBFT、HotStuffなど悪意あるノードへの対処
- EPaxos / Flexible Paxos: リーダーレスコンセンサス、過半数制約の緩和
- 分散トランザクション: 2PC/3PCとコンセンサスの関係（Percolator, Spanner）
- TLA+によるRaftの形式検証
- KSM（Kernel Same-page Merging）: CoW応用としての重複ページ統合、仮想化環境での効果
- IOMMU: デバイスDMAに対する仮想メモリ保護
- Persistent Memory（PMEM）とDAX: mmapとNVDIMMの組み合わせ
- Linux MGLRU（Multi-Generation LRU）: kernel 6.1の改良ページ置換の設計思想
- **格子ベース暗号（Lattice-based）の数学**: LWE（Learning With Errors）と Module-LWE の構造、ML-KEM/ML-DSA の内部
- **ペアリング暗号（Pairing-based）**: BLS 署名、Identity-based encryption、ゼロ知識証明（zk-SNARKs）の数学的基礎
- **同型暗号（Homomorphic Encryption）**: BFV/CKKS スキーム、暗号化されたデータ上での演算
- **TLS 1.3 のハンドシェイク詳細**: ECDHE_X25519 + AEAD-ChaCha20-Poly1305 の組み合わせ
- **量子鍵配送（QKD）**: BB84プロトコル、無条件安全性の物理的根拠
- **TAGE-SC-L**: CBP-5優勝の Statistical Corrector + Loop predictor の構造
- **Transient Execution Attacks系譜**: L1TF/Foreshadow、MDS/ZombieLoad、LVI、Retbleed、Inception (Zen 3/4)
- **Intel eIBRS / AMD AutoIBRS**: ハードウェア側投機実行保護の詳細
- **VLIW/EPIC (Itanium) 敗北の教訓**: 静的スケジューリングが動的OoOに負けた根本理由
- **Apple M シリーズの分岐予測器**: リバースエンジニアリング知見
- **Memory Disambiguation Predictor**: Load/Store Queue での依存投機
- **DSB (Decoded Stream Buffer)**: uop cache と分岐予測の連携
- **RocksDB詳細チューニング**: `level_compaction_dynamic_level_bytes`, `compaction_pri`, `target_file_size_multiplier`, MyRocks本番パラメータ
- **Bε-tree / Fractal Tree Index (TokuDB/PerconaFT)**: B木のノードにバッファを持つ中間設計、RUM空間での位置付け
- **WiscKey (FAST 2016)**: Key-Value分離によるwrite amp削減手法
- **Learned Index / Learned Bloom Filter**: MLでインデックス・フィルタを置換する研究
- **ClickHouse MergeTree**: Primary key sparse index、skip indexの独自設計
- **Shard-per-core アーキテクチャ (ScyllaDB/Seastar)**: mutex地獄を避けた設計

---

### ガベージコレクションアルゴリズム（2026-04-18）
- **GC の基本問題**: 動的確保メモリのうち「今後アクセスされない」ものの自動解放。手動管理（malloc/free）のバグ（UAF/double-free/leak）を構造的に排除
- **到達可能性解析**: Root Set（スタック・グローバル・レジスタ）から有向パスで到達可能なオブジェクトを生存、残りをガベージ
- **古典アルゴリズム**: 参照カウント（循環参照問題）、Mark-Sweep（断片化）、Mark-Compact（移動コスト）、Copying/Cheney（ヒープ半分利用）
- **世代別仮説（Weak Generational Hypothesis）**: 「多くのオブジェクトは若くして死ぬ」。Young（Minor GC頻繁）・Old（Major GC稀）で分離管理
- **Card Table / Remembered Set**: Old→Young 参照の追跡機構。世代間参照の高速走査を可能にする
- **三色マーキング（Dijkstra 1978）**: 白（未訪問）・灰（訪問済・子未完）・黒（完了）。**Strong Tri-Color Invariant**: 黒→白直接参照の禁止
- **Write Barrier**: Mutator 動作中の参照変化を捕捉。Dijkstra Insert（白を灰化）、Yuasa Delete（削除前に灰化）、Go Hybrid
- **Go GC**: 並行三色 + Pacer（GOGC環境変数で次サイクルタイミング制御）。STW 500μs以下目標をGo 1.12で達成
- **G1GC（Java 9+ デフォルト）**: ヒープを等サイズリージョン（1-32MB）に分割、ガベージ密度高リージョン優先。MaxGCPauseMillis で停止目標設定
- **ZGC（低レイテンシ）**: Colored Pointer（64bit に mark/remap メタデータビット埋込）+ Load Barrier + self-healing。**TB級ヒープで 1ms 未満 pause**
- **Shenandoah**: Brooks Pointer による forwarding、ZGC の代替設計
- **最新動向**: Generational ZGC (Java 21)、Project Lilliput（64bit ヘッダ化）、Far Memory GC（CXL/RDMA）
- **GC vs 静的解析**: Rust の所有権・借用・ライフタイムは**コンパイル時に解放タイミング決定**。動的GC と対極のアプローチで同問題を解く
- **「停止時間 vs スループット」は本質的トレードオフ**: リアルタイム（低レイテンシ優先）vs バッチ（高スループット優先）で選択が反転

---

### KademliaとDHT（2026-04-22）
- **DHTが解く問題**: 中央サーバなしで数百万のノードに分散した `key→value` を O(log N) でルックアップし、ノードの頻繁な出入り（churn）に耐え、全ノードが対等である——3条件の同時達成
- **DHT系譜**: Chord（2001 MIT、円形IDリング+フィンガーテーブル）→ Pastry/Tapestry（プレフィックスルーティング）→ **Kademlia（2002 NYU、Maymounkov & Mazières）**。Kademliaは BitTorrent DHT / IPFS / Ethereum Discovery / Tor hidden services の基盤となり事実上の業界標準
- **XOR距離メトリック**: `distance(a,b) = a XOR b`（整数解釈）。メトリック公理を満たし、さらに**unidirectional**（任意のxと距離Dに対しyが唯一）、**abelian group**（可換群）で数学分析が閉じる。計算はCPU 1サイクル
- **k-buckets**: 160個の距離バケット（距離2^i以上2^(i+1)未満のノードを最大k=20個保持）。LRU置換ポリシーが**Sybil攻撃耐性の核心**——古いノード優先で「滞在時間を攻撃コストに変換」。暗号に頼らず時間を通貨化する設計
- **ルックアップアルゴリズム**: α=3並列でFIND_NODE、各応答から近いノードに再帰、収束まで。各イテレーションでkeyとの最長一致プレフィックスが1ビット以上伸びるためO(log₂ N)ホップ
- **4つのRPCで完結**: PING / STORE / FIND_NODE / FIND_VALUE。keyは最近接k個に冗長複製、1時間ごとrepublish、24時間expire。シンプルさの極致
- **実装実例**: BitTorrent Mainline DHT（数百万ノード）、IPFS/libp2p（CID）、Ethereum Node Discovery v5、Tor v3 hidden services
- **設計思想の普遍性**: 「距離の定義を変える」だけでアルゴリズムの美しさが一変。Chord（リング距離）→ Pastry（プレフィックス）→ Kademlia（XOR）。**「LRUが攻撃耐性になる」**という素朴設計の逆説——滞在時間を攻撃者のコストに変換する時間経済学
