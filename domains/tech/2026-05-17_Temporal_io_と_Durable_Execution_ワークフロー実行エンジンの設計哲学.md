# Temporal.io と Durable Execution — クラッシュしても続く「永続実行」の設計哲学
**日付**: 2026-05-17
**分野**: tech
**タグ**: #DurableExecution #Temporal #Workflow #分散システム #信頼性工学

## 学んだこと

### 「Durable Execution（永続実行）」とは何か

Temporal.io は Uber 出身の Maxim Fateev と Samar Abbas が AWS Simple Workflow と Uber 内部の Cadence を進化させて 2019 年にオープンソース化した **ワークフロー実行プラットフォーム**。コア概念は **Durable Execution** — プログラムの実行状態（変数の値、関数呼び出し位置、待機中のタイマー）がプロセス境界を超えて自動的に永続化され、**ワーカーが落ちても、データセンターが停電しても、数時間後・数日後に同じ実行状態から「次の一行」が再開される**。

通常のプログラム実行モデルでは、プロセスが落ちれば実行コンテキスト（コールスタック、ローカル変数、I/O 待機状態）はすべて失われる。Durable Execution はこれを **「実行履歴を Event Sourcing 風に永続化し、再生(replay)することで状態を復元する」** という方法で覆す。プログラマは普通の関数を書いているように見えるが、その実行は「イベントログに追記される一連の決定」として記録される。

### Event Sourcing + Replay によるメモリ復元

Temporal の中核機構は **「ワークフロー実行 = 決定論的関数 + Event History」** という等式。ワークフローコード（Go/Java/Python/TypeScript で書ける）は次のような構造を持つ：

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order: Order) -> Result:
        await workflow.execute_activity(charge_card, order.payment)
        await workflow.sleep(timedelta(hours=24))  # 24時間スリープ
        await workflow.execute_activity(ship_order, order.items)
```

この `sleep(24h)` は通常のプロセスでは不可能 — ワーカーは 24 時間生き続けないかもしれない。Temporal はこれを次のように解決する：

1. ワーカーが `workflow.sleep(24h)` を呼ぶと、これは **「Timer Started」イベント** として Temporal Service の永続ストレージ（Cassandra、PostgreSQL、MySQL）に書き込まれる
2. ワーカーは即座にワークフロー実行を **suspend** し、メモリを解放する
3. 24 時間後、Temporal Service がタイマー満了を検知し、いずれかのワーカー（同じワーカーである必要はない）に「再開」を指示する
4. 再開ワーカーは Event History を頭から **replay** し、`sleep` までのすべての状態を再構築する
5. `sleep` 完了の所まで来たら、新しいコードを実行する

このアーキテクチャの肝は **「コードは決定論的でなければならない」** という制約。replay 時に同じ条件で同じ動作をしないと、状態が不整合になる。だから `time.now()`、`random()`、外部 API 呼び出しは **Activities**（後述）として隔離される。

### Workflow と Activity の分離 — 純粋関数と副作用の境界

Temporal の最重要な抽象は **Workflow** と **Activity** の分離：

- **Workflow**: 決定論的・冪等的・長時間実行可能。ビジネスロジックの「オーケストレーション」を担う。外部 I/O はできない。`time.now()` でなく `workflow.now()` を使う（これは Event History から再生される）
- **Activity**: 非決定論的・副作用を持つ。実際の I/O（API 呼び出し、DB アクセス、ファイル操作）はすべて Activity 内で行う。失敗したら **at-least-once セマンティクス** で再試行される

この分離は **関数型プログラミングの「純粋関数と副作用の分離」** とほぼ同型 — Haskell の IO モナドが副作用を型で隔離するように、Temporal は「決定論コード」と「副作用コード」をランタイム機構で隔離する。

Activity が冪等であることはユーザー責任。Temporal は「Activity が完了した」を Event History に記録するため、replay 時に同じ Activity は再実行されない（completed イベントから結果を取り出すだけ）。

### History Replay と Versioning の難問

Durable Execution の最大の落とし穴は **「コードを変更したら過去のワークフローはどうなるか？」**。1 ヶ月前に開始したワークフローが今日のコードで replay されたら、コードフローが変わって Event History と食い違うかもしれない。これを **non-determinism error** と呼ぶ。

Temporal は **GetVersion API**（Java/Go）または **patched()**（Python）で対応：

```python
v = workflow.patched("add-fraud-check")
if v:
    await workflow.execute_activity(check_fraud, order)
