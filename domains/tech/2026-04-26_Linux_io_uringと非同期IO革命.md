# Linux io_uring と非同期I/O革命
**日付**: 2026-04-26
**分野**: tech
**タグ**: #io_uring #Linux #非同期IO #syscall削減 #PostgreSQL18 #ScyllaDB #Cloudflare #セキュリティ

## 学んだこと

### なぜ io_uring が生まれたか — 既存3モデルの構造的欠陥
Jens Axboe（Meta、ブロックレイヤメンテナ）が Linux 5.1（2019年5月）で導入。動機は既存の非同期I/Oモデルが揃って破綻していたため。

- **Linux AIO (`io_submit(2)`, libaio)**: `O_DIRECT` 限定で、バッファI/Oでは事実上同期fallback（page cache hitでも context switch が発生）。ソケット非対応。提出ごとに 104 バイトの `iocb` を kernel にコピーし、メタデータ管理に複数のロック。`io_getevents` は signal セーフでない。
- **POSIX AIO (`aio_read(3)`)**: glibc がユーザ空間スレッドプールにブロッキング read を投げる「fake AIO」。スレッド生成・signal 配送オーバヘッドで production 用途は不可。
- **epoll**: readiness 通知の reactor 型で、I/O 自体は別途同期 syscall が必要。1完了あたり最低 2 syscall（`epoll_wait` + `read`）。spurious wakeup と `EAGAIN` 再試行。バッファI/O・通常ファイルは対象外。

io_uring はこれら全てを統一する。**proactor 型完了通知**、**バッファI/O対応**、**ソケット・ファイル・dev 統一**、**0または1 syscall**、**スレッド不要**。

### SQ/CQ Ring アーキテクチャ
`io_uring_setup(2)` が3領域の匿名 mmap を返す:

1. **Submission Queue (SQ) Ring** — head/tail と SQE index 配列
2. **SQE 配列** — 実際の128バイトentry
3. **Completion Queue (CQ) Ring** — CQE 配列

head/tail は user/kernel 間で**共有メモリ**となる SPSC リング。SQE と CQE を分離するのは、完了が提出順序と異なる可能性があり、SQE を in-flight 中に上書きしないため。

メモリバリアは x86 TSO では smp_store_release/load_acquire で十分だが、ARM 等 weakly-ordered では明示バリアが要る。**liburing が抽象化**するので user は通常意識しない。

提出は SQPOLL 時 **0 syscall**、通常時も `io_uring_enter(2)` 1回で N 件 batch 投入できる。libaio の「1件ごとに `iocb` をコピー」より圧倒的に速い構造的根拠。

### モード別フラグ
| Flag | Kernel | 意味 |
|---|---|---|
| `IORING_SETUP_SQPOLL` | 5.1 | kernel 側に polling thread を置き SQ tail を busy-poll、syscall 完全排除 |
| `IORING_SETUP_IOPOLL` | 5.1 | NVMe block layer を polling、割り込み排除（`O_DIRECT` 必須）。SPDK に最も近い |
| `IORING_SETUP_COOP_TASKRUN` | 5.19 | task_work を signal 経由で割り込まず syscall 境界で実行 |
| `IORING_SETUP_DEFER_TASKRUN` | 6.1 | task_work を `io_uring_enter(GETEVENTS)` まで完全遅延（Dylan Yudaken / Meta） |

DEFER_TASKRUN は「大きな recv 完了が他処理の memcpy を割り込む」問題を回避する。`SINGLE_ISSUER` 必須で submitter == waiter 保証下でしか有効化できない。

### Linked SQEs / Registered Resources / Multishot

**Linked SQEs (`IOSQE_IO_LINK`)**: 連続 SQE を依存チェーンとして提出。例: `openat → read → close` を1回の `io_uring_enter` で（前段失敗ならチェーン自動キャンセル）。

**Registered files**: 通常 syscall は毎回 `fget_light/fput_light` で fdtable の RCU 参照取得・参照カウント操作が必要。事前登録すると io_uring が file ポインタを保持、SQE は index 指定（`IOSQE_FIXED_FILE`）。high-fanout サーバで顕著な効果。

**Registered buffers**: `get_user_pages/put_pages` で user ページを pin するコストを事前払い。`IORING_OP_READ_FIXED` で再利用。

**Provided buffers / ring-mapped buffers (5.19+)**: アプリが buffer pool を登録し、kernel 側が CQE 発行時に buffer を動的選択。multishot recv の必須機構。

