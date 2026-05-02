# DuckDB と組み込み OLAP 分析データベース — SQLite for Analytics の系譜
**日付**: 2026-05-03
**分野**: tech
**タグ**: #DuckDB #OLAP #vectorized-execution #embedded-database #DuckLake #MotherDuck

## 学んだこと

### 設計哲学 — CWI 系譜と「埋め込み OLAP」というニッチ
DuckDB は CWI (Centrum Wiskunde & Informatica) Database Architectures Group 発祥。Mark Raasveldt と Hannes Mühleisen が 2018–19 年に開始し、SIGMOD 2019 デモ論文と CIDR 2020 論文 "Data Management for Data Science — Towards Embedded Analytics" でその主張を展開した。CWI は MonetDB と Vectorwise (X100) を生んだ系譜であり、DuckDB はその直系の進化形である。

ポジショニングは "SQLite for analytics"。in-process でリンクし、サーバ不要、単一ファイル、ゼロ依存。SQLite が OLTP を組み込み化したことを、OLAP で実現した。問題空間は明確で、データサイエンティストが「中規模データ (数 GB〜100 GB)」を扱う際、Pandas はメモリで死に、Spark/ClickHouse は重すぎる、その谷間を埋める。

### Vectorized Execution Engine — Volcano と Materialize の中間
Volcano モデルの pull ベース反復子は維持しつつ、1 タプルではなく **固定サイズの Vector (DataChunk)** を渡す。`STANDARD_VECTOR_SIZE` は現在 **2048**。8 byte × 2048 = 16 KB で L1d キャッシュに収まる — これが命令キャッシュ局所性とデータキャッシュ局所性のスイートスポット。

設計選択の対比が美しい:
- 行ごと (Volcano クラシック): 関数呼び出しオーバーヘッドが支配的
- 全マテリアライズ (MonetDB クラシック): 中間結果が L1/L2 から溢れる
- Vector vol: 関数呼び出し償却 + キャッシュ局所性の両立

JIT (LLVM) を採用しないのは哲学的選択である。MonetDB/X100 (Boncz, Zukowski, Nes 2005) 以来の「interpreted vectorized でも JIT 並みの速度」という主張に立ち、コンパイル時にテンプレート特殊化された C++ カーネルで通す。**LLVM 依存をやめれば配布が劇的に楽になる** — 「組み込み」を本気でやるための制約駆動設計だ。

### ストレージとライトウェイト圧縮
単一ファイル `.duckdb`、固定サイズブロック (デフォルト 256 KB)、WAL も同居。Row Group (約 122,880 行) を並列スキャン単位に、その中で Column Segment に分割。各列セグメントは統計に基づき **RLE / FOR (Frame-Of-Reference) / Dictionary / Bitpacking / Gorilla / FSST / ALP** から自動選択する。

逆説的だが、この圧縮は **クエリ速度を上げる**。メモリ帯域がボトルネックの現代 CPU では、bitpacked 列を SIMD で展開しながらスキャンする方が、非圧縮列を読むより速い。圧縮は「CPU 税」ではなく「IO 税の減税」なのだ。

### MVCC を OLAP に最適化する発明
Neumann 2015 の HyPer "Fast Serializable MVCC for Main-Memory DBs" の variant を採用。だが OLAP ではデータが圧縮済みで in-place 更新ができない。DuckDB の発明は **2048 行のバッチ単位で「カラム別の bulk version 情報」を undo buffer に保持する** というもの。結果、100 列テーブルの全行更新で、HyPer 25 倍・PostgreSQL 116 倍遅くなるのに対し、DuckDB は **1 列更新と同じ 0.43 秒**で済む (公式ベンチ)。OLAP 典型の bulk update / MERGE に最適化された設計判断。

### Zero-copy "BYOData" と DuckLake
Arrow / Pandas / Polars / Parquet / CSV を直接クエリ可能 (`SELECT * FROM 'data.parquet'`)。Arrow とは constant-time 変換ができるレイアウト互換 (完全に同一ではない)。Pandas 2.0 以降 Arrow バックエンドが標準化されたことで、コピーなしの経路が完成した。

2025–2026 の重要動向は **DuckLake** だ。Iceberg のメタデータ JSON 木の Optimistic Concurrency 衝突問題を、**普通の RDBMS のトランザクションに委譲して解決**する。Iceberg のメタデータ JSON + Avro マニフェストの複雑性を回避し、メタデータを SQL DB (SQLite/Postgres/DuckDB) に格納、データは Parquet。Spark / Trino / DataFusion クライアントも登場し、2026-04 に v1.0 へ。

### 2024–2026 の主要リリース
- **1.0 (2024-06)**: ストレージ後方互換保証
- **1.2 (2025-02)**: Parquet Bloom filter pushdown、`allowed_directories` セキュリティ
- **1.4 LTS (2025-09)**: AES-256-GCM 暗号化、MERGE 文、Iceberg writes
- **1.5 (2026-03)**: Non-blocking checkpoint (TPC-H +17%)、VARIANT 型、GEOMETRY core 昇格、point cloud で 3x 圧縮、DuckLake v0.4 統合

VSS 拡張で HNSW ベクトル検索もサポート (vector similarity)。WebAssembly ビルド (duckdb-wasm) でブラウザ内 OLAP も成立する。

