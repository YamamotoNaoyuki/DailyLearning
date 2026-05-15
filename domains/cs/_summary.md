# コンピュータサイエンス 分野サマリー

**エントリ数**: 34
**最終更新日**: 2026-05-16

## 蓄積された知識

### TLA⁺ と形式手法：並行・分散システムの仕様検証 (2026-05-16)
- **TLA⁺** = Temporal Logic of Actions Plus、Leslie Lamport（1990年代）。実装ではなく **設計** を検証する形式仕様言語。集合論+一階述語論理+時相演算子で書く。状態=変数値の組、アクション=状態遷移述語（プライム x'）、挙動=状態の無限列、仕様=初期+常に何らかのアクション+公平性
- **時相演算子**: □P（常に）、◇P（いつかは）、□◇P（公平性）、◇□P（安定性）
- **PlusCal**: 擬似コード風の構文（while/if/await）で書け、TLA⁺ に自動変換。学習障壁を下げる
- **TLC モデル検査器**: 仕様から全到達状態を列挙し、安全性属性（不変条件）と活性性属性（liveness）を検査。有限のモデルパラメータ（プロセス数 3 等）で網羅、Small Scope Hypothesis（バグは小さい例で再現される）に依拠
- **TLAPS（TLA⁺ Proof System）**: 機械支援の定理証明系。Paxos、Disk Paxos、Byzantine Paxos、Memoir、Spire 等の完全証明実績
- **業界採用**: AWS（DynamoDB / S3 / EBS / Cosmos DB 等で本番投入前検証）、Microsoft（Xbox One メモリマネージャ）、CockroachDB、MongoDB Raft 実装。Chris Newcombe らの CACM 2015 論文「How Amazon Web Services Uses Formal Methods」が転換点。**DynamoDB で 35 ステップ深さの反例発見**（コードレビュー数百時間でも見つからなかった）
- **対比表**: TLA+（並行・分散、時相論理）vs Alloy（集合論、可視化）vs Coq/Lean（定理証明完備）vs Z（並行性弱い）vs Spin（プロトコル特化）vs CBMC（C コード）
- **限界**: 学習曲線が急、仕様と実装の乖離、状態空間爆発。**[[FoundationDB と DST]] のような実装レベルテストと補完関係**
- **新潮流**: PGo（PlusCal→Go 変換、MIT）、Apalache（SMT ベース）、Quint（2024 年、TypeScript 風シンタックス）、Stateright（Rust）
- **核心洞察**: 「証明する」ツールでなく「設計を強制的に厳密化する」ツール。**検査結果より、書く過程に価値がある**。人間の作業記憶 7±2 チャンクの限界を計算的補綴具で補う（小脳の内部モデルと同型）。「TLA⁺ で設計検証 + DST で実装検証」が現代分散システム品質保証の最先端

### Burrows-Wheeler 変換 (BWT) と FM-index ― 圧縮全文検索の設計哲学 (2026-05-15)
- **BWT (Wheeler 1983, Burrows-Wheeler 1994)**: 入力文字列の全循環シフトを辞書順ソートし、最終列を取り出す可逆変換。同じ文字が「ラン」になりやすい並び替え。bzip2 (1996) が後段の MTF + ハフマン/算術符号化と組み合わせて gzip を上回る圧縮率を達成
- **Suffix Array との対応**: BWT[i] = T[SA[i] − 1]（mod n）として計算可能。SA-IS, DC3 で線形時間 O(n) で suffix array を構築できるので BWT も O(n)
- **FM-index (Ferragina & Manzini 2000)**: 圧縮されたまま全文検索可能な索引。**「圧縮 + 検索」を同時達成**する初めての構造。構成要素は BWT(T)、C 配列、Occ(c, k) 関数、Sampled suffix array。サイズはエンピリカル・エントロピー H_k の n+o(n) ビット
- **Backward Search**: **パターンを後ろから処理** → O(|P|) で範囲を絞り込み。範囲 [sp, ep] を保持しながら sp = C[c] + Occ(c, sp-1)+1, ep = C[c] + Occ(c, ep) の漸化式を回す。LF mapping (Last-to-First) の本質
- **Wavelet Tree**: 多文字アルファベットを二分木に再帰的に分解、各ノードで bitmap rank を行う。空間 n log σ + o(n log σ) ビットで O(log σ) クエリ
- **Sampled SA + LF mapping**: SA を 1/k 間引いて保存し、未保存位置からは LF を繰り返し適用してサンプル位置まで戻る。空間効率と復元時間のトレードオフ
- **バイオインフォマティクスでの大成功**: ヒトゲノム 3GB → BWT+FM で 1-2GB。短いリード検索が数 ms。**Bowtie (Langmead 2009), BWA (Heng Li 2009)** が NGS 時代の基盤
- **拡張**: 双方向 FM-index (ロングリード対応)、RLBWT (反復配列で空間を r-bit に圧縮)、r-index (Gagie-Navarro-Prezza 2018) でペタバイト級 PanGenome に対応
- **核心洞察**——「圧縮された表現は元データの全構造を持つ」——情報理論と計算可能性の境界を押し広げた。「逆順処理」の力（forward では指数的探索が backward では単調絞り込み）。Suffix tree/array/BWT/FM-index は同じ「接尾辞構造」の異なる視点

