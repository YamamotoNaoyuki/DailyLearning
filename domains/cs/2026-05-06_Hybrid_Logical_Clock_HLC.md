# Hybrid Logical Clock (HLC) — 物理時刻と論理時刻のハイブリッド
**日付**: 2026-05-06
**分野**: cs
**タグ**: #分散システム #HLC #論理時計 #因果一貫性 #CockroachDB #Spanner #TrueTime

## 学んだこと

### 出発点 — Lamport / Vector clocks の限界
昨日整理した通り、Lamport 時計は `a → b ⇒ C(a) < C(b)` の **片方向**しか保証せず、ベクトル時計は `a → b ⟺ V(a) < V(b)` の双方向同値を持つが O(N) のサイズと「人間に読めない数列」というデメリットを抱える。実運用ではもう一つの致命的な弱点がある — **どちらも wall clock とまったく相関しない**。デバッグで「2026-05-06 14:32 のイベント」を探せず、TTL や retention policy（「7 日前のデータを削除」）も書けない。

一方で wall clock 単体では因果関係を保証できない。NTP 同期は通常 ms 〜 数十 ms の skew を残し、leap second / VM pause / cgroup throttle で**逆行**もする。Cassandra の初期 LWW (last-write-wins) が時計ずれで update を消した事故は、wall clock を因果保証として使った代償だった。

### TrueTime — Google Spanner のハードウェア解
Corbett et al. (OSDI 2012) の Spanner は、各データセンタに **GPS 受信機 + 原子時計** を冗長配置し、`TT.now()` が `[earliest, latest]` の不確実性区間を返す API を提供する。区間幅 ε は通常 1〜7 ms に抑えられている。Spanner の commit-wait は「自分が割り当てた commit timestamp s が `TT.now().earliest` を確実に下回るまで `2ε` 待つ」ことで **external consistency (= strict serializability)** を実現する。

これは美しいが、コストが厳しい：
- データセンタ全棟への GPS アンテナ + 原子時計の物理配備
- Google 内部の専用時刻配信プロトコル
- 数 ms の commit-wait をクリティカルパスに固定で入れる前提

オンプレ・マルチクラウド・コミュニティ実装では現実的でない。**ここに Hybrid Logical Clock の設計余地がある。**

### HLC のコア発想 (Kulkarni et al., OPODIS 2014)
論文 "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases" の核心アイデアは、各イベントのタイムスタンプを **`(l, c)` ペア**で表現することにある：

- `l` (logical part)：そのノードがこれまで観測した中で最大の物理時刻ベース値。NTP の `pt` を下回らないが、メッセージ受信で他ノードの `l` に追従して**前進**する。
- `c` (counter)：同じ `l` 内でイベント順を区別する単調増加カウンタ。Lamport 時計の精神を継承。

辞書式比較で全順序が定義され、`l` 部分は**常に NTP 物理時刻に近い値**として人間に読める。

### HLC 更新ルールの擬似コード
論文 Algorithm 1 の本質を簡潔に書くと：

```
// 各ノードのローカル状態
l : int64   // 最新の論理時刻
c : int64   // 同 l 内のカウンタ
pt() : int64  // NTP 物理時刻 (ms or ns)

// (1) ローカルイベント (write, internal step)
on local_event:
    l_old = l
    l = max(l_old, pt())
    if l == l_old:
        c = c + 1
    else:
        c = 0
    return (l, c)

// (2) メッセージ送信
on send(m):
    ts = local_event()
    m.timestamp = ts

// (3) メッセージ受信
on receive(m):
    l_old = l
    l = max(l_old, m.timestamp.l, pt())
    if l == l_old == m.timestamp.l:
        c = max(c, m.timestamp.c) + 1
    else if l == l_old:
        c = c + 1
    else if l == m.timestamp.l:
        c = m.timestamp.c + 1
    else:  // l == pt()
        c = 0
    return (l, c)
```

ここで重要な不変条件は **`l ≥ pt()` ではない、`l ≥ pt()` でも `l ≤ pt() + ε`**（NTP skew bound 内）になる、という点。`l` は物理時刻を**上回り得る**が、`l - pt()` は有界に保たれる。Kulkarni らはこの差を **drift** と呼び、発散しないことを証明した。

### Causality は捕まえるが、因果関係**を完全に**特徴付けはしない
HLC が保証するのは Lamport 時計と同じ片方向：

> `e → f` ⇒ `HLC(e) < HLC(f)`

逆 `HLC(e) < HLC(f) ⇒ e → f` は**成り立たない**。これは spec 上の弱点ではなく **意図された設計判断** — 双方向保証はベクタークロックが必要で O(N) になる。HLC は「Lamport 時計のサイズ (O(1)) + 物理時計の人間可読性」を狙ったので、因果完全性は最初から放棄している。

代わりに HLC は **causal consistency 実装に十分な順序情報**を提供する。MongoDB の `afterClusterTime` での causal session、CockroachDB の uncertainty interval read はいずれもこの片方向保証で動く。

