# Apache Arrow と列指向ゼロコピー・データ交換
**日付**: 2026-05-14
**分野**: tech
**タグ**: #ApacheArrow #ColumnarFormat #ZeroCopy #ADBC #DataFusion

## 学んだこと

### Apache Arrow の存在意義 ― 「シリアライゼーション税」の撤廃
**Apache Arrow** は 2016 年に Wes McKinney（pandas 作者）と Jacques Nadeau（Drill）らによって始まり、2026 年 2 月で誕生 10 周年を迎えた、**言語非依存・プロセス間共有可能な列指向インメモリ・フォーマット**である。Arrow の解決した問題はそれまでデータ処理スタックを蝕んできた **「シリアライゼーション税」** ――「Spark から pandas へデータを渡すだけで CPU の 80% が消える」という現象であった。原因は、各システムが独自のメモリレイアウト（Spark の InternalRow、pandas の Block Manager、Postgres の wire protocol）を持ち、境界を越えるたびに行→列、列→行の変換と直列化・逆直列化を繰り返していたこと。Arrow は **「共通の物理メモリレイアウト」** を仕様化することで、変換ゼロ・コピーゼロのプロセス間共有を可能にした。

### 物理レイアウト ― Validity Bitmap + Buffers + Children
Arrow の列は **(1) Validity Bitmap**（NULL マスクの 1 ビット/要素）、**(2) 値バッファ**（固定長型なら密な値配列、可変長型ならオフセット＋データ）、**(3) 子配列**（List/Struct のネスト構造）という単純な構造で表現される。すべてのバッファは **64-byte アライメント** で配置され、SIMD 命令（AVX2/AVX-512/NEON）が直接動作する。CPU キャッシュラインの境界とアロケータのアロケーションサイズ（typically 64-byte multiples）に合わせた設計で、「ハードウェアの都合に合わせた人工的な制約を仕様にする」発想は DuckDB の vector size 2048 と同じく **L1d/L1i 局所性駆動の設計**。

### IPC とゼロコピー共有 ― Flatbuffers が鍵
Arrow IPC (Inter-Process Communication) フォーマットは **Flatbuffers** でメタデータをエンコードする。Protocol Buffers が「シリアライズ・デシリアライズが必要」なのに対し、Flatbuffers は **「ヘッダから直接ポインタ参照」** できるためメタデータ自体のパースコストもゼロ。実データ部はそのまま mmap でき、複数プロセスが **同じ物理メモリページ** を参照する。これにより Pandas → DuckDB、Polars → DataFusion、PySpark → Ray という言語境界・プロセス境界のデータ受け渡しが「ポインタの貸し借り」になる。**`pyarrow.Table` から `polars.from_arrow()` が μ 秒で済むのはコピーが発生しないから**。

### ADBC (Arrow Database Connectivity) ― JDBC/ODBC の現代版
**ADBC** は 2023 年に登場、2026 年現在 PostgreSQL/Snowflake/BigQuery/DuckDB/SQLite が公式実装を提供する **「列志向ネイティブ」のデータベース接続規格**。従来の JDBC/ODBC は「行単位フェッチ → ドライバ層で列変換 → アプリで列→列変換」という三重変換を強いていた。ADBC では DB サーバが **Arrow RecordBatch ストリームを直接返す**ため、サーバ・ドライバ・アプリの全層で同一のメモリレイアウト。Snowflake の社内ベンチマークで「100M 行の SELECT で **JDBC 比 8 倍**、ピーク CPU は 1/4」が確認されている。BigQuery Storage Read API、Databricks SQL Statement Execution API、ClickHouse Native Protocol も Arrow Flight を内部採用。

### Arrow Flight と Flight SQL ― gRPC 上の高速転送層
**Arrow Flight** は gRPC 上に作られた Arrow 専用の RPC 層で、HTTP/2 のマルチストリームを使って **複数 RecordBatch を並列転送**する。`Flight SQL` は Flight 上の SQL クライアントプロトコルで、Dremio/InfluxDB/Trino が採用。**TLS 1.3 + Arrow + gRPC** で「セキュアな PB 級データ転送」を 10 GbE のワイヤーレートに迫る速度で実現する。Hadoop の HiveServer2 (Thrift over TCP, 行指向) との性能比較で 5-20 倍の差。

### Apache DataFusion ― Rust 製組み込みクエリエンジン
**DataFusion** は元々 Arrow のサブプロジェクトだったが 2024 年に Apache トップレベルプロジェクトに昇格。Rust 製の **「組み込み可能・モジュラー・列指向クエリエンジン」** で、論理プラン→物理プラン→ベクトル化実行のパイプライン全体が **Arrow RecordBatch を入出力**として共有する。Polars、Comet（Spark の DataFusion 置換）、Ballista（分散実行）、InfluxDB 3.0、Cube.js、Greptime DB が DataFusion を内部エンジンに採用。**「クエリ最適化器とベクトル化実行を独立コンポーネント化」** することで、SQL 方言や分散レイヤだけを差し替えれば新しい OLAP を作れる。**SIGMOD 2024 論文** で発表され、Velox（Meta）と双璧をなす次世代エンジン。