### ラムダ計算と型システムの基礎 ― STLC から System F、Curry-Howard へ (2026-05-14)
- **ラムダ計算 (Church 1932-36)**: 変数 + 抽象 λx.M + 適用 M N の三構成要素でチューリング完全。**「計算とは関数適用そのもの」**――関数型言語の理論基盤
- **型なし λ のパラドックス**: Ω = (λx. x x)(λx. x x) が無限簡約、Curry のパラドックスで論理的矛盾。型システムは**自己適用を構文レベルで排除**する装置
- **STLC (Church 1940)**: σ → τ の関数型のみ。**強正規化定理 (Tait 1967)**: 任意項が有限ステップで停止。チューリング完全性 vs 停止性のトレードオフ
- **Curry-Howard 同型 (1934/1969)**: 型 = 命題、項 = 証明、関数型 = 含意、関数適用 = Modus Ponens、β-簡約 = 証明正規化。**「型を持つプログラムを書くこと」=「直観主義論理で命題を証明すること」**。Coq/Lean/Agda の理論基盤
- **System F (Girard 1972 / Reynolds 1974)**: 全称型 ∀X. τ で**型を変数化**。`id = ΛX. λx:X. x : ∀X. X→X`。パラメトリック多相 ―― Haskell/ML/Rust generics の祖先。強正規化は保持される
- **System F の代償**: 型推論不可能 (Wells 1994)。Hindley-Milner は rank-1 多相に制限して型推論可能性を回復。**「型推論可能性 vs 表現力」**のトレードオフ
- **上位系**: System Fω（type constructor 多相、Haskell type families）、依存型（型が値に依存、Idris/Lean）、Calculus of Constructions (Coquand & Huet 1988) ――Coq の基盤、Four Color Theorem 機械検証 (Gonthier 2008)
- **線形型・Quantitative Type Theory**: 変数の使用回数を型で管理（0/1/ω）。Rust 所有権モデル、量子プログラミング言語、Idris 2 採用。「**計算資源そのものを型で管理する**」未来
- **核心洞察**: 型システムは**禁止の体系**――許容を増やせば決定可能性を失う。**「論理が型システム設計の最終仲裁者」**。System F の表現力は「型変数化」というたった一つの抽象化から生まれる ― 抽象化の段数が言語の表現力を決定する

### TLS 1.3 ハンドシェイクの設計哲学 — なぜ過去の設計を根本から捨てたか (2026-05-13)
- **MAC-then-Encrypt の構造的欠陥**: TLS 1.2 の CBC + MAC-then-Encrypt は原理的に修正不可能なレベルで壊れていた。BEAST (2011) / Lucky 13 (2013) / POODLE (2014) は全て同じ根本欠陥の表れ。TLS 1.3 は MAC-then-Encrypt を廃止し AEAD のみに統一した
- **静的 RSA 鍵交換の廃止と前方秘匿性の強制**: TLS 1.2 の RSA 鍵交換では、サーバーの長期秘密鍵が漏洩すれば記録していた全過去通信を復号できた（前方秘匿性なし）。TLS 1.3 はすべての鍵交換を一時 ECDHE/DHE に限定し、前方秘匿性を強制
- **暗号スイートの大幅削減（数十種類→5種類）**: 「柔軟性がある限り弱い選択肢を選ぶ人がいる」という現実への対処。暗号スイートのグレシャムの法則を制限で排除した設計
- **1-RTT ハンドシェイク**: ClientHello に key_share（DH公開値）を最初から含めることで、ServerHello 受信直後に DH 共有秘密を計算できる。**サーバーはその後の全メッセージ（証明書を含む）を暗号化**できる。TLS 1.2 では証明書は平文だった
- **HKDF 三段階キースケジュール（Krawczyk OPTLS設計）**: Early Secret → Handshake Secret → Master Secret の連鎖。PSK と ECDHE を独立した段階で混入し、片方が漏洩しても他方が守る。各段階でトランスクリプトハッシュを混入してダウングレード攻撃を防止。目的別（ハンドシェイク/アプリケーション/再開）に鍵を分離
- **0-RTT の意図的なトレードオフ**: PSK を使って最初のリクエストを 0 往復で送れるが、replay 保護がない。RFC 8446 はこれを設計上の明示的なトレードオフとして記載し、「idempotent 操作（GETなど）にのみ使え」とアプリケーションに責任を委ねた。完全な replay 保護 = 最低 1-RTT 必要は数学的に証明可能
- **SIGMA プロトコルと暗号化された証明書**: CertificateVerify は DH 鍵交換との identity misbinding 攻撃を防ぐためハンドシェイクトランスクリプトへの署名を含む。証明書は ServerHello 後に暗号化されるが、SNI は ClientHello 内で平文のまま（ECH RFC 9849 で対処中）
- **削除カタログが欠陥の歴史書**: 廃止された RSA鍵交換・CBC暗号・RC4・MD5/SHA-1・Export暗号・圧縮・Renegotiation は全て実際に悪用された攻撃の根拠。特に Export 暗号（FREAK/Logjam 2015）は冷戦期の輸出規制の遺物が30年後に攻撃に使われた
- **核心洞察**: 「削除こそが最大の設計成果」——TLS 1.3 は追加した機能より削除した機能の方が重要。後方互換性への政治的圧力に抗して危険な機能を廃止した IETF TLS WG の 4 年間（2014〜2018）の仕事。「柔軟性は脆弱性の母」「制限が安全性を生む」の典型例。0-RTT のトレードオフ明示化は CAP定理・RUM予想と同型の「何を犠牲にするかの明示」設計哲学

