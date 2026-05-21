# TigerBeetleと金融グレードDBの設計哲学：VOPRとViewstamped Replication
**日付**: 2026-05-18
**分野**: tech
**タグ**: #database #financial #determinism #VSR #consensus #DST

## 学んだこと

### TigerBeetleとは何か：固定スキーマの金融データベース
TigerBeetleは「金融トランザクション専用」に特化した分散DB。汎用RDBの真逆を行く。
スキーマは固定で、`Account`と`Transfer`の2つのオブジェクトしか扱わない。これは複式簿記（double-entry bookkeeping）の根本構造そのもの——「あらゆる金融取引は2つのアカウント間のtransfer」という公理に基づく。Stripe、Mollie、Adyenのような決済プロセッサが、PostgreSQLの上で1秒あたり数千件の決済を捌くために巨大なオーケストレーションレイヤーを組んでいる現実への、ラディカルな代替案である。

設計目標は3つの極限：
1. **1,000,000 transfers/sec** を6ノードクラスタで処理
2. **すべてのレコードが二度書かれる**（ACID + クラッシュ整合性）
3. **Strict Serializability**（最も強い一貫性モデル）

汎用DBが「何でもできる」ことで失う性能と正確性を、ドメインを絞ることで奪還する戦略。

### Viewstamped Replication（VSR）：Paxos以前の合意アルゴリズム
TigerBeetleの合意層はVSR(Oki & Liskov, 1988)を採用。これはRaftよりも古く、Paxosとほぼ同時期に提案された合意アルゴリズム。VSRはRaftのインスピレーション源だが、よりクリーンな設計と見なされることもある。

- **View number**: リーダーが交代するたびにインクリメントされる単調増加の論理時刻
- **Op number**: 各操作に割り振られる単調増加の番号
- **View change protocol**: プライマリ障害時、新リーダーは過半数のレプリカからログを集めて最新状態を再構築

VSRはRaftのように「ログを送る」のではなく「viewの遷移を合意する」モデル。State machine replicationの「正しさ」と「単純さ」のトレードオフが異なる。

### Deterministic Simulation Testing（DST）とVOPR
TigerBeetleの最も革新的な部分は、**VOPR**（Viewstamped Operation Replicator）と名付けられたシミュレーションテストフレームワーク。映画《WarGames》のWOPRから命名された遊び心。

仕組み：
- **すべての非決定性の源を抽象化**: ディスク、ネットワーク、システムクロック。これらすべてに代替実装を差し込み、シード値で再現可能にする
- **1コア上で6ノードクラスタ全体を時間圧縮シミュレート**: 1時間で1か月分、700倍の高速化
- **故障注入**: メッセージドロップ、bit rot、bad sector、ネットワーク分断、リーダー停止——確率的に注入
- **1,000 CPUコアで365日24時間稼働**: 1日あたり「2千年分」のシミュレートランタイムを稼ぐ

この発想の妙：「現実のクラスタを長時間動かしてバグを待つ」のではなく、「決定論的に時間を圧縮してすべての悪い偶然を再現可能に発生させる」。同種の発想はFoundationDBの`flow`ライブラリにもある（昨日のtech学習で扱った）が、TigerBeetleはZigで書かれゼロアロケーションを徹底することで、より極端に推し進めている。

### LSM-Forest：データファイル設計
TigerBeetleはLSM-Treeを「Forest」と呼ぶ独自構造で実装：
- **データファイルは単一の固定サイズファイル**（事前確保）。OSの動的アロケーションを信用しない
- **すべての書き込みは事前確保された領域への上書き**: ファイルシステムのメタデータ更新を最小化
- **チェックサムはBLAKE3**で各ブロックごとに記録、Reed-Solomon erasure coding でセクター故障に耐性

「ディスクは嘘をつく」という前提に立つ。fsyncのバグ、bit rot、サイレント破損——すべてが起きると想定して、それでも正確性を保つ設計。

