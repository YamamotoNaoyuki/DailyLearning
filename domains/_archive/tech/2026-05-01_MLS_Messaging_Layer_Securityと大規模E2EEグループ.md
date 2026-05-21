# MLS (Messaging Layer Security) と大規模E2EEグループメッセージング
**日付**: 2026-05-01
**分野**: tech
**タグ**: #MLS #E2EE #TreeKEM #暗号 #IETF #RFC9420

## 学んだこと

### MLSの位置づけ
MLS (Messaging Layer Security) は IETF が 2023 年 7 月に **RFC 9420** として標準化した、グループメッセージング向けエンドツーエンド暗号化プロトコル。Signal Protocol の Double Ratchet が「2 者間」で素晴らしい性質を達成したのに対し、MLS は **数千人規模のグループ**でも `O(log N)` で鍵更新できることを目的に設計された。アーキテクチャ仕様は **RFC 9750** に分かれている。Cisco Webex、Wire、Matrix（実装中）、Discord、Mozilla などが採用ないし実装を進めている。

### 解決すべき問題：Signal の限界
Signal/Double Ratchet をグループに素朴に拡張すると "Sender Keys" 方式になる。これは N 人グループで誰かが鍵を更新するたびに **N-1 個の Pairwise Channel** にメッセージを暗号化する必要があり、メンバー追加・削除・PCS（Post-Compromise Security）回復のコストが `O(N)`。1000 人グループでは破綻する。MLS は木構造でこれを `O(log N)` に落とす。

### TreeKEM：核心となる仕組み
MLS の核は **TreeKEM** という Continuous Group Key Agreement (CGKA)。各メンバーをリーフに配置した左右対称な二分木を作り、すべての内部ノードに「そのサブツリーのメンバー全員が共有する秘密」を割り当てる。ルートの秘密が「グループ秘密」となり、そこから派生したキーで実メッセージを AEAD 暗号化する。

メンバー A が鍵を更新したいとき：A はリーフから根までの経路上の各内部ノードに新しい秘密を生成し、その秘密を **「対側のサブツリーが復号できる公開鍵」** で暗号化して配布する。配布対象が `log N` 個のサブツリーで済むため、計算・帯域は `O(log N)`。HPKE (RFC 9180) ベースの KEM で公開鍵暗号化するので、DH 固定でなく将来的に **PQ KEM への差し替え（PQ-MLS）** が可能。

### Forward Secrecy と Post-Compromise Security
- **Forward Secrecy (FS)**: 過去に送ったメッセージが、現在の鍵漏洩で復号されない。MLS は各 epoch ごとに鍵を破棄。
- **Post-Compromise Security (PCS)**: 一度漏洩しても、その後の Update Commit でグループが「自己治癒」する。Signal も持つ性質だが、MLS はグループに対して `O(log N)` で実現できる点が画期的。

### Epoch、Commit、Proposal
MLS は **Epoch** という離散時刻を持つ。`Add` / `Remove` / `Update` の各操作は **Proposal** として提案され、誰かが **Commit** メッセージで複数 Proposal をまとめて epoch を進める。同時に複数の Commit が出ると **Concurrent Commit** が発生し、サーバー（Delivery Service）がどれを採用するか決定。負けた Commit を出したメンバーは状態を巻き戻して再 Commit する必要がある（楽観的並行制御）。

### Delivery Service と Authentication Service
MLS は **2 つの非信頼サーバー**を分離する：
- **Delivery Service (DS)**: Commit メッセージの順序付けと配信。中身は読めない。
- **Authentication Service (AS)**: 各メンバーの長期鍵 (Identity Key) を証明書として束ねて配布する。X.509 ベースまたは独自トラストモデル。

DS が改ざんしても、Commit にはシグネチャと epoch ハッシュが含まれるためクライアントが検出できる。Authentication は MLS 外部に押し出されており、OIDC や Keytransparency と組み合わせる。