### Causal consistency vs External consistency
重要な区別：
- **Causal consistency**：因果関係 `→` を保つ全順序を提供する。HLC で達成可能。
- **External consistency (= strict serializability, Spanner 用語)**：トランザクション T1 が wall clock 時刻 t1 にコミットし、T2 が後で開始するなら、T2 は T1 を観測する。実時間順序と整合する。**TrueTime + commit-wait でしか達成できない**（または等価な物理時刻保証）。

HLC は external consistency を**保証しない** — 2 つの独立トランザクションが地理的に離れた DC で並行コミットしたとき、因果関係がなければ HLC タイムスタンプの大小と実時間順序は一致し得ない。CockroachDB は serializable は保証するが external consistency は明示的に放棄しており、代わりに **uncertainty interval (max_offset, default 500 ms)** で「読み飛ばし」を検出する。

### Bounded skew assumption — HLC の正しさの土台
HLC の正しさ証明は **clock skew が有限 ε で抑えられている** ことに依存する。NTP がまともに動いていれば通常 ε ≤ 250 ms 程度、Chrony や PTP なら μs 級。ε を超えた場合、HLC はまだ単調性を保つが「causality を伝えない値が大きく drift する」可能性がある。

CockroachDB はこれを `--max-offset 500ms` で陽に表現し、ノードが自分の物理時計が他ノードから 500ms 以上ずれていると検知すると **panic して自殺**する。これは「壊れた時計で動き続けて consistency 違反を出すより、ノードを落とすほうが安全」という設計哲学。

### 実装事例
| システム | HLC 用途 | 特徴 |
|---|---|---|
| **CockroachDB** | トランザクション timestamp | uncertainty interval `[ts, ts + max_offset]` 内の committed value を見つけたら `ReadWithinUncertaintyIntervalError` で再試行。HLC + read restart で external consistency 風の serializable を達成 |
| **YugabyteDB** | Raft + HLC | Spanner-like architecture を TrueTime なしで実現。HLC を Raft entry timestamp に使用 |
| **MongoDB 3.6+** | causal session | `afterClusterTime` が HLC タイムスタンプ。クライアントが session token を保持し、replica set 切り替え後も自分の write を観測できる |
| **FoundationDB** | (HLC ではない) 単一 sequencer | 全 commit を 1 ノードでシリアライズ。HLC の代替設計 — 「分散時刻に頼らず単一順序源を持つ」哲学 |

### HLC vs TrueTime — トレードオフ
| 観点 | TrueTime (Spanner) | HLC (CockroachDB等) |
|---|---|---|
| ハードウェア | GPS + 原子時計必須 | NTP のみ |
| commit latency | 固定 `2ε` (1〜14 ms) wait | 0 wait、ただし read uncertainty で retry コストあり |
| 一貫性レベル | external consistency (linearizable) | serializable + causal、external は不保証 |
| skew 許容 | ε 内なら自動補正 | max_offset 超過で node panic |
| 運用環境 | Google 専用 / 高度なオンプレ | 任意のクラウド / コモディティ NTP |
| デバッグ可読性 | wall clock 直接 | HLC の `l` 部が wall clock 近似 |

これは「ハードウェアコストで latency を確定 (TrueTime)」vs「ソフトウェアコストで retry 確率を受容 (HLC)」のトレードオフ。

### HLC の限界と落とし穴
1. **Cross-region read-after-write**：HLC は因果セッションを伝播するメタデータ (session token, gossip) を要求する。クライアント側で持たないと、地理分散環境では「自分の write が見えない」現象が起きる。
2. **Monotonicity violation**：物理時計が逆行 (NTP step adjustment, VM live migration, leap second smear) すると `pt()` が後退するが、HLC は `l = max(l, pt())` で自身は単調性を保つ。ただし `l - pt()` drift が積み重なる。CockroachDB は `pt()` の逆行を検出してログを吐く。
3. **C 部分の overflow**：`l` が同一値で固定された期間が長いとカウンタ `c` が無制限に増える可能性。論文では `c < 2^16` で `l = l + 1`, `c = 0` する救済策を提示。実装では稀。

### Hybrid Vector Clocks (HVC) と Stable Timestamp
- **HVC (Demirbas-Kulkarni 2017)**：HLC のベクトル版。`(pt, [c_1, ..., c_N])` で因果完全性 + 物理時刻近似を両立。サイズ O(N) は HLC と同じく避けられない。
- **Stable Timestamp**：CockroachDB / TiDB が follower read で使う概念。「この timestamp 以下の全 transaction が解決済み」と保証された値で、HLC を使って分散合意される。「**読み手は最新ではなく `safe_ts` で読む**」設計が、leader にトラフィックを集中させずに consistent read を可能にする。

## 気づき・洞察

HLC の設計判断で最も学びがあるのは **「因果完全性を捨てる」という選択** を明示的にしたこと。学術的には vector clock が「正しい」答えで、HLC は「弱い」が、運用現場では「O(1) で wall clock に近く、ほとんどの causal consistency 用途に十分」が圧倒的に勝つ。これは [4/29] で扱った Reed-Solomon の MDS 性質を Locally Repairable Code (LRC) で**部分的に犠牲**にして修復帯域を最適化した設計と同型 — **理論的最適性より、運用上の支配的コスト軸を最適化する** という工学判断。