### 性能：レコード設計とCPU効率
- すべてのオブジェクトは**128バイト固定**（cache lineにフィット）
- **バッチング**: クライアントから来た複数のtransferを一括してWAL書き込み、合意、適用。1リクエスト/トランザクションのコストを償却
- **NUMA-aware**, **io_uring** (Linux), **no allocations in hot path**: Zigのcomptimeとalignment制御を活用

その結果、PostgreSQL上で1,000 TPSを必死で稼ぐ決済システムが、TigerBeetleでは1M TPSに到達する。

## 気づき・洞察

### 「汎用性の捨て方」が新世代DBの共通戦術
DuckDB（OLAP特化）、TigerBeetle（金融特化）、FoundationDB（KVS特化）、ScyllaDB（shard-per-core）——いずれも「汎用RDBが負っているコスト」を、ドメインを絞ることで剥がしている。

これは「汎用ハードウェアから専用ハードウェアへ」というGPU/TPUの軌跡と相似。Worse-is-betterの逆転——RDBが30年間「すべてに使える」ことを売りにしてきた前提が、今や逆に重荷になっている。

### 決定論はテストではなく「証明」の前段階
DSTの本質は「テストカバレッジを増やす」ことではなく、「すべてのバグを再現可能にする」こと。一度シードと共に観測されたバグは、永遠に再現でき、デバッグできる。これはほぼ「形式手法の前段階」と言える——昨日学んだTLA+が「モデル上で性質を検証する」のに対し、DSTは「実装そのものを高速シミュレートで検証する」。両者は補完関係にある。

### 「複式簿記が公理」という発見
金融ドメインを「すべてのトランザクションは2アカウント間の振替」と抽象化したのは、ルカ・パチョーリ（1494年）の発明。500年以上の歴史を持つこの会計原理が、現代の最先端DB設計の数学的基礎になっている事実は美しい。Domain-specificであることが、結果として最も普遍的な構造を見出すことに繋がる。

## 他分野との接続

- **cs（昨日のTLA+）**: VSRはTLA+で形式仕様化されている。DSTは仕様検証ではなく実装検証だが、「決定論を確保する」というアプローチは同じ哲学
- **tech（昨日のTemporal）**: Temporal.ioのDurable Executionも「決定論的な再生」を性能ではなく耐障害性の手段として使う。TigerBeetleは「正確性の検証」に、Temporalは「再開可能性」に決定論を使う——同じ概念の異なる応用
- **anatomy（CPG）**: 「決定論的な内部時計」と「外部からの摂動への適応」という構造は、CPGの脊髄回路にも似ている。固定パターンと適応のトレードオフ
- **bread（FDT/温度管理）**: 「変動要因を一つずつ把握して制御する」FDT(Final Dough Temperature)の発想は、DSTの「非決定性を一つずつ抽象化する」と通底する

## 次に深掘りしたいこと
- VSRとRaftの合意プロトコルの正確な違い（特にview change時の安全性証明）
- Zigのcomptimeをどう活用してアロケーションフリーを実現しているか
- TigerBeetleがACIDトランザクションをどう表現するか（金融トランザクションは「2フェーズコミット相当のトランザクション」を必要とするケースも多い）

## 主要参考ソース
- [tigerbeetle/docs/internals/ARCHITECTURE.md](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/internals/ARCHITECTURE.md) (公式)
- [tigerbeetle/docs/internals/vopr.md](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/internals/vopr.md) (公式)
- [Why TigerBeetle is the most interesting database in the world](https://www.amplifypartners.com/blog-posts/why-tigerbeetle-is-the-most-interesting-database-in-the-world) (Amplify Partners)
- [A New Era for Database Design with TigerBeetle - InfoQ](https://www.infoq.com/presentations/tigerbeetle/) (InfoQ)
- [Oki, B. M., & Liskov, B. H. (1988). Viewstamped Replication](https://dl.acm.org/doi/10.1145/62546.62549) (PODC原論文)