await workflow.execute_activity(charge_card, order.payment)
```

旧コードで開始した実行は `patched()` を `False` として記録（実は記録もしない）、新コードで開始した実行は `True` として記録。これで履歴整合性が保たれる。

これは **データベースのスキーママイグレーション** と同じ難問。実行中のフローの上で論理を変えるのは、走っているプロセスの DNA を書き換えるようなもの。

### Signal / Query / Update — 外部からのインタラクション

長時間実行ワークフローは外部から干渉される必要がある：

- **Signal**: 非同期のメッセージ送信。ワークフローは `workflow.wait_condition()` でシグナル待機できる。例：「人間の承認を 7 日待つ」フロー
- **Query**: 同期の状態問い合わせ。ワークフローの現在状態を読み取る（副作用なし）
- **Update** (2024 年追加): 同期だが状態を変更できる。Signal + Query を一つに統合

Signal は **Erlang/OTP のメッセージパッシング** の影響が見える。アクターモデルの「個別のアクターが mailbox を持つ」構造を、Durable Execution に統合した形。

### Architectural Components

Temporal Cluster は次のコンポーネントから成る：

1. **Frontend Service**: gRPC API を提供。クライアントとワーカーの入口
2. **History Service**: ワークフロー実行履歴を管理。シャーディングされる（デフォルト 4096 shards）。状態機械のコア
3. **Matching Service**: タスクキューを管理。ワーカーへの仕事の配信
4. **Worker Service**: 内部用ワーカー（タイマー処理、子ワークフロー管理など）
5. **Persistence Layer**: Cassandra / PostgreSQL / MySQL のいずれか。History の永続化
6. **Visibility Store**: Elasticsearch（v1.20 以降は SQL ベースも可）。検索・ダッシュボード用

History Service のシャーディングは **「ワークフロー ID をハッシュして 4096 個のシャードに割り当てる」** 方式。各シャードは単一スレッドで状態機械を進めるため、**シャード内の順序保証は厳密だが、シャード間は並行**。これは Kafka のパーティション戦略と同じ哲学。

### Performance と Limits

Temporal は速くない — 1 つの Workflow Execution の **更新スループットは 1 秒間に 50-100 回程度**（History Service の書き込みボトルネック）。だから「秒間百万トランザクション」用途ではない。代わりに **「数十万〜数百万の並行ワークフロー、各々が秒〜日単位で進行」** という用途に最適化されている。

- 最大 Workflow Execution 数: シャード分割で水平スケール可能、実績で **数億の同時実行**
- 1 ワークフロー実行の Event History 上限: デフォルト 51,200 events または 50MB。これを超えると `ContinueAsNew` で新しい実行に引き継ぐ
- ペイロードサイズ: デフォルト 2MB（Signal/Activity 引数）

### 競合と類似技術

Durable Execution カテゴリには複数の実装がある：

- **Temporal.io**: オープンソース、自己ホスト or Temporal Cloud。最も成熟
- **Cadence** (Uber): Temporal の祖。Uber が現在も内部利用
- **AWS Step Functions**: マネージドの State Machine ベース。Amazon States Language(JSON) で記述。コード性は低い
- **Azure Durable Functions**: .NET 中心。同様の Event Sourcing 構造
- **Restate**: 2024 年登場の新世代。よりシンプルな API、組み込み可能なシングルバイナリ
- **DBOS**: 2024 年の研究プロジェクト。PostgreSQL 上に Durable Execution を構築

### Use Cases

Temporal が向く問題：

- **金融取引のオーケストレーション**（Coinbase、Stripe、HSBC が利用）
- **SaaS のオンボーディング・ライフサイクル管理**（Snap、Box）
- **AI/ML パイプライン**（OpenAI、Replit）— 長時間学習ジョブ、推論パイプライン
- **マイクロサービス間のサーガパターン**（Distributed Saga）
- **人間ワークフローの絡む承認プロセス**（Description workflows、retry on human input）

## 気づき・洞察

### 「コードと状態の二項対立を解消する」革新

伝統的なプログラミングは **「コード(stateless) + データベース(stateful)」** の二項構造。コードはサーバープロセスに、状態は DB に住む。プロセス再起動でコードの実行コンテキストは捨てられ、DB だけが残る。

Temporal は **「コードの実行コンテキストそのものを永続化する」** ことで、この二項対立を消す。プログラマは「データベースに状態を保存」「アプリ起動時に状態を復元」というコードを書かなくていい — Temporal が自動でやる。**「実行が永続化される」というプリミティブを持つことで、システム設計が劇的に簡単になる**。

これは [[tech/Apache_Arrowと列指向ゼロコピー・データ交換]] が「データ表現の標準化で I/O コストを消す」のと同型 — **抽象レベルを一段上げることで、それまで本質と思われていた作業（シリアライゼーション/状態管理）が消える**。

### Event Sourcing の本質的勝利

Event Sourcing は 2010 年代初頭から「状態の変化をすべてイベントログに記録し、状態は導出物として再構築する」というパラダイムを提案してきた（[[tech/イベントソーシングとCQRS]]）。しかし当時の実装は複雑で、CRUD アプリには過剰だった。

Temporal の革新は **「Event Sourcing をプログラマから隠蔽し、普通のコードに見せる」** こと。プログラマは `await workflow.execute_activity()` という普通の `await` を書くだけで、舞台裏では Event History が育っている。**抽象化の質は、利用者がそれを意識しなくていい度合いで測られる**。

### Determinism という制約が自由を生む

「ワークフローは決定論的でなければならない」という強い制約が、replay 可能性・debug 可能性・履歴のリッチさをすべて生む。**制約がない自由は弱い自由** — Temporal の「決定論コード」と「副作用 Activity」の二段階分離が、結果として「クラッシュしても続く実行」という強い保証を可能にする。

これは [[cs/TLA_plus_と形式手法_分散システム仕様検証]] の **「曖昧さを除く制約が表現力を生む」** と同じ哲学。形式手法と Durable Execution は **「設計を厳密化する」** という同じ方向の二つの手段。

### 「待つこと」が一級市民になる

Temporal の最大の認識転換は **「`sleep(7 days)` が普通の演算になる」** こと。伝統的システムでは「7 日後に何かする」は cron や別の job queue で実装し、状態管理が複雑だった。Temporal では `await workflow.sleep(timedelta(days=7))` という一行。

これは **「時間軸方向のスケール」** を取り戻すパラダイム。マイクロサービス時代に失われた「業務プロセスの長期視点」を、コードで自然に表現できる。

## 他分野との接続

### FoundationDB の DST との対比 — 信頼性工学の二つの極

[[tech/FoundationDBと決定論的シミュレーションテスト]] の DST は **「テスト時に決定論を強制する」** 手法。Temporal は **「本番実行時に決定論を強制する」** 手法。両者とも「決定論こそがシステムを御す」哲学を共有するが、適用フェーズが対称的。

DST はバグを見つけるための決定論、Durable Execution は実行を再開するための決定論。**同じ原理が異なる目的で使われる**。

### Music の作曲技法との接続 — 動機の変奏と replay

ワークフローの replay は、音楽における **テーマと変奏** に似ている。**「同じ主題を別の文脈で再生する」** という構造。[[music/ブラームス交響曲第4番とパッサカリアの建築]] のパッサカリアは「8 小節の主題を 30 回変奏する」形式 — 同じ素材が反復され、毎回違う展開が乗る。

Temporal の Event History も「同じ事象が時を経て再生される」構造 — 過去の決定（Event）が現在の状態を構成する。**過去と現在の関係性そのものが音楽形式とプログラムの両方で本質的**。

### Bread の長時間発酵との接続 — 「待つ時間」を制御する技術

パン作りの長時間冷蔵発酵（[[bread/長時間冷蔵発酵リターディングの科学と風味形成]]）は **「24-72 時間という長時間の生物プロセスを管理する技術」**。Temporal も同様に **「数時間〜数ヶ月の長時間プロセスを管理する技術」**。

両者とも **「時間が素材を変える」** ことを利用する。パンの場合は乳酸菌活動と酵素分解が、Temporal の場合は外部世界の変化（承認、支払い完了、状態遷移）が、待ち時間の中で進行する。

### 解剖学の固有受容覚との接続 — 内部モデルの維持

[[anatomy/固有受容覚と筋紡錘]] が伝える「身体の内部状態」は、脳が運動を計画するための **内部モデル** を支える。Temporal の Event History も **「システムの内部状態を保持する」** 構造。

身体の内部モデルは脳の小脳・基底核に分散して保存される。Temporal の状態は History Service にシャーディングされて保存される。**「分散して保存される内部モデルが、全体としての一貫性を保つ」** という共通構造。

## 次に深掘りしたいこと

- Temporal の Sticky Execution（同じワーカーで replay を続ける最適化）の内部実装
- History Service のシャード・リバランス時の整合性保証メカニズム
- Continue-As-New パターンと「無限ワークフロー」の設計
- Temporal vs DBOS の比較 — PostgreSQL に Durable Execution を組み込む新世代設計
- Restate のシングルバイナリ設計と Temporal の Cluster 設計のトレードオフ
- Workflow Versioning の `GetVersion` パターンの限界と「並行バージョン運用」のベストプラクティス

## 主要参考ソース

- Temporal 公式ドキュメント (docs.temporal.io)
- Maxim Fateev, "Why Durable Execution Will Define the Next Decade", QCon 2023
- Cadence Workflow ペーパー (Uber Engineering Blog, 2017)
- Restate.dev 公式ドキュメント (durable-execution の比較セクション)
- Stephen Cleary, "Durable Functions" (Microsoft Docs)
- AWS Step Functions Internals (re:Invent 2019)
