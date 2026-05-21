# Apache Iceberg とオープンテーブルフォーマット ― オブジェクトストレージにACIDをもたらす設計

**日付**: 2026-04-29
**分野**: tech
**タグ**: #DataLakehouse #Iceberg #ACID #Metadata #Snapshot

## 学んだこと

### Iceberg が解こうとした問題 ― Hive テーブルの限界
2010年代の「データレイク」の事実上のテーブル抽象は **Hive table** だった。Hive は HDFS/S3 上のディレクトリ構造そのものをテーブル定義とみなし、`/year=2024/month=01/day=15/` のようにディレクトリ階層がパーティションを表現する。これには深刻な弱点がある:

1. **アトミック性なし**: 複数ファイルを書き換える `INSERT OVERWRITE` で読み手は中間状態を見てしまう（"dirty read"）
2. **`LIST` の遅さ**: S3 では数十万のパーティションをリストするだけで分単位かかる
3. **パーティション漏れ**: ユーザがクエリで `WHERE event_date='2024-01-15'` と書かないとフルスキャンになる（暗黙のパーティションプルーニングが効かない）
4. **スキーマ進化の脆弱性**: カラム追加・削除でファイル順序の前提が崩れる

Iceberg は **Netflix** の Ryan Blue らが 2017 年に開発を始め、これらを「メタデータをファイルそのもので管理する」という発想で解いた。

### 三層メタデータツリー
Iceberg のテーブルは「カタログ → メタデータファイル → マニフェストリスト → マニフェストファイル → データファイル」という階層を成す:

- **Catalog**: テーブル名 → 最新のメタデータファイルへのポインタ。Hive Metastore, AWS Glue, Nessie, REST Catalog などが担う
- **Metadata file** (`v1.metadata.json`): スキーマ、パーティション仕様、ソートオーダー、過去スナップショット一覧
- **Manifest list** (`snap-*.avro`): 1スナップショット内に含まれる **manifest file** の一覧と、各 manifest が触るパーティション値の min/max
- **Manifest file** (`*.avro`): 個々のデータファイルへの参照と各カラムの **min/max・null数・row count** などの統計
- **Data files** (`*.parquet`): 実際の列指向データ

この階層により、クエリプランナは「カタログ → メタデータ → マニフェストリストの partition stats → マニフェストの column stats」と段階的にプルーニングし、**S3 LIST を一切呼ばずに必要なファイルだけ読む**。これが Hive 比で桁違いに速い理由である。

### スナップショットアイソレーションの実装
Iceberg の ACID は楽観的並行制御で実現される。書き込みは:
1. 現在のメタデータファイルを読む（baseline snapshot ID を確定）
2. 新しいデータファイルを書く
3. 新しいマニフェストとマニフェストリストを書く
4. 新しいメタデータファイル `vN+1.metadata.json` を書く
5. **カタログに対して "v1 → v1+1" の atomic CAS** を発行（HiveMetastore の場合は `ALTER TABLE` の旧/新ポインタ比較、REST catalog なら HTTP の commit エンドポイント）

CAS が失敗（誰かが先にコミットした）すれば、リトライまたはコンフリクト解決ロジック（行レベル削除なら多くの場合マージ可能）に進む。これは **Calvin/FoundationDB 系の楽観的トランザクション**と同じ設計思想で、ストレージ自体（S3）はトランザクションを知らないがカタログの単点が serialization point になっている。

### 隠しパーティショニング (Hidden Partitioning)
Hive では「`event_ts` を `event_date` という別カラムに変換してパーティションキーにする」のが常套手段だった。これは ETL を肥大化させ、ユーザがクエリで `event_date` を指定し忘れるとフルスキャンになる。

Iceberg は **partition transform** をスキーマの一部として宣言する: `PARTITIONED BY (days(event_ts))`。クエリで `WHERE event_ts > '2024-01-15'` と書くだけで、エンジンは透過的に `days(event_ts)` への変換を計算してパーティションプルーニングを効かせる。さらに `bucket(N, user_id)`, `truncate(L, name)` といった transform も同様に効く。これは **論理スキーマと物理レイアウトの完全な分離**で、後述のパーティション進化を可能にする。

### スキーマ進化とパーティション進化
- **Schema evolution**: カラム追加・削除・型拡張・順序変更が**データファイルを書き換えずに**可能。これは Parquet の field-id ベース（カラム名ではなく一意 ID で参照）で実現される
- **Partition spec evolution**: 「先月までは `days(ts)`、今月から `hours(ts)`」のように、過去データを書き換えずにパーティション戦略を変えられる。各データファイルはどの spec で書かれたかをマニフェストに保持する

