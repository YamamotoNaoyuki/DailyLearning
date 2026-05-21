# 分散システム一貫性モデル階層 — Linearizability vs Serializability vs Causal vs Eventual
**日付**: 2026-05-03
**分野**: cs
**タグ**: #分散システム #一貫性モデル #linearizability #serializability #causal-consistency #Jepsen #PACELC

## 学んだこと

### 整理: 直交する 4 軸
一貫性モデルが乱立して見えるのは、複数の独立軸を一次元の「強さ」に潰そうとするからだ。本質的な軸は次の 4 つ:

- **(a) 対象の粒度**: 単一オブジェクト (register/queue) か、複数オブジェクトに跨る transaction か。Linearizability は前者、Serializability は後者の語彙。
- **(b) 全観測者で同じ全順序を見るか** (single total order)。Sequential Consistency / Linearizability は YES。Causal は NO (concurrent な操作は順序自由)。
- **(c) Real-time order との整合**。物理時刻で T1 が完了してから T2 が開始したら、その順序を尊重するか。Linearizability/Strict Serializability は YES。Sequential/Serializable は NO。
- **(d) 因果関係の保護**。happens-before を尊重するか。Causal 以上が YES、Eventual は NO。

この 4 軸を独立に扱うと、Viotti & Vukolić (2016, ACM Comput. Surv.) が形式化した 42+ モデルの partial order が「自然」に見えてくる。

### Linearizability (Herlihy-Wing 1990) — Compositional の鋭利さ
Linearizability の真に重要な性質は **compositionality** (locality) である: オブジェクト A と B がそれぞれ linearizable なら、A∪B も linearizable。これが Sequential Consistency にはない。

MESI cache coherence (既習) は linearizable per cache line だが、複数行に跨る整合性は別物 — x86 の memory model が TSO で SC より弱い理由はここに通じる。Compositionality は分散モジュラ設計の根拠で、etcd や ZooKeeper が「単一 linearizable ストアの組み合わせ」で複雑なロジックを構築できるのはこのため。

### Sequential Consistency vs Linearizability — Attiya-Welch 下界
Attiya-Welch (1994, ACM TOCS) は「shifting」技法で、**clock skew が u の環境で linearizable read/write は最低 u/4 の遅延**が必要なことを示した (read u/4, write u/2)。一方 Sequential Consistency は read か write の片方を local 完了できる。

この差が「LinkedList を直線的に並べる代償」で、広域分散で linearizable がコスト高になる理論的根拠。Spanner は GPS+atomic clock で u を ~7 ms に圧縮し、commit-wait で吸収する。

### Strict Serializability = Linearizability ∘ Serializability
**Spanner の "external consistency"** は名前が違うだけで Strict Serializability と等価 (Google Cloud blog で公式に確認)。Spanner / FoundationDB / CockroachDB / FaunaDB が共通して目標とする最強レベル。

CockroachDB は厳密には "serializable + per-key linearizable" で、**Stale read を許す代わりに causal reverse time travel を回避**する独自設計。

### ANSI レベルは「終わった」
Read Uncommitted/Committed/Repeatable Read は 1992 年の ANSI 仕様だが、Berenson et al. 1995 が「実装言語に過ぎず、anomaly 列挙が抜けがある」と批判して以降、研究文脈ではほぼ役割を終えた。

**Snapshot Isolation (SI)** が事実上 Repeatable Read の置き換えとなり、**Cahill 2008 SSI** で Write Skew を抑えた Serializable に到達 (PostgreSQL 9.1 が初の本番実装)。SSI の鍵は cycle 検出ではなく **rw-antidependency の "dangerous structure"** を局所判定する点。

### Causal+ — Eventual と Strong の中間「本命」
COPS (Lloyd 2011, SOSP) は **Causal+ = Causal Consistency + convergent conflict handling** を定義。後者は merge function (associative + commutative + idempotent) で全 replica が同じ収束値に至ることを要求 — **CRDT の semilattice 構造そのもの**。

Eiger は COPS を column-family 化、AntidoteDB は CRDT を first-class にした「Causal+ CRDT store」。**Cosmos DB の Session/Consistent Prefix レベル**は Causal の実用近似と読み解ける。