### 計算可能性理論 — チューリングマシン・停止問題・Rice の定理 (2026-05-12)
- **チャーチ・チューリングのテーゼ**: 「直感的に計算可能 ⟺ チューリングマシンで計算可能」。λ計算・再帰関数・TM が等価。数学的定理でなく自然法則的主張だが90年以上反例なし。量子計算ですら計算可能性の範囲は変えない（変えるのは計算量だけ）。TM の本質＝「無限のテープ × 有限の制御」という非対称が万能性を生む
- **万能チューリングマシン**: TM の記述 ⟨M⟩ を文字列化して別の TM の入力に置ける → U(⟨M⟩,w)=M(w)。これがストアドプログラム方式（フォン・ノイマン型）の理論的原型。Lisp の eval、JVM、QEMU、ブラウザの JS エンジン、MoE の重みを読んで走らせる推論エンジンはすべて万能 TM のインスタンス。「コードとデータの区別は便宜的」＝メタプログラミングの基盤であり同時にコードインジェクション脆弱性の根源
- **停止問題は決定不能**: 「TM M が入力 w で停止するか」を判定する H は存在しない。証明＝対角線論法（D(⟨M⟩): if H(⟨M⟩,⟨M⟩)=yes then loop forever else halt、に D 自身を入力すると矛盾）。「自己言及＋否定」が嘘つきのパラドックス・ラッセルのパラドックスと同じ構造。帰結：完璧な無限ループ検出器・最適化コンパイラの停止保証・リソース上限の事前判定は原理的に不可能
- **Rice の定理**: プログラムが計算する関数についての、自明でないあらゆる「意味的（extensional）」性質は決定不能。帰結（すべて決定不能）：プログラム等価性判定（コンパイラ最適化の正しさ検証が自動化できない理由）、全域性、完全な静的バグ検出、完全なマルウェア検出。「プログラムを実行せずにその"意味"を完全に知ることはできない」＝静的解析が必ず保守的（誤検出を許す）か不完全（見逃しを許す）になる根本理由
- **決定不能性の階層と帰着**: 多対一帰着 A≤ₘB で「難しさ」を比較。停止問題は半決定可能（r.e.）だがその補集合は r.e. ですらない。算術的階層 Σₙ/Πₙ（量化子の交替数＝計算不能性の度合い）。ゲーデルの第一不完全性定理＝「証明可能性が決定可能なら停止問題も決定可能になる」→ 証明可能性は決定不能（Entscheidungsproblem への否定的回答、チャーチ＆チューリング 1936）。「真である ⊋ 証明できる」のギャップ ＝ 「半決定できる ⊋ 決定できる」のギャップの論理版
- **「決定不能を回避する」＝制限という工学**: eBPF verifier（無制限ループ禁止／bounded loops で停止性を決定可能な部分集合に押し込める）、型システム（HM は決定可能だが System F の完全な型推論は決定不能）、正規言語 vs 文脈自由言語（包含・等価の判定可能性が違う）、モデル検査（有限状態に限れば決定可能）、全関数型言語（Agda/Idris の totality checker、構造的再帰のみ許してチューリング完全性を犠牲に停止保証を得る）。**「理論が不可能と言う ⇒ 入力を制限する／近似で妥協する／トレードオフを明示的に設計する」がシステム工学の最も汎用的なパターン**（MoE のルーティング近似、anatomy の把持力制御、golf のコースマネジメントと同型）
- **核心洞察**: 「自己言及は両刃の剣」——「プログラムをデータとして扱える（万能性）」という強力さと「プログラムについての完全な判定はできない（停止問題・Rice）」という限界は同じコイン（universality）の表裏。「完璧な静的解析が存在しないのはツールが未熟だからでなく原理的に不可能だから」→ 正しい戦略は「完璧を目指す」でなく「誤検出と見逃しのトレードオフをどう設計するか」