### Time Travel と監査性
全スナップショット（メタデータの履歴）が保持されるため、`SELECT * FROM tbl AS OF '2024-01-15 12:00:00'` で過去状態を読める。これは MVCC のスーパーセットで、保持期間内なら**任意の過去時点に分析を再現できる**。GDPR の「忘れられる権利」とは衝突するため、`expire_snapshots` で物理削除する管理操作が用意されている。

### Iceberg vs Delta Lake vs Hudi
2026 年現在、3つの主要 OTF がある:
- **Iceberg** (Netflix → Apache): メタデータ JSON + Avro マニフェスト。ベンダー中立。Snowflake/BigQuery/Databricks すべてが対応
- **Delta Lake** (Databricks): JSON トランザクションログ。Databricks エコシステムが本拠地
- **Hudi** (Uber): タイムライン＋ファイルグループ。CDC・upsert に強み

2024-2025 年に Snowflake が Iceberg を一級市民として受け入れ、Databricks も Iceberg-Delta 相互運用 (UniForm) を発表したことで、**Iceberg が事実上の業界標準**へ収束した。

## 気づき・洞察

Iceberg の本質的な発明は「**メタデータをデータと同じオブジェクトストレージに置き、カタログは単なるポインタにする**」という分離である。これは Git の構造に酷似している:

| Git | Iceberg |
|---|---|
| commit (immutable) | snapshot (immutable) |
| tree (directory listing) | manifest list |
| blob (file content) | data file (Parquet) |
| HEAD (refs/heads/main) | catalog pointer |

Git も「コミット差分はオブジェクトストアにイミュータブル、ブランチポインタだけが mutable」だった。Iceberg はこれを peta-byte 規模の表データに適用したと言える。**OS の VFS や DB の MVCC で確立された "イミュータブル過去 + ポインタの atomic 更新" のパターンが、データウェアハウス層で再発見された**のだ。

もう一つの洞察は「**S3 という '弱い' ストレージの上に '強い' トランザクションを構築する**」アプローチである。S3 は eventually consistent だった時代もあったが、現在は read-after-write 一貫性を持つ。しかし依然「複数オブジェクトのアトミックな書き換え」はサポートしない。Iceberg は単一の **"カタログへのポインタ更新"** を直線化点 (linearization point) にすることで、その上に意味論的なトランザクションを構築している。これは **CAP 定理の制約を理解した上で、強い保証が必要な部分にだけ集中する**設計思想であり、分散システム工学の良い実例である。

## 他分野との接続

- **cs / MVCC** (2026-04-27): Iceberg のスナップショットは MVCC のバージョンチェーンと完全対応。スナップショット ID = 読み取りタイムスタンプ。`expire_snapshots` = vacuum
- **cs / LSM ツリー** (2026-04-21): どちらも「イミュータブルファイル + メタデータでバージョン管理」の発想。Iceberg のコンパクションは LSM の compaction と動機が同じ（小さなファイルが増えると読み性能が劣化する）
- **cs / Bloom Filter** (2026-04-28): Iceberg のマニフェストの column stats（min/max）は Bloom Filter と同じく「不要な読み込みを早期に除外する」確率的/統計的データ構造の系譜
- **tech / Event Sourcing** (2026-03-23): スナップショットの連鎖は event log と双対。Iceberg は「テーブルの全変更履歴を保持する」という意味で event-sourced と言える

## 次に深掘りしたいこと

- Iceberg の **REST Catalog spec** が Hive Metastore を置き換える流れと、それが分散カタログ（Polaris, Unity, Lakekeeper）にもたらす影響
- **Puffin file** と統計拡張（HyperLogLog でカーディナリティ統計、Bloom filter index など）
- Iceberg V3 spec で議論されている **行レベル削除のマージオンリード（merge-on-read）vs コピーオンライト（copy-on-write）のトレードオフ**

## 参考ソース

- [Apache Iceberg 公式仕様 (iceberg.apache.org/spec)](https://iceberg.apache.org/spec/) — Tier 1: 公式仕様
- [Apache Iceberg metadata explained (olake.io)](https://olake.io/blog/2025/10/03/iceberg-metadata/) — Tier 2: 専門ブログ
- [Snowflake Apache Iceberg tables documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg) — Tier 1: 公式ドキュメント
- [Databricks: What is Apache Iceberg](https://docs.databricks.com/aws/en/iceberg/) — Tier 1: 公式ドキュメント