もう一つ深い対比は **Spanner vs CockroachDB の哲学差**。Spanner は「不確実性をハードウェアで消す」、CockroachDB は「不確実性をソフトウェアで管理する」。前者は Google 規模の vertical integration があって初めて成立し、後者は Google 帝国外での Spanner-likeness を可能にした。Kulkarni et al. 2014 がなければ CockroachDB / YugabyteDB は今の形で存在しない。**論文一本がエコシステムの形を決める** 例。

`l = max(l, pt())` のたった一行は、Lamport 時計の `C ← max(C, msg.C) + 1` と TrueTime の `[earliest, latest]` の中間を取る蝶番の役割を果たす。`max` 演算が因果保証を与え、`pt()` 参照が wall clock 近似を与え、両者の組み合わせが skew bound 仮定下で drift を有界に保つ。**設計の最小性が美しい** — Lamport 時計に「物理時刻を mix する」という一動作を加えただけで、運用上の問題を一気に解いた。

## 他分野との接続

- **tech (HTMX)**：HTMX は「JavaScript で書ける完全な SPA」を諦めて「サーバ駆動の HTML 断片置換」で 80% の用途に対応する。**理論的最大表現力を捨てて運用コストを最適化する**戦略は HLC と同型 — 「vector clock が正しいけれど HLC で十分」「React で完全制御できるけれど HTMX で十分」。
- **music (Arvo Pärt の Tintinnabuli)**：Pärt の作風は伝統和声の複雑性を捨てて 3 和音の sustained tone (tintinnabuli voice) と旋律 (M-voice) の 2 軸に還元した。**O(N) を O(2) に削る**ことで本質を浮かび上がらせる。HLC が `(l, c)` の 2 次元に分散時刻を畳み込む発想と通じる。
- **piano (スロー・プラクティス)**：遅いテンポで弾くとき、各音の物理時刻 (テンポ) と論理時刻 (拍構造) は別の役割を持つ。物理時刻だけ遅くしても拍構造が崩れれば学習効果が無く、論理時刻だけ意識しても物理的な指運動が雑なら身につかない。**両者を独立に保ちつつ整合させる**訓練は HLC の `l` と `c` の役割分担に似る。
- **golf (TPI Titleist Performance Institute)**：TPI のスクリーニングは「クラブヘッドスピード (物理)」と「キネマティック・シーケンス (論理順序: 骨盤→胸郭→腕→クラブ)」を別軸で評価する。physical と logical が同じスイングの異なる側面を捉えるのは HLC が同じイベントを `pt` と `c` で多面的に表すのと同型。
- **anatomy (迷走神経 HRV)**：心拍変動 (HRV) は「絶対時刻での拍数」(物理) ではなく「拍間隔の論理的揺らぎ」(変動性) で自律神経を評価する。物理時刻だけ見れば「規則的」が良いが、論理的多様性が**喪われた状態こそ病態**。HLC が「物理近似 + 論理因果」を両立するのと同じく、生体時計も両軸で機能する。
- **bread (パネトーネ)**：パネトーネの一次発酵 (lievito madre) は時計時間 (12 時間) よりもドウの **論理的状態** (酸性度、体積倍率、グルテン展開) で判定する。物理時刻と論理状態の両方を見ながら焼くのは HLC オペレータの心構えに近い。

## 次に深掘りしたいこと

- **Interval Tree Clock (Almeida-Baquero-Fonte 2008)**：動的にプロセスが出入りする環境向けのベクトル時計拡張。HLC と組み合わせる研究 (Hybrid ITC) はあるか？
- **CockroachDB の uncertainty interval read restart の証明**：HLC + max_offset で本当に serializable が出るのか、Jepsen レポートで何が見つかったか。
- **Spanner の commit-wait を消す試み**：Tencent CynosDB や Alibaba PolarDB-X の Spanner-like 実装で TrueTime 代替に何を使っているか。
- **HLC の formal verification**：TLA+ で HLC の correctness を機械的に検証した事例。Lamport 自身が TLA+ を作ったことも踏まえると、思想的に閉じている。
- **Closed timestamps (CockroachDB)**：follower read を可能にする「安全な過去時刻」の伝播プロトコル。HLC + Raft の組み合わせ最適化。

## 主要参考ソース
- Kulkarni, Demirbas, Madappa, Avva, Leone, "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases", OPODIS 2014
- Corbett et al., "Spanner: Google's Globally-Distributed Database", OSDI 2012
- CockroachDB Engineering Blog, "Living Without Atomic Clocks: Where CockroachDB and Spanner Diverge", 2017
- MongoDB Documentation, "Causal Consistency and Read and Write Concerns" (3.6+)
- Demirbas, Kulkarni, "Hybrid Vector Clocks", 2017
- Bailis, Fekete, Ghodsi, Hellerstein, Stoica, "Highly Available Transactions: Virtues and Limitations", VLDB 2014
- Jepsen Reports on CockroachDB (Kyle Kingsbury, 2017, 2020)