**Multishot operations**: 1 提出で複数完了を生む。`POLL_ADD multishot` (5.13)、`ACCEPT multishot` (5.19、接続毎の SQE 提出不要)、`RECV/RECVMSG multishot` (6.0、provided buffer 必須)、`Receive bundles` (6.10、複数 buffer を1 CQE にまとめ)。エコーサーバ等で **CPU 使用率半減** クラス。

### 実用ベンチマークと採用事例
- **PostgreSQL 18 (2025)**: Andres Freund が長年提案してきた AIO 実装が `io_method = {sync, worker, io_uring}` で着地。pganalyze の pgbench で sync 15071ms vs io_uring 5723ms（**約2.6倍**）。EBS 等ネットワークストレージで顕著。
- **ScyllaDB / Seastar**: linux-aio backend を io_uring に置換。
- **Cloudflare**: ソケット I/O に利用。`IORING_REGISTER_IOWQ_MAX_WORKERS` (5.15+) で worker pool 制御。4096 SQE 提出が 4096 スレッド生む地雷を文書化。
- **その他**: QEMU virtio-blk、systemd-journald、libuv（opt-in）、Ceph BlueStore（評価中）。
- **Zero-copy send (`SEND_ZC`, 6.0)** + **kTLS** で TLS レコード暗号化まで kernel で完結し、user 空間に plaintext copy すら発生しない構成が可能。

### セキュリティ史 — Google の判断
Google Security Blog (2023年6月) によれば、kCTF VRP に提出されたエクスプロイトの **約60%が io_uring 起因**。約 100万USD の bug bounty 支払い。結果、Google は **ChromeOS 全面無効化**、**Android アプリ向け無効化**、**production server 無効化** に踏み切った。

主要 CVE:
- **CVE-2022-29582**: `IORING_OP_TIMEOUT` cancellation race → UAF → LPE
- **CVE-2023-2598**: registered buffer ring の境界外 read
- **CVE-2024-0582**: registered buffer 解除パスでの memory corruption → root LPE（6.4 まで影響）

**seccomp filter の構造的限界**: 通常 seccomp は syscall 単位だが、io_uring は「`io_uring_enter` を許可すると任意 opcode 実行可能」。`read` を seccomp で禁止しても `IORING_OP_READ` で迂回可能。これが「seccomp bypass」と評された根本原因。Linux 5.19 で `REGISTERED_FD_ONLY` 等の mitigation が入ったが、**運用上は io_uring 全体をブロック**する方が確実。Docker/containerd デフォルト seccomp からも除外推奨。

### 他OS・他技術との比較
| | パターン | I/O 種別 | バッチ提出 | カーネルバイパス |
|---|---|---|---|---|
| epoll | reactor | socket/pipe | × | × |
| kqueue | reactor | socket+timer+vnode+signal | × | × |
| **IOCP** | proactor | socket/file | × | × |
| **io_uring** | proactor | 全部 | ◯ | △ (IOPOLL/SQPOLL) |
| **SPDK** | userspace polling | NVMe only | ◯ | ◯ |

**IOCP** は io_uring の最も近い親戚（Win NT 完成形、completion port = CQ）。ただしバッチ提出 API はなく、`GetQueuedCompletionStatusEx` で複数取得のみ可能。SQE 相当の「事前準備の一括投入」は無い。