### HyperLogLog と Count-Min Sketch — ストリーミング近似アルゴリズム (2026-05-10)
- **ストリーミングモデル**: 無限長データ列に対し O(polylog n) メモリで近似回答。Count-distinct (HLL)、frequency estimation (CMS)、heavy hitters、quantile が四大問題
- **HyperLogLog**: Flajolet-Fusy-Gandouet-Meunier 2007。Flajolet-Martin (1984) → LogLog (1985) の系譜。バケット分割 + 末尾連続 0 ビット数の最大値 + **調和平均**で分散最小化。バケット数 m=2^14 で約 12 KB、標準誤差 1.04/√m ≈ 0.81%。**1 兆カーディナリティでも誤差 1% 程度**
- **Count-Min Sketch**: Cormode-Muthukrishnan 2003。d 個独立ハッシュ関数 + d×w 整数配列。更新で全行 +1、クエリで min。w=⌈e/ε⌉, d=⌈ln(1/δ)⌉。**過大誤差のみ保証 (過小なし)**、誤差≤εN 確率 1-δ。実装は超軽量
- **Min vs Max の対称性**: HLL の max は希少事象の珍しさを活用、CMS の min は衝突過大の最小化。**最大と最小は異なる情報を抽出する**統計的二重性
- **HLL++ / HyperLogLogLog**: Heule 2013 (Google) で sparse encoding と small cardinality bias 補正。Karppa-Pagh 2022 でさらに 70% メモリ圧縮 (Golomb-Rice 符号化)
- **応用**: Redis HLL (Sparse/Dense 自動切替)、BigQuery、Reddit、Twitter フォロワー差分、Google AdSense クリック頻度、Cassandra hot key 検出、TensorFlow count_table
- **核心洞察**: 「正確を諦めて巨大スケールに到達」というパラダイム転換。確率的データ構造は Bloom (1970)→MinHash→CMS→HLL の系譜で、各々がトレードオフを別の場所に置いた美しい設計空間。**生物の sensor fusion (筋紡錘+GTO) と同じ「独立観測の統合」原理**

### TCP輻輳制御の進化 — Reno, CUBIC, BBR (2026-05-09)
- **歴史的契機**: 1986年インターネット輻輳崩壊事件（Stanford-LBL間のスループット32kbps→40bps激減）。Van Jacobson 1988「TCP Congestion Avoidance and Control」論文が現在まで続く枠組みを確立
- **Reno（1990s, AIMD古典）**: ACK毎にcwnd+1線形増加、ロス時50%減。**「ロスベース」=パケットロスを輻輳の唯一の信号として使う**。スロースタート/輻輳回避/高速再送/高速回復の4状態モデル。1Gbps高速回線では線形増加が遅すぎ
- **CUBIC（2008、Linux 2.6.18から標準）**: KAIST Sangtae Ha & Injong Rhee 開発。**3次関数 W(t) = C(t-K)³ + W_max** の窓制御。前回W_max付近でゆっくり、超えると急速増加。ロス時30%減（Renoより穏やか）。**RTT非依存**で高RTTでも公平。Linux/Windows 10以降のデフォルト
- **BBR（2016、Google）**: Neal Cardwell, Yuchung Cheng らが**モデルベース**へパラダイム転換。**BtlBw（ボトルネック帯域）×RTprop（最小RTT）= BDP**でレート制御。**ロスを輻輳信号として使わない**。YouTube/Spotify採用後、平均スループット14%向上、リバッファリング3%削減
- **ロスベースの宿命**: パケットロスは「輻輳」と「ランダム障害」を区別不能。長距離ファイバ・無線でロス率0.1-1%常時発生→CUBICは輻輳と誤認しcwnd減少。**100ms+RTTでBBRがCUBICの数倍スループット**の理由
- **BBRv1の公平性問題とBBRv2/v3**: BBR vs CUBICでBBRが80-90%帯域取得（不公平）、shallow bufferで大量ロス引き起こし。**BBRv2（2019）**でECN信号反応＋ロス率2%閾値で減速。**BBRv3（2023）**でさらにフェアネス改善
- **核心洞察**: **「ドメインの基本前提を疑う」ことが革新の源泉**。「ロス=輻輳」という1980年代地上有線の暗黙前提を、Googleは「現代の無線・衛星・光網では成立しない」と看破。**「フェアネス vs 効率性」のトレードオフ**は分散システム設計の普遍的問題

### ガベージコレクション — 世代別から ZGC まで (2026-05-08)
- **GCの根本問題**: throughput vs latency, compaction vs fragmentation, generational vs flat, concurrent vs STW のトレードオフ。「いつ・どのオブジェクトが死んでいるか」を安全・高速・低レイテンシで判定
- **世代別GC**: 弱い世代仮説「ほとんどのオブジェクトはすぐ死ぬ」を活用。Young (Eden+Survivor) で頻繁・小規模、Old は稀・大規模。Card Tableで Old→Young参照をwrite barrierで効率追跡（512バイト単位の dirty card）
- **G1 GC** (JDK 9+デフォルト): 約2000個リージョン分割、ガベージ密度の高いリージョンから回収（Garbage-First）。MaxGCPauseMillis target 設定可能。Concurrent markingあるが evacuation phase は STW。100GB級ヒープでpause数百ms到達
- **ZGC** (JDK 11+, JDK 25 LTS でデフォルト): **Colored Pointers**（64bit ポインタ上位bitにメタデータMarked0/1, Remapped, Finalizable）+ **Load Barrier**（参照ロード毎にメタデータ検証・healing）。sub-millisecond pause、ヒープサイズ非依存。JDK 21で Generational ZGC
- **Shenandoah** (Red Hat): ZGCと同目標、別実装。**Brooks Pointers**（各オブジェクト先頭に転送ポインタ）。32/64bitアドレス空間制約なし、移植性高い、pause<10ms
- **Read vs Write Barrier**: Card TableはWrite barrier（書込み時作業）、ZGCはRead barrier（読込み時作業、CPU branch predictorでほぼゼロコスト化）。**ハードウェアの統計的振る舞いを前提にした設計**
- **核心洞察**: GC設計史は「STWをいかに減らすか」の連続。Mark-Sweep→Generational→CMS→G1→ZGC/Shenandoah の各世代が並行性拡大の別解。Colored Pointer は「データ構造を実装の制約として活用する」eBPF的発想

