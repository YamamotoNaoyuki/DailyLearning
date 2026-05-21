# PaxosとRaft — 分散合意アルゴリズムの設計と「理解可能性」という美徳

**日付**: 2026-05-07
**分野**: cs
**タグ**: #分散合意 #Paxos #Raft #リーダー選出 #ログ複製

## 学んだこと

### 分散合意問題 — なぜ難しいのか

分散システムにおいて「全ノードが同じ値に同意する」ことは自明に難しい。FLP 不可能性定理 (Fischer-Lynch-Paterson, 1985) は「**非同期通信モデルで 1 ノードでも故障する可能性があるなら、合意は決定的アルゴリズムでは保証できない**」ことを証明した。これは衝撃的な結果で、「完全な合意」は不可能と理論的に確定した。

しかし実用的には合意を取らなければデータベースの複製・分散ロック・リーダー選出などが成立しない。FLP の壁を回避する方法:

1. **同期性の仮定を緩めない**: タイムアウトを使えば確率的に進行できる
2. **故障モデルを限定**: ビザンチン故障 (悪意ある嘘) を排除し、停止故障 (crash-stop) のみ仮定する
3. **進行性 (liveness) を犠牲にして安全性 (safety) を優先**: 「合意が取れない場合は止まる」が「誤った合意を取ることはない」を保証する

Paxos と Raft はいずれもこの方針 (停止故障モデル + 安全性優先) を採用している。

### Paxos の核 — Leslie Lampport の「議会の比喩」

Paxos は Leslie Lamport が 1990 年に発表 (実際の論文出版は 1998 年) した分散合意アルゴリズムで、ギリシャ・パクソス島の架空の議会システムに見立てて記述された。中核アイデアは:

**役割**:
- **Proposer**: 値を提案する
- **Acceptor**: 提案を受け入れるか拒否するか決める
- **Learner**: 合意された値を学習する (実装上は Acceptor と兼務されることが多い)

**2 フェーズ構成**:
1. **Prepare フェーズ**: Proposer が一意な番号 n を生成し、Acceptor 過半数に "Prepare(n)" を送る。各 Acceptor は「これより大きい番号で promise したことがなければ」、自分が以前 accept した値 (あれば) を返答しつつ、今後 n より小さい提案は無視すると約束する
2. **Accept フェーズ**: Proposer は過半数の応答を受け取れば "Accept(n, v)" を送る (v は応答の中で最大番号の値、または自分の提案値)。Acceptor は promise した値より大きい番号なら accept する

過半数 (quorum) の交差性により「2 つの異なる値が同時に合意される」ことはない。これが安全性を保証する。

**Multi-Paxos**: 単一値の合意ではなく、ログのような連続値の合意には Multi-Paxos が使われる。リーダーを 1 つ選び、Prepare フェーズを最初に 1 度だけ実行し、以降は Accept フェーズのみで連続合意する。

### Paxos の「分かりにくさ」問題

Paxos は理論的に優雅だが、実装する人が悪戦苦闘することで悪名高い。Lamport 自身が "Paxos Made Simple" (2001) という論文を「これでも分からない人のために」書き直したほど。Google の Mike Burrows の有名な発言: 「**世界には 1 つの分散合意アルゴリズムしかない: Paxos である。他の全ては Paxos の不正確な (broken) バージョンか、Paxos の特殊ケースだ**」。同時に Paxos 実装者の苦悩を表現する: 「**Paxos の論文と実装の間には『ここに魔法を書く』という補助定理が無数にある**」。

具体的な落とし穴:
- リーダー選出が明示されていない (実装者が別途設計する必要)
- ログ圧縮 (snapshot) の手順が論文にない
- メンバ変更 (cluster reconfiguration) は別の論文 "Cheap Paxos" で扱われる
- 実装の正しさ証明が極めて難しい (TLA+ 仕様が後付けで作られた)

### Raft の登場 — 「理解可能性」を第一原理に

Diego Ongaro と John Ousterhout が 2014 年に発表した **Raft** は、Paxos の「分かりにくさ」を **設計上の欠点** として明確に位置付け、「**理解可能性 (understandability) を第一原理に置く合意アルゴリズム**」として設計された。これはコンピュータサイエンスにおける設計判断としてかなり珍しい: 通常は性能・正しさが第一優先で、可読性は二の次だが、Raft は「実装ミスを減らすために、理解しやすさが性能より重要」と判断した。

Raft の構造:

**3 つのサブ問題に分解**:
1. **リーダー選出 (Leader Election)**: 明示的に常にリーダーが 1 人
2. **ログ複製 (Log Replication)**: リーダーが全フォロワーに log entries を複製
3. **安全性 (Safety)**: リーダー変更時のログ整合性保証

**役割**: Leader, Follower, Candidate の 3 状態のみ。各ノードは時刻 (term) を持ち、term ごとに 1 人のリーダーを選ぶ。

**リーダー選出**:
- Follower は heartbeat を一定時間受信しなければ、自分を Candidate に昇格させ、term を +1 して投票要求を送る
- 過半数の投票を得れば Leader になる
- 投票は **first-come-first-serve** + **ログが自分以上に新しい候補者にだけ投票** という制約付き
- ログ制約により「過半数の票を得るリーダーは必ず最新ログを持つ」が保証される

**ログ複製**:
- 全コミュニケーションは Leader → Follower 方向 (Paxos より対称性が低い)
- Leader はクライアント要求を受けると、自分のログに append し、AppendEntries RPC で Follower に送る
- 過半数が応答すれば commit、結果をクライアントに返す

### Paxos vs Raft の本質的差異