**SPDK 比較** (Didona et al., SYSTOR '22): ジョブ数 ≤10 で SPDK > io_uring(IOPOLL) > io_uring。SQPOLL 有 io_uring は SPDK 比 9-16% 劣。ジョブ数12以上では polling thread とアプリ thread の core 奪い合いで io_uring が逆転する場合も。**io_uring NVMe passthrough** (5.19+) が生 NVMe コマンド送信を可能にし、SPDK 領域を侵食している。

## 気づき・洞察

### 「syscall 削減」が真の革命
io_uring の設計哲学は「syscall を高速化する」ではなく「**syscall そのものを発生させない**」点に尽きる。SQPOLL モードは究極形——user/kernel 間の遷移コストを 0 にし、shared memory ring だけが境界となる。これは hypervisor の virtio や DPDK の queue モデルと同じ思想であり、**「OS 抽象境界を共有メモリで貫通する」というモダンシステム設計の収斂**を示している。

### proactor の遅延帰還
Linux は長年 reactor 文化（select/poll/epoll）だった。proactor の Win IOCP は1990年代に既に存在した。io_uring の登場は「**Linux が IOCP に追いついた**」という見方もできるが、SQ/CQ という user-kernel 共有 ring は IOCP には無い純粋な進化。**proactor + batched submission + zero-syscall** という三位一体は io_uring が初の発明。

### セキュリティと性能のトレードオフ
io_uring の脆弱性多発は偶然ではない——**カーネル境界を緩めるほど攻撃面が広がる**という原則の体現。完了通知だけでなく opcode 実行を user 空間からトリガーできる仕組みは、設計上 seccomp policy の粒度を破壊する。Google の判断は合理的で、「**性能が最重要のサーバ**でのみ採用、ユーザ近傍では無効化」が現実解。Confidential Computing と同様、性能と隔離が二律背反する領域。

### 「Linux で AIO は動かない」が終わった
PostgreSQL 18 は記念碑的——20年「Linux AIO は壊れている」と言われ続けた状態が解消された。Andres Freund のパッチセットは 2021 年から始まり、PostgreSQL 17 の streaming I/O API がその布石、PG18 でついに本実装。データベース業界の汎用認知が io_uring を成熟段階に押し上げた瞬間。

## 他分野との接続

- **CS (Kademlia DHT, LSM ツリー)**: 非同期 I/O は分散ストレージの I/O パスを律速する。LSM の compaction や DHT の peer 通信で epoll → io_uring 移行はスループットを直接押し上げる
- **CS (ロックフリー CAS)**: SQ/CQ ring は古典的な SPSC ロックフリーキューの実装。memory barrier の正しさが性能と正当性の同時条件
- **解剖学 (基底核と手続き記憶)**: SQPOLL モードは「習慣化された I/O 経路」を kernel polling thread に焼き付ける——大脳基底核が反射的運動経路を担うのと相同。reactor は意識的注意（前頭前野）、proactor は習慣化（基底核）の比喩
- **golf (ランダム練習 vs ブロック練習)**: io_uring の linked SQE は「依存タスクの一括計画」、multishot は「同型タスクの繰り返し」——両者を生で混在させられる API は、運動学習の文脈干渉効果と相似する練習設計
- **bread (Detmolder Verfahren の多段階発酵)**: 1段・2段・3段の選択は io_uring のモード（IOPOLL/SQPOLL/DEFER_TASKRUN）と同じ「**いつ kernel/オーブンに渡すか、どこまで user/職人が制御するか**」のトレードオフ

## 次に深掘りしたいこと

- **eBPF + io_uring の統合**: BPF プログラムを SQE で投入する `IORING_OP_BPF`（実装議論段階）。kernel-resident programmable I/O pipeline
- **NVMe passthrough と zoned namespace**: SPDK 代替としての成熟度
- **PostgreSQL 18 io_uring backend のチューニング**: shared_buffers, effective_io_concurrency との相互作用、AIO worker count
- **liburing の API 安定性**: 6.x 以降の追加 OP（`URING_CMD`、`SOCKET`、`CONNECT`）の運用評価
- **rust-uring エコシステム**: tokio-uring, monoio, glommio の比較、Rust async-runtime での採用状況
- **「io_uring を seccomp で安全に絞る」研究**: Linux 6.7+ の per-op deny 機構の実用性

## 参考ソース
- Jens Axboe, "Efficient IO with io_uring": https://kernel.dk/io_uring.pdf
- LWN.net, "Ringing in a new asynchronous I/O API": https://lwn.net/Articles/776703/
- LWN.net, "Deferring task work in io_uring": https://lwn.net/Articles/906470/
- liburing wiki, "io_uring and networking in 2023": https://github.com/axboe/liburing/wiki/io_uring-and-networking-in-2023
- Andres Freund, PGCon 2020 talk: https://anarazel.de/talks/2020-05-28-pgcon-aio/2020-05-28-pgcon-aio.pdf
- pganalyze, "Postgres 18: Accelerating Disk Reads with Async I/O": https://pganalyze.com/blog/postgres-18-async-io
- Didona et al., "A systematic study of libaio, SPDK, and io_uring" (SYSTOR '22): https://atlarge-research.com/pdfs/2022-systor-apis.pdf
- Joshi et al., "Upstreaming a flexible and efficient I/O Path in Linux" (USENIX FAST '24): https://www.usenix.org/system/files/fast24-joshi.pdf
- Cloudflare blog, "Missing Manuals: io_uring worker pool": https://blog.cloudflare.com/missing-manuals-io_uring-worker-pool/
- Google Security Blog (2023) via oss-sec: https://seclists.org/oss-sec/2023/q3/38
- LPC 2022, "io_uring command and Modern NVMe passthrough": https://lpc.events/event/16/contributions/1382/