### Paxos と Raft — 分散合意アルゴリズムの設計と「理解可能性」 (2026-05-07)
- **FLP 不可能性 (Fischer-Lynch-Paterson 1985)**: 非同期通信で 1 ノードでも故障する可能性があれば、合意は決定的アルゴリズムでは保証不可能。Paxos/Raft は「停止故障モデル + 安全性優先 + ランダム化タイムアウトで確率的進行」で実用化
- **Paxos (Lamport 1990/1998)**: Proposer/Acceptor/Learner の 3 役割、Prepare-Accept 2 フェーズ、過半数 quorum 交差性で安全性保証。Multi-Paxos でリーダー固定化しログ複製。Mike Burrows: 「世界には合意アルゴリズムは Paxos だけ、他は不正確版か特殊ケース」だが実装は悪戦苦闘
- **Raft (Ongaro-Ousterhout 2014)**: 「**理解可能性 (understandability)** を第一原理に置く」設計判断。Leader/Follower/Candidate 3 状態、リーダー選出 + ログ複製 + 安全性に問題分割。**Follower は最新ログ持つ Candidate にのみ投票**で「過半数票を得るリーダーは必ず最新ログ持つ」を強制 — 実装簡略化のための強制約
- **両者の本質差**: Paxos は対称的 (リーダー暗黙)、Raft は非対称 (リーダー明示・全通信が Leader→Follower)。Heidi Howard 「両者は事実上等価、Raft の制約は実装簡略化のための賢明なトレードオフ」
- **エコシステム**: Paxos 系=Chubby/ZooKeeper(Zab)/Spanner、Raft 系=etcd/Consul/TiKV/CockroachDB/MongoDB/KRaft。新規プロジェクトは Raft 圧倒的多数=「実装難易度=採用判断」
- **核心洞察**: Raft の最大貢献は「理解可能性を測定可能な研究課題にした」こと。Ongaro 博論は 43 人で理解度テスト実施、人間の認知能力をアルゴリズム設計の変数として扱った稀有な研究。CRDT が「衝突解決を事前定義」するのと同じ哲学=人間の限界を踏まえた制約設計

### Hybrid Logical Clock (HLC) — 物理時刻と論理時刻のハイブリッド (2026-05-06)
- **HLC コア発想 (Kulkarni et al., OPODIS 2014)**: タイムスタンプ `(l, c)` ペア。`l` は最大観測物理時刻ベース値、`c` は同 `l` 内のカウンタ。Lamport 時計の `max` 演算 + 物理時刻参照を組合せ、O(1) サイズで wall clock 近似と因果保証を両立
- **更新ルール**: ローカルイベントで `l ← max(l, pt())`、`l` 更新なら `c++`、更新時 `c=0`。受信時は `l ← max(l_old, m.l, pt())` で 4 ケース分岐。`l - pt()` drift は NTP skew bound 内で有界
- **TrueTime (Spanner, OSDI 2012) 比較**: GPS+原子時計で `[earliest, latest]` 区間 (ε ≈ 1〜7ms)、commit-wait `2ε` で external consistency 達成。HLC は wait なし + retry コスト、causal+serializable のみで external 不保証
- **保証の片方向性**: `e → f ⇒ HLC(e) < HLC(f)` のみ。逆は不成立。これは設計判断 — 双方向はベクトル時計 O(N) が必要、HLC は意図的に放棄。causal session には十分
- **bounded skew assumption**: 正しさは clock skew ε が有限であることに依存。CockroachDB は `--max-offset 500ms` で陽に表現、超過したノードは panic 自殺 (壊れた時計で動くより安全)
- **採用例**: CockroachDB (uncertainty interval `[ts, ts+max_offset]` で read restart)、YugabyteDB (Raft entry timestamp)、MongoDB 3.6+ (`afterClusterTime` causal session)。FoundationDB は対照的に単一 sequencer 設計
- **HLC vs TrueTime トレードオフ**: 「ハードウェアコストで latency 確定」vs「ソフトウェアコストで retry 確率受容」。Spanner = Google 帝国内、CockroachDB/YugabyteDB = Spanner-like を任意クラウドで実現
- **Hybrid Vector Clocks (Demirbas-Kulkarni 2017)**: HLC のベクトル版で因果完全性 + 物理近似。**Stable timestamp** = follower read 用「safe_ts 以下は解決済み」保証で leader トラフィック分散
- **限界**: cross-region read-after-write は session token 伝播必須、`pt()` 逆行 (NTP step, leap second smear) で drift 蓄積、`c` overflow は `l++; c=0` 救済
- **核心洞察**: 「**因果完全性を捨てる**」明示的選択。学術的には vector clock が「正しい」が、運用では「O(1) で wall clock 近似 + ほぼ十分」が支配。Reed-Solomon → LRC で MDS 部分犠牲化と同型の工学判断。**Spanner = 不確実性をハードウェアで消す、CockroachDB = ソフトウェアで管理する**哲学差。Kulkarni 2014 論文一本がエコシステムを生んだ