### External Commit と RFC 9420 の追加機能
RFC 9420 は元の TreeKEM 論文 (Bhargavan et al. 2018) から大幅に拡張されている。最重要なのが **External Commit / External Proposal**: グループ外の人がグループに参加するとき、`KeyPackage` を取得して自分自身を Add する Commit を投げる。これにより招待を非同期で処理できる。CISPA の "ETK: External-Operations TreeKEM" (2025) はこの拡張部分の安全性を初めて形式的に証明した。

### Quarantined-TreeKEM と非アクティブメンバー問題
TreeKEM の弱点は「**ずっとオフラインのメンバー**」。彼らの保有する鍵が漏れても気づけず、PCS が回復しない。ACM CCS 2024 の Quarantined-TreeKEM は、一定期間アクティブでないメンバーをツリーから「隔離」し、再接続時に再認証することでこの問題を緩和する提案。

## 気づき・洞察

**「ツリー構造で集合演算を `log N` にする」発想は CS 的に既知**だが、それを「動的な集合・継続的鍵更新・部分情報の秘匿性」と組み合わせた点が秀逸。Bloom Filter が確率で集合を圧縮し、LSM ツリーが時間軸で書き込みを償却したように、TreeKEM は **「サブツリーごとの共通秘密」というインデックス構造**で `N 人 × T 回の更新` という二次元の問題を `log N × T` に落とす。

注目すべきは **Authentication と Confidentiality の分離**。Signal は両方を 1 つのプロトコル内で扱うが、MLS は「誰がこの公開鍵を持つか」の判断を外部に追い出した。これにより **Keytransparency**（Google が WhatsApp で展開）のような透明性ログと自然に組み合わさる。プロトコル設計の **疎結合** という意味で正しい判断。

**過去 1 週間のテーマとの繋がり**：MESI で見た「コヒーレンスを `log N` で配るのではなく invalidate でブロードキャストする」のは N が小さい CPU だから許される。MLS は「人間ユーザーは N が大きい」前提に立つ。Reed-Solomon が冗長で耐障害性を、Bloom Filter が確率で省メモリを、TreeKEM が階層で鍵スケーラビリティを得る。**「対称性を壊して階層を作る」**ことが分散系のスケール手法の中核。

PQ-MLS は来年以降の重大トピック。Signal の PQXDH は 2 者間のみで、グループ PQ-PCS は MLS が事実上唯一の本格的解。HPKE 抽象化の上で ML-KEM (Kyber) を差し替えるだけで PQ 対応できる設計は、Composable Cryptography の勝利でもある。

## 他分野との接続

- **CS（Reed-Solomon, Bloom Filter, MESI）**: 「集合構造を効率化するアルゴリズム」という共通テーマ。今週ずっと辿っている。
- **CS（Hindley-Milner, Curry-Howard）**: HPKE のような型安全な API 設計と、プロトコルの状態機械（epoch transitions）を型で表現する FSM の発想が近い。
- **音楽（カノン構造）**: Bach のフーガが主題を周期的に提示するように、MLS は epoch を周期的に進めて状態を更新する「リズム」を持つ。フーガの主題が変容しながら同一性を保つのは、グループメンバーが Add/Remove されても同じ「グループ」として連続する MLS の構造と相似。

## 次に深掘りしたいこと
- HPKE (RFC 9180) の暗号学的詳細：mode_psk, mode_auth_psk の使い分け
- PQ-MLS の進捗：ML-KEM 統合のドラフト
- Matrix プロトコルが MLS に移行している理由と難点（既存 Olm/Megolm との互換性）
- Quarantined-TreeKEM の論文を読み込み、実装上のトレードオフを理解する

## 主要参考ソース
- [RFC 9420 - The Messaging Layer Security (MLS) Protocol](https://datatracker.ietf.org/doc/rfc9420/) - IETF 標準仕様
- [RFC 9750 - The MLS Architecture](https://www.rfc-editor.org/rfc/rfc9750.html) - アーキテクチャ仕様
- [ETK: External-Operations TreeKEM and the Security of MLS in RFC 9420](https://eprint.iacr.org/2025/229.pdf) - CISPA 2025 形式的証明
- [Quarantined-TreeKEM, ACM CCS 2024](https://dl.acm.org/doi/10.1145/3658644.3690265) - 非アクティブユーザー対策