## 気づき・洞察

**1. JIT 不採用の哲学的意味** — 「速度のためなら何でもやる」の対極。配布容易性という外部制約を最優先し、内部実装で JIT 比 90% を叩き出す。**制約は設計を磨く**の典型例。

**2. Vector size 2048 = L1d キャッシュサイズという物理学** — ハードウェアの物理から最適な抽象化単位を逆算する。MESI キャッシュ整合性の知識 (前回学習) が、なぜ vector size を大きくしすぎてはいけないかの直感を支える。

**3. HyPer MVCC を「列バルク化」した発明** — 行単位 version chain という DB 業界の常識を捨て、2048 行ブロック単位に再設計。**制約 (圧縮ブロックを破壊できない) から発明が生まれる**。

**4. MotherDuck の "bridge" operator** — クエリプランの一部を local DuckDB、残りを cloud DuckDB で実行し、tuple stream の up/down 演算子で繋ぐ。**分散 DB の plan を 2 ノードに退化**させた合理的設計。BigQuery の ~400 ms 起動タックスを ms 級に削る。

**5. DuckLake は「Iceberg のメタデータ問題を RDBMS に委譲」** — 並行 writer の衝突を ACID トランザクションで解決するという、技術スタックの上位レイヤーで頑張りすぎていた問題を一段下に降ろす発想。**抽象化の階層を間違えない**設計判断。

**6. 圧縮 = 速度向上という逆説** — 帯域律速の世界観。これは MESI/メモリモデルの理解と直結し、「データ移動こそコスト」という現代 CPU の真理を内面化している。

**7. Single-node only が機能か制約か** — Jordan Tigani (MotherDuck CEO、元 BigQuery) "Big Data is Dead" 論。192 コア NVMe 機なら数 TB は単一ノードで十分。**分散しないという選択**が新規参入の障壁回避に。

**8. "Embedded analytics" は新カテゴリ** — Spark/ClickHouse vs Pandas の谷間。Polars (Rust + DataFrame API) と DuckDB (C++ + SQL) は同じ谷間に異なるアプローチで進入し、Apache DataFusion を含めた 3 者で 2026 年の "中規模 OLAP" 市場を形成。

## 他分野との接続

- **MVCC / Lamport 時計 (前日学習)**: HyPer serializable MVCC の単一ノード最適化と、Lamport 時計に基づく分散 version vector の対比。**スケール依存で最適解が分岐する**。
- **MESI キャッシュ整合性 (先週学習)**: vector size 2048 が L1d に収まる選択は、コア間 vector 共有を避けて MESI invalidation を最小化する設計判断と表裏一体。
- **Reed-Solomon / Bloom filter (既習)**: Parquet 1.2 の Bloom filter pushdown と既習の確率的データ構造が直結。zone map による行スキップは、erasure coding の MDS 性質と同様に「**部分情報で全体を判定**」の哲学。
- **Apache Iceberg (既習 2026-04-29)**: DuckLake は Iceberg のメタデータ問題への対案として読み解ける。同じテーブルフォーマット問題に異なる解。
- **Curry-Howard (既習)**: 圧縮形式での late materialization は「型情報を保持したまま計算」という型理論的発想に通じる — 値を decode せずに述語評価する。
- **オートリーズ (パン分野・本日学習)**: 「**仕事を時間に置換する**」という哲学が共通。混捏エネルギーを酵素 + 時間で置換するベイカーと、混捏 (=サーバ常駐) を組み込み + 圧縮で置換する DuckDB は、リソースのトレードオフ設計として同型。

## 次に深掘りしたいこと

- DuckLake v1.0 の SQL カタログ実装詳細 — PostgreSQL バックエンドでの並行 writer の隔離レベル設計
- MotherDuck の bridge operator の query plan partitioning ヒューリスティック
- Pianoteq / Modartt の物理モデリング DSP (本日 piano 分野で学んだ非線形フェルト) と DuckDB のテンプレート特殊化 C++ カーネルの「interpreted vs compiled」哲学比較

## 主要参考ソース

- [DuckDB CIDR 2020 paper](https://duckdb.org/pdf/CIDR2020-raasveldt-muehleisen-duckdb.pdf)
- [DuckDB SIGMOD 2019 demo](https://hannes.muehleisen.org/publications/SIGMOD2019-demo-duckdb.pdf)
- [Analytics-Optimized Concurrent Transactions](https://duckdb.org/2024/10/30/analytics-optimized-concurrent-transactions)
- [Lightweight Compression in DuckDB](https://duckdb.org/2022/10/28/lightweight-compression)
- [DuckDB Quacks Arrow](https://duckdb.org/2021/12/03/duck-arrow)
- [DuckDB 1.4.0 LTS](https://duckdb.org/2025/09/16/announcing-duckdb-140)
- [DuckDB 1.5.0](https://duckdb.org/2026/03/09/announcing-duckdb-150)
- [DuckLake v1.0](https://ducklake.select/2026/04/13/ducklake-10/)
- [MotherDuck research paper](https://motherduck.com/research/motherduck-duckdb-in-the-cloud-and-in-the-client/)
- [Neumann Fast Serializable MVCC (HyPer)](https://db.in.tum.de/~muehlbau/papers/mvcc.pdf)