### 永続データ構造とPath Copying (2026-05-05)
- **永続データ構造**: 変更操作後も過去の版を保持。Driscoll-Sarnak-Sleator-Tarjan 1986《Making Data Structures Persistent》で体系化。Clojure・Haskell・React state・Git の基礎
- **永続性の階層**: Ephemeral (揮発的) / Partially Persistent (旧版アクセスのみ) / Fully Persistent (旧版変更可) / Confluently Persistent (合流可、Gitの`merge`)
- **Fat Node Method**: 各ノードに複数版の値とバージョン番号を保持。検索 O(log m)、空間 O(1)/変更。逆ポインタ追跡が必要で実装複雑
- **Path Copying**: 変更されたノードからルートまでの経路上のノードのみコピー。O(log n) 時間・空間。バランス木の場合、最も実装しやすい
- **DSST Hybrid (Node Copying)**: Fat Node + Path Copying の組合せ。各ノードに少数の追加スロット、埋まったときだけ新ノード。**O(1)償却時間・空間**
- **Okasaki赤黒木 (1999)**: 永続赤黒木の挿入を約30行のHaskellで実装。`balance`関数の4パターンマッチング。再帰呼び出しが path copying を暗黙に行う。「**immutability が永続性を無料で生む**」
- **HAMT (Hash Array Mapped Trie)**: Bagwell 2001 + Hickey 2008永続化。32要素スパース配列、5bitセグメント、最大深さ7、ビットマップ実装。Clojure HashMap・Scala Vectorの基礎。実質O(1)アクセス
- **構造共有 (Structural Sharing)**: 変更経路以外を旧版と共有。React.memo の参照等価判定で再レンダリング自動最適化。Immer は Proxy で疑似可変インターフェイスを提供しつつ内部で path copying
- **核心洞察**——「不変性は時間旅行を可能にする」。Reduxタイムトラベルデバッガ、git checkout、Reactレンダー履歴の基礎。**並行プログラミングではロック不要**。「O(log n)は実用的にO(1)」（log_32(40億)≈7）
- **Zigアロケーターとの哲学的対比**: ArenaAllocator=「世代単位で一括解放」(過去を捨てる) vs 永続データ構造=「過去を残す」。両者とも個別freeを排除する点で共通だが、過去の扱いが正反対の双子戦略

### SSA形式とコンパイラ最適化 (2026-05-04)
- **SSA (Static Single Assignment)**: 各変数を静的に**一度だけ定義**する IR。Use-Def chain が単一ポインタに退化し、**sparse analysis** の基盤を提供。反復 dataflow O(N²) を O(use 数) に縮約
- **φ関数**: 合流点での value selection を表す仮想命令。同一ブロックの全 φ は **並列**評価 — これが out-of-SSA で parallel copy 問題を生む
- **支配境界 DF (Dominance Frontier)**: 「d が支配する領域のすぐ外側の合流点」。Cytron 1991 の核心定理「**φ は iterated DF に挿入すべき**」
- **Lengauer-Tarjan (TOPLAS 1979)**: 支配木を **O(E·α(E,N))** で計算。α は Ackermann 逆関数で実用上ほぼ定数。simple 版は O(m log n)
- **SSA構築 — Cytron et al. (1991, TOPLAS)**: 支配木 + DF 計算 → iterated DF にφ挿入 → pre-order rename。最悪 O(N²) だが almost linear。LLVM `mem2reg` の基盤
- **SSA構築 — Braun et al. (2013, CC)**: DF を計算しない**オンザフライ**法。`readVariable`/`writeVariable` API、incomplete CFG 対応、trivial φ removal で minimal SSA 保証。LLVM Cytron 実装より僅速。Cranelift, libFirm, LuaJIT 採用
- **SCCP (Wegman-Zadeck 1991)**: 未到達ブロックを `⊥` ではなく separately 扱い、定数 + 死コード分岐を同時発見。**SSA edge 上の lattice worklist** でほぼ線形
- **GVN (Alpern-Wegman-Zadeck 1988)**: 値番号で同値類分割。SSA の def 一意性により hash-cons がそのまま機能。φ を uninterpreted 関数扱いするため不完全 (Gulwani 2004 が完全多項式時間版)
- **LICM**: ループ不変は **オペランドが loop preheader を支配するか** だけで決まる — 反復 dataflow 不要
- **DCE**: 副作用ある命令を root に逆向き mark。SSA で def 一意のため到達不能 def は即削除
- **Out-of-SSA 変換**: 素朴な per-predecessor copy 挿入は **lost-copy / swap problem** を起こす。Briggs et al. 1998 が改良、**Sreedhar et al. 1999 (Method I/II/III)** が φ-congruence class で copy 最小化、**Boissinot 2009 (CGO)** が現代 LLVM 実装の系列
- **SSA-based レジスタアロケーション**: Chaitin 1981 で graph coloring 帰着 → NP完全。しかし **Hack-Goos 2006 (IPL)** + Brisk + Bouchez が独立に「**SSA の干渉グラフは chordal**」を証明 — 支配関係が perfect elimination order を誘導。**O(\|V\|·ω(G)) で最適彩色**可能、spilling/coloring/coalescing を decouple
- **Caveat (Pereira-Palsberg 2006)**: classical SSA elimination *後* の RA は再び NP完全。SSA-RA は **destruction 前に色付け、parallel copy 含む形で out-of-SSA** する必要
- **Linear Scan (Poletto-Sarkar TOPLAS 1999)**: live interval を線形スキャン、**O(V log R)**。HotSpot C1, V8 で採用、Wimmer 2010 の Extended 版が GraalVM で使用
- **採用例**: LLVM IR (純粋 SSA、memory は alloca + mem2reg)、GCC GIMPLE-SSA (4.0/2005)、HotSpot C2 **sea-of-nodes** (Click 1995 PhD、basic block を捨てデータ/制御依存を一様 graph)、**MLIR (Lattner CGO 2021)** は dialect-centric + SSA 核で multi-level IR、Mojo/IREE/CIRCT が採用
- **SSA 拡張**: **Gated SSA (Tu-Padua 1995)** = γ/μ/η で条件情報内包、**Array SSA (Knobe-Sarkar 1998)** = element-level + δ 関数で parallelization 解析、**HSSA (Chow 1996)** = μ/χ で alias/memory も SSA 化、**Concurrent SSA** = π/ψ で同期点表現
- **核心洞察**: SSA は λ計算の **A-normal form (ANF)** とほぼ等価 (Appel 1998 "SSA is Functional Programming") — φ は continuation の引数渡しに対応。**問題の難しさは表現に依存する** — Chaitin が25年封印した NP完全問題が IR を変えるだけで多項式時間最適に。**支配境界という幾何学**が「φ をどこに置くか」を graph-theoretic 不変量に reduce した美しさが Cytron 1991 の本質