両者は「**同じ問題を解く同じ抽象クラスのアルゴリズム**」だが、設計判断が異なる:

| 観点 | Paxos | Raft |
|------|-------|------|
| リーダー | 暗黙的、外付け設計 | 明示的、強制 |
| ログ整合性 | リーダーが最新でなくてもよい (前 term のログを後 term で複製可) | リーダーは必ず最新 |
| 投票制約 | Acceptor は誰にでも投票 | Follower は最新ログを持つ Candidate にのみ投票 |
| 認識上のコスト | 高い (理論優雅、実装困難) | 低い (理論やや冗長、実装直感的) |
| 性能上の差 | ほぼ同等 | ほぼ同等 |

Heidi Howard の論文 (Cambridge, 2020) "Paxos vs Raft: Have we reached consensus on distributed consensus?" は、両者が事実上等価であると示しつつ、Raft の制約 (リーダーは最新ログ持ち) は実装簡略化のための賢明なトレードオフだと結論している。

### 実装エコシステム

- **Paxos 系**: Google Chubby, Apache ZooKeeper (Zab), Spanner, Megastore
- **Raft 系**: etcd, Consul, TiKV, CockroachDB, MongoDB (一部), Kafka KRaft

新規プロジェクトでは Raft 採用が圧倒的に多い。これは「実装難易度 = 採用判断」を端的に示している。

## 気づき・洞察

Raft の最大の貢献は「**理解可能性」を測定可能な研究課題にしたこと**である。Ongaro の博士論文では、43 人の大学院生に Paxos と Raft の解説を見せて理解度テストを行い、Raft 群が有意に高得点を取ったと示している。これはコンピュータサイエンスの論文で「人間の認知」を実験変数として扱う希有な研究で、ソフトウェア工学に通じる: アルゴリズムは「動く」だけでは不十分で、「正しく実装される」ことが重要であり、後者は人間の認知能力に依存する。

これは私が Automerge / CRDT (今日の tech エントリ) で見た発想と同根である: CRDT は「衝突解決ロジックを事前に代数的に保証する」ことで、実装者が考えなくていい設計を提供する。Raft も同様に「リーダーは常に最新ログを持つ」という強い制約を設けることで、実装者が考えるべきエッジケースを減らす。両者ともに「**人間の限界を踏まえた制約設計**」が哲学。

そして FLP 不可能性との関係も興味深い: 両アルゴリズムは「合意が永遠に取れない可能性」を完全には排除できない (split vote が無限に続く理論的可能性)。だが実装上は「ランダム化されたタイムアウト」によって確率的に必ず進行する。理論的不可能性 + 実用的可能性 という併存は、計算理論全般に見られるパターン (例: 暗号は計算量的に安全だが情報論的には破られる)。

最後に、Lamport の言葉「Paxos は世界唯一の合意アルゴリズム」と Ongaro の Raft の登場は対立しているように見えて、実は連続している: Lamport は「**問題の構造**」が一つしかないと言ったのであり、Raft はその構造の **異なる表現** である。数学的構造を一つにすると、表現の選択は工学判断となる。これは群論で「同型な群は本質的に同じ」と言いつつ、扱う表現 (置換群、行列群) によって計算難易度が変わるのと同じ。

## 他分野との接続

ゴルフの **マッチプレー戦略** (今日の golf エントリ) との意外な対応がある。マッチプレーでは「相手の状態を観察してから自分の戦略を決定する」相互依存性がある。Paxos の Prepare-Accept 2 フェーズ構造も「相手 (Acceptor) の状態を Prepare で確認してから Accept する」という同じ構造。両者ともに「相手の状態への適応的最適化」というゲーム理論的構造を持つ。

CRDT (Automerge、今日の tech エントリ) との関係は、両者が「**分散整合性問題への異なる解**」である点。Paxos/Raft は「全員で合意する」アプローチ (強整合性)、CRDT は「衝突しない代数で個別動作する」アプローチ (弱い整合性、ただしマージは保証)。これは「合意 vs 自律」のトレードオフで、用途によって最適解が異なる。実際のシステムでは両者を併用する: Spanner は Paxos でリーダー合意、その上で CRDT 的手法でマルチリージョン書き込みを最適化。

音楽の **ドビュッシー《ペレアス》** との哲学的対応: ドビュッシーがワーグナー的「最大主義」に対して「最小主義」を選んだように、Raft が Paxos の「理論優雅な抽象」に対して「実装可能な具体」を選んだ。両者ともに「より大きく・より複雑に」ではなく「より分かりやすく・より到達可能に」という美学を共有している。

## 次に深掘りしたいこと

- Multi-Paxos のリーダー安定化機構 (livelock を防ぐためのリーダーシップ)
- Raft の log compaction (snapshot) の実装詳細と性能
- Byzantine Fault Tolerant 合意 (PBFT, HotStuff) と Raft の差異
- EPaxos (Egalitarian Paxos) の "leaderless" 設計と現代の実装

## 主要参考ソース

- Ongaro, Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft 原論文, USENIX ATC 2014)
- Lamport, "Paxos Made Simple" (2001)
- [Heidi Howard, "Paxos vs Raft" (Cambridge)](https://www.repository.cam.ac.uk/bitstreams/14f1d94c-6022-4ef6-9175-33be465b80c0/download)
- [Distributed Consensus: Paxos vs. Raft (DEV Community)](https://dev.to/narendars/distributed-consensus-paxos-vs-raft-and-modern-implementations-2gng)
- [Paxos vs. Raft Algorithm in Distributed Systems (GeeksforGeeks)](https://www.geeksforgeeks.org/system-design/paxos-vs-raft-algorithm-in-distributed-systems/)