### PACELC (Abadi 2010/2012) と HAT (Bailis 2014)
**PACELC** は CAP の盲点である「partition がない平常時の latency-consistency tradeoff」を明示。**Cassandra/Riak/Cosmos = PA/EL**、**Spanner/VoltDB = PC/EC**。

Bailis の **HAT (VLDB 2014)** はさらに踏み込み、「partition 下でも available なまま実装可能な isolation level」を分類: Read Committed / Monotonic Atomic View / Read Your Writes は HAT 可能、**Snapshot Isolation / Serializability は HAT 不可** (証明)。これが「CAP の C は何のことか」議論を厳密化した。

### RAMP — atomic visibility だけを安く買う
RAMP transactions (Bailis SIGMOD 2014) は「multi-partition の atomic visibility」だけを isolation 全体ではなく単独で提供。RAMP-Fast は read 1RTT、write 2RTT、metadata は writes に linear。**synchronization independence + partition independence** という二条件で線形スケール。

「全部入りトランザクションは要らない、見え方だけ揃えたい」secondary index/materialized view の典型用途。

### Jepsen の最新成果 (2025)
Kyle Kingsbury の Jepsen は 2013 年以降、各 DB ベンダーの主張と実測の乖離を暴き続けている。検証エンジンは 2 系統: **Knossos** (linearizability 検証、SAT-based、O(2^n) 概算)、**Elle** (transactional cycle 検出、O(n) 級、VLDB 2020)。

2025 年の主要 finding:

- **Amazon RDS for PostgreSQL 17.4** (2025-04-29): Repeatable Read で **Long Fork anomaly** を発見。原因は primary が in-memory lock 順、secondary が WAL 順で transaction を visible にする不一致。RDS 固有でなくコミュニティ PostgreSQL にも存在。
- **TigerBeetle 0.16.11–0.16.45**: 金融 OLTP として Strong Serializability を主張 → process pause/network partition/clock skew/disk corruption/upgrade を経ても保持を確認。Safety issue は 2 件のみ。
- **Bufstream 0.1.0** (Kafka 互換): healthy cluster で acknowledged write loss、3 safety + 2 liveness issue。Kafka 自身の transaction protocol にも write loss / aborted read / torn transaction を発見。
- **NATS 2.12.1**: 単一 kernel crash + partition で acknowledged message loss (default fsync 2 分間隔が原因)。

## 気づき・洞察

**1. 「強さ」は一次元ではない** — Linearizability と Serializability は直交する別語彙の合成 (= Strict Serializable) で初めて両軸を捉える。**混同が業界標準であること自体が問題**。

**2. Compositionality こそ Linearizability の真価** — SC との見かけ上の小差が分散モジュラ設計の根拠。Lamport 時計 (前日学習) は SC 実現には十分だが Linearizability には不十分という対応関係。

**3. MESI / x86 TSO の memory model は局所的に Linearizable だが、組み合わせると SC ですらない** (store buffer)。これは DB の SI と SSI の差と同型: **局所一貫性と global serializability は別物**。

**4. Causal+ がスイートスポット** — HAT 可能 (network partition で available) でありながら、開発者の直感 (Read Your Writes / 因果順序) を壊さない。Eventual は debug 不能、Strong は latency 不能。**現実的な妥協点**。

**5. CRDT の semilattice = Causal+ の convergent conflict handling** — Curry-Howard と同様、**順序代数構造 ≅ 一貫性証明**という同型。数学が分散安全性に直結する。

**6. PACELC は CAP より実用的** — partition は稀、平常時の L vs C tradeoff が運用コストの本体。CAP の C/A 二択論は理論的に正しいが運用判断の誤誘導。

**7. Jepsen が暴き続ける gap** — ベンダー主張と実測の不一致は文化的問題でなく、**形式モデルが論文では証明されても実装では崩れる** (concurrency bug, clock skew, fsync policy)。Elle/Knossos のような外部検証は Property-Based Testing の分散版で、形式手法と相補的。