### 分散システム一貫性モデル階層 — Linearizability vs Serializability vs Causal vs Eventual (2026-05-03)
- **直交する 4 軸**: (a) 単一オブジェクト vs multi-object transaction、(b) single total order の有無、(c) real-time order との整合、(d) 因果関係の保護。一次元の「強さ」に潰さず軸で整理すると 42+ モデル (Viotti-Vukolić 2016) の partial order が自然に見える
- **Linearizability (Herlihy-Wing 1990)**: single object + single total order + real-time。**Compositionality (locality)** が真価 — A と B が個別に linearizable なら A∪B も linearizable。SC にはない性質。MESI cache coherence は per-line linearizable だが組み合わせは TSO
- **Attiya-Welch 1994 下界**: clock skew u 環境で linearizable read/write は最低 u/4 遅延必要。SC は片方を local 完了可能。Spanner は GPS+atomic で u を ~7 ms に圧縮し commit-wait で吸収
- **Strict Serializability** = Linearizability ∘ Serializability。Spanner の "external consistency" と等価。Spanner / FoundationDB / CockroachDB / FaunaDB が目標とする最強レベル
- **Snapshot Isolation (SI)** が Repeatable Read を実用代替、**SSI (Cahill 2008)** で Write Skew 抑制し Serializable に到達 (PostgreSQL 9.1)。SSI の鍵は cycle 検出ではなく **rw-antidependency の "dangerous structure" 局所判定**
- **Causal+ (COPS, Lloyd 2011)** = Causal + convergent conflict handling (CRDT semilattice)。Eiger / AntidoteDB / Cosmos DB Session レベル。**HAT 可能 + 直感保持**でスイートスポット
- **PACELC (Abadi 2012)**: CAP の盲点である平常時 latency-consistency tradeoff を明示 (PA/EL = Cassandra/Riak、PC/EC = Spanner/VoltDB)。**HAT (Bailis 2014, VLDB)**: SI / Serializability は network partition 下で available 不可と証明
- **RAMP transactions (Bailis 2014)**: multi-partition の atomic visibility だけを単独提供、read 1RTT/write 2RTT。secondary index/materialized view 用
- **Jepsen 2025**: RDS PostgreSQL 17.4 で Long Fork anomaly 発見 (primary in-memory lock 順 vs secondary WAL 順の不一致)。TigerBeetle 0.16.x は Strong Serializability 保持確認、Bufstream 0.1.0 で Kafka 自身の transaction protocol bug 発見。Knossos (linearizability SAT) + Elle (cycle detection O(n) 級、VLDB 2020)
- **核心洞察**: 「強さ」は一次元ではない — **Linearizability ⊥ Serializability、合成して初めて両軸を捉える**。Compositionality こそ Linearizability の真価。**CRDT の semilattice = Causal+ の convergent handling = 順序代数 ≅ 一貫性証明**の同型 (Curry-Howard の分散版)。Jepsen が暴き続ける gap は「**形式モデルが論文では証明されても実装では崩れる**」現実