### Arrow Compute と UDF Stability
Arrow Compute は Arrow 上で動く C++/Rust 製の関数ライブラリ（hash、cast、aggregate、filter）。重要なのは **「カーネルが言語境界を越えて再利用される」** こと。pandas が「dtype を Arrow に統一」する Pandas 2.0 (2023) 以降、`pyarrow.compute` の関数を Python から呼ぶと **C++ 実装が直接ベクトル化実行**される。Polars の `Expr` も裏で Arrow Compute を呼ぶ。「**Numpy が pandas/scikit-learn の共通基盤になったように、Arrow Compute は次世代の数値計算共通基盤**」になる予兆。

### 2026 のフロンティア ― Lakehouse の共通言語
2026 年現在、Arrow は **Iceberg/Delta/Hudi の Lakehouse スタック共通の中間層**として確立した。Parquet → Arrow → DataFusion/Polars/DuckDB → Arrow → クライアントというパイプラインで、**Parquet の列指向ファイルフォーマットと Arrow の列指向メモリフォーマット**が双子の役割を果たす。Iceberg 1.6 (2026 Q1) で **Arrow-based vectorized reader** がデフォルト化、Delta-rs (Rust 実装) は Arrow ネイティブ。ClickHouse はネイティブフォーマットを保ちつつ Arrow をエクスポート層で採用。**「列指向ストレージと列指向計算の歴史的統合」** が完了しつつある。

## 気づき・洞察

- **「データを動かす vs 動かさない」哲学の双子**——Arrow（共通フォーマットで効率的に動かす）と Iceberg/Delta（動かさず on-disk のままクエリする）は逆ベクトルだが同じ目標（シリアライゼーション削減）に到達する。プロセス境界を越える瞬間だけ Arrow に変換し、それ以外は元のストレージで持つというハイブリッドが現代の標準
- **「仕様の最小化」が普及を生む**——Arrow は「メモリレイアウトだけ」を仕様化し、計算・転送・接続・ストレージは別プロジェクト（Compute/Flight/ADBC/Parquet）に分離した。HTTP が「テキストプロトコル」だけを仕様化し REST/GraphQL/SSE/WebSocket を許したのと同じ。**仕様が小さいほど採用が広がる**
- **共通フォーマットの政治学**——Arrow 普及の最大の障壁は技術ではなく「自社専用フォーマット」への執着だった。Spark の InternalRow、Snowflake のクローズドな型、各社独自のドライバ。2024-2026 にこれらが Arrow に降伏したのは「ベンダーロックインのコストが顧客から見えるようになったから」。**オープン標準は経済的圧力で勝つ**
- **GPU/CUDA との接続点**——cuDF（NVIDIA RAPIDS）は Arrow をネイティブ・データモデルとし、GPU ↔ CPU 間の memcpy も Arrow フォーマットで行う。**ホスト・デバイス・分散ノード・別プロセス・別言語のすべての境界で同じレイアウト**を使う ―― これは「CRDT が編集の境界を越える」「MCP が AI とツールの境界を越える」のと同型の **「境界を越えるための共通インターフェース」哲学**
- **「ゼロコピー」は実は「相対コピー削減」**——厳密には NUMA 越え・GPU 越えでは物理コピーが発生する。Arrow が言う zero-copy は「**論理的に同じバッファを複数主体が参照できる**」こと。仮想メモリページの mmap、PCIe DMA、RDMA がそれぞれの境界で物理的最適化を担う

## 他分野との接続

- **cs (列指向ストレージ vs 行指向, B+ tree vs LSM)**: Arrow の列指向は OLAP の典型解だが、行ごとの更新が必要な OLTP では行指向が依然有利。**ワークロード特性が物理レイアウトを決定する**普遍法則
- **piano (内的聴感)**: ピアニストが楽譜を見ながら頭の中で音を鳴らすとき、視覚情報と聴覚情報を「変換」しているのではなく **「同じ音楽イメージの異なる表現を並行参照」** している。Arrow の zero-copy も同じく「変換しない、参照する」
- **bread (クラスト形成)**: パンの内部（クラム）と表面（クラスト）が「同じ生地」の異なる物理状態であるように、Arrow のデータも「同じバイト列」の異なる解釈（int32 配列か float32 配列か）として読まれる。**物理は一つ、論理は多様**
- **golf (傾斜地ライ)**: 「同じスイング」が地形によって違うボールフライトを生む ―― Arrow の同じバッファが異なる言語・プロセスで違うインターフェースに見えるのと同型。**変換ではなく適応**

## 次に深掘りしたいこと

- Arrow Flight RPC v2 と HTTP/3 統合の最新状況（QUIC マルチストリームを利用した Flight SQL 改良案）
- Arrow IPC v3 提案（FlatBuffers 廃止と Protobuf 復帰の論争）
- Velox（Meta）と DataFusion の設計判断の違い ―― Vectorized iterator vs Pull-based push 化
- Substrait（クロスエンジン論理プラン IR）との関係：DataFusion が Substrait をデフォルト IR にする日

---

## 参考ソース
- [Apache Arrow 公式 GitHub](https://github.com/apache/arrow) (Tier 1: 公式)
- [Apache Arrow is 10 years old (公式ブログ 2026-02)](https://arrow.apache.org/blog/2026/02/12/arrow-anniversary/) (Tier 1)
- [Arrow Columnar Format 仕様](https://arrow.apache.org/docs/format/Columnar.html) (Tier 1: 公式仕様)
- [Apache DataFusion: A Fast, Embeddable, Modular Analytic Query Engine (SIGMOD 2024)](https://dl.acm.org/doi/pdf/10.1145/3626246.3653368) (Tier 1: 査読論文)
- [Apache DataFusion 公式ドキュメント](https://datafusion.apache.org/) (Tier 1)