**8. 「役割を終えた」isolation level がいまだ default** — Read Uncommitted/Committed が多くの DB で default である経済的事実。Serializability の coordination cost を払えないアプリの方が多数派、という産業的現実。

## 他分野との接続

- **Lamport 時計 (前日学習)**: happens-before の形式化が Causal Consistency の前提。Logical clock は Sequential Consistency 実装の最小道具。
- **MVCC (前日学習)**: SI の実装基盤。SSI は MVCC 上に rw-antidependency 検出を載せた拡張。
- **MESI (先週学習)**: cache coherence は線形オブジェクトの linearizability、x86 memory model は SC より弱い (TSO)。**DB 文脈と語彙が異なるだけで同じ問題**。
- **Raft / CAP (既習)**: Raft = linearizable log = CP system。Strict Serializable は Raft + transaction layer (CockroachDB) で実装。
- **CRDT (既習)**: SEC ⊂ Causal+。Antidote が両者の合流点。
- **Curry-Howard (既習)**: 順序代数 (semilattice) と一貫性証明の同型は、論理-計算-代数 の三位一体の分散版。
- **DuckDB (本日 tech)**: HyPer MVCC を OLAP 化した「列バルク version」は、Serializable と SI の境界を OLAP context で再設計した発明。
- **ゴルフルール改正 (本日 golf)**: 「**TV evidence の causality**」と「プレーヤー認識の causality」の不整合は分散システムの clock skew 問題と同型 — Linearizability vs naked-eye standard。
- **シューベルト Der Leiermann (本日 music)**: 無限ループするドローン ↔ プログラムの **fixed-point / 不動点**。Causal+ や CRDT の semilattice 収束も「閉じない解決」を扱う。

## 次に深掘りしたいこと

- Cahill 2008 SSI の実装詳細 — PostgreSQL 9.1 がいかにして performance regression なく Serializable を提供したか
- COPS の dependency tracking の実用 overhead と Eiger/Antidote の改良
- Spanner Atomic Multi-Region Writes の commit wait latency 設計
- Jepsen Elle の cycle detection アルゴリズム — Knossos より polynomial に落ちた数学

## 主要参考ソース

- [Herlihy & Wing, "Linearizability: A Correctness Condition for Concurrent Objects" (TOPLAS 1990)](https://cs.brown.edu/~mph/HerlihyW90/p463-herlihy.pdf)
- [Lamport, "How to Make a Multiprocessor Computer That Correctly Executes Multiprocess Programs" (IEEE TC 1979)](https://lamport.azurewebsites.net/pubs/multi.pdf)
- [Attiya & Welch, "Sequential Consistency versus Linearizability" (TOCS 1994)](https://groups.csail.mit.edu/tds/papers/Attiya/SPAA91.pdf)
- [Lloyd et al., "Don't Settle for Eventual" COPS (SOSP 2011)](https://pdos.csail.mit.edu/6.824/papers/cops.pdf)
- [Bailis et al., "Highly Available Transactions" (VLDB 2014)](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf)
- [Bailis et al., "Scalable Atomic Visibility with RAMP Transactions" (SIGMOD 2014)](http://www.bailis.org/papers/ramp-sigmod2014.pdf)
- [Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design" (IEEE Computer 2012)](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)
- [Viotti & Vukolić, "Consistency in Non-Transactional Distributed Storage Systems" (ACM CSUR 2016)](https://arxiv.org/abs/1512.00168)
- [Jepsen Analyses](https://jepsen.io/analyses)
- [Jepsen Amazon RDS for PostgreSQL 17.4 (2025)](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4)
- [Jepsen TigerBeetle 0.16.11](https://jepsen.io/analyses/tigerbeetle-0.16.11)
- [Kingsbury & Alvaro, "Elle" (VLDB 2020)](https://people.ucsc.edu/~palvaro/elle_vldb21.pdf)
- [Google Cloud, "Strict Serializability and External Consistency in Spanner"](https://cloud.google.com/blog/products/databases/strict-serializability-and-external-consistency-in-spanner)
- [CockroachDB, "Living Without Atomic Clocks"](https://www.cockroachlabs.com/blog/consistency-model/)