### Lamport 論理時計とベクタークロック (2026-05-02)
- **Lamport "Time, Clocks, and the Ordering of Events" (1978)**: 物理時計と完全同期は不可能 → 観測可能な因果関係だけで「順序」を定義する哲学的飛躍。分散システム理論の基礎
- **Happens-before 関係 (→)**: ①プロセス内順序、②送受信ペア、③推移律。a → b でも b → a でもない並行 (concurrent) イベントは順序を定義する必要がない
- **Lamport タイムスタンプ (スカラー)**: ローカルイベントで C++、受信時 C ← max(C, msg.C) + 1。`a → b ⇒ C(a) < C(b)` (clock condition) — **片方向のみ**保証、逆は不成立
- **Lamport 全順序**: (C, プロセス ID) の辞書式順序でタイブレーク。分散ミューテックスで使うが、人為的な順序を強制し因果関係を超える
- **ベクタークロック (Mattern 1989, Fidge 1988)**: 各プロセスが N 次元ベクトル V_i を持つ。受信時は要素ごとの max + 自身++。`a → b ⟺ V(a) < V(b)` の双方向対応で**因果関係を完全特徴付ける**。比較不能 = concurrent を明示
- **複雑度トレードオフ**: スカラー O(1) + 弱い情報 vs ベクトル O(N) + 完全情報。動的システム (mobile, IoT) ではベクトル長膨張が課題
- **Version Vector**: DynamoDB / Riak の eventual consistency DB で実装。読み出し時 concurrent 書き込みを siblings として返し、アプリで衝突解決
- **Dotted Version Vector (Almeida 2014)**: クライアント増加時の false concurrency 対処 (Riak)。古典 VV の純粋性を犠牲に実用性
- **Hybrid Logical Clock (Kulkarni 2014)**: 物理時計 + 論理オフセット。CockroachDB / MongoDB が採用。NTP 物理時計の人間可読性 + 論理時計の単調性
- **核心洞察**: 並行性は「順序が決まらない」のではなく「順序を決める情報が不足している」を**正直に表現**する設計概念。Cassandra 初期 LWW + 時計ずれ事故は論理時計省略の代償。Spanner の TrueTime は物理時計の不確実性を GPS+原子時計でハードウェア有界化

### Curry-Howard 同型 — 命題は型、証明はプログラム (2026-05-01)
- **核心**: 命題 ↔ 型、証明 ↔ プログラム（項）、証明の正規化 ↔ プログラム評価 (β-reduction)。論理体系と計算体系の同型
- **歴史**: Curry 1934 (含意のみ) → Howard 1969 (自然演繹 ↔ STLC 完全対応) → Martin-Löf 1972 (依存型 ↔ 一階述語論理) → Wadler 2015 CACM "Propositions as Types"
- **対応表**: ⊃→関数型→、∧→積×、∨→直和+、⊤→1、⊥→Void、∀→Π型、∃→Σ型、推論規則 ↔ 型付け規則
- **MP は関数適用**: P⊃Q が真 + P 真 → Q 真 ⇄ f: P→Q + x: P → f(x): Q。「**証明は構成 (proof is construction)**」(Brouwer-Heyting-Kolmogorov)
- **古典 vs 直観主義**: Curry-Howard は元来直観主義に対応。Griffin (1990) で **二重否定除去 ↔ call/cc**、排中律 ↔ continuation。Curry-Howard-Lambek 拡張で**圏論 (CCC)** との三項同型
- **Martin-Löf 型理論と依存型**: Π型 = 依存関数 = ∀証明、Σ型 = 依存ペア = ∃証明、Id 型 = 等式。**Voevodsky の Univalence Axiom (2009)** で同型な型は等しい (HoTT)
- **証明支援系**: Coq (1989, 4色定理 2005, Feit-Thompson 2012, CompCert)、Agda (2007)、**Lean (2014, mathlib)**、Idris (2011)
- **言語機能との対応**: Linear Logic (Girard 1987) ↔ **Linear Types/Rust 所有権**、Hindley-Milner ↔ 直観主義含意・全称断片、Effects/Modal Types ↔ Modal Logic

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
| 計算理論 | 3 |
| コンピュータアーキテクチャ | 2 |
| セキュリティ | 2 |
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
- **削除こそが最大の設計成果**: TLS 1.3 は追加した機能より削除した機能が重要。「柔軟性は脆弱性の母」——選択肢の存在が弱い選択を許す。制限・廃止・禁止が安全性・正確性・理解可能性を生む（Raft の状態空間削減、AEAD のみへの集約、ebpf の bounded loops と同型）
- **責任の再分配としてのトレードオフ明示**: 0-RTT の replay 非保証を RFC に明記して「idempotent 操作にのみ使え」とアプリに委ねる設計は、CAP/RUM の「何を犠牲にするかの明示」哲学と同型。「完全に守る」ではなく「何を守り何を守らないかを明示する」が成熟したプロトコル設計
- **段階的秘密鍵導出（キースケジュール）の耐障害性**: TLS 1.3 の Early/Handshake/Master Secret 連鎖は「片方の秘密が漏洩しても他方が守る」ハイブリッド強度設計。各段階に独立した情報源を混入し、一点の妥協が全体を壊さない — Reed-Solomon の冗長性、Raft のクォーラム、HLC の物理+論理ハイブリッドと同じ「多重保護」パターン

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
- **ECH（Encrypted Client Hello, RFC 9849）詳細**: SNI の暗号化、Outer/Inner ClientHello 二層構造、DNS HTTPS レコードでの公開鍵配布
- **QUIC + TLS 1.3 統合設計**: HTTP/3 では TLS 1.3 が QUIC に組み込まれ、0-RTT の replay 保護をトランスポート層が担う。TLS over TCP との設計差異
- **Post-Quantum TLS ハイブリッドモード**: X25519 + ML-KEM の組み合わせ鍵交換、Cloudflare/Google 2024-2025 展開、格子暗号と楕円曲線のハイブリッド強度保証の数学
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
