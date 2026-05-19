# DPDKとカーネルバイパスネットワーキング — ユーザー空間TCP/IPスタックとXDP/io_uringの設計比較

**日付**: 2026-05-20
**分野**: tech
**タグ**: #DPDK #kernel-bypass #networking #XDP #io_uring #userspace-tcpip #HFT #high-performance

## 学んだこと

### カーネルバイパスが解決する問題
Linux カーネルのネットワークスタックは「汎用」を担保する代わりに3つの本質的オーバーヘッドを抱える。(1) **割り込み駆動**: NIC が割り込み→softirq→ksoftirqd→ソケットバッファへの copy という長いパス、毎パケット2-4回のコンテキストスイッチ。(2) **メモリコピー**: NIC リングバッファ→ skb 構造体→ソケット受信キュー→ユーザー空間という3回のコピー、各々が L3 キャッシュをポリュート。(3) **システムコール**: `recv()` ごとに ring3→ring0 遷移、Spectre/Meltdown 緩和（KPTI）後は数百ns 追加。結果として汎用ソケットは1コア当たり 100-200k packets/sec が天井。10Gbps ライン（14.88 Mpps for 64B packets）には 70+ コア必要。

### DPDK（Data Plane Development Kit、Intel発、2010年〜現Linux Foundation配下）
**設計哲学**: 「カーネルを完全に迂回し、NIC を直接ユーザー空間にマップする」。(a) **UIO/VFIO** で NIC PCI BAR をユーザー空間にマップ→ドライバごとカーネルから引き剥がす（uio_pci_generic, vfio-pci）。(b) **busy-poll**: 割り込みではなく専用コア（isolcpus + nohz_full + cpuset 隔離）が無限ループで NIC リングを polling。(c) **HugePages** (2MB/1GB): TLB ミス削減、ユーザー空間 mempool として使用。(d) **PMD (Poll Mode Driver)**: Intel ixgbe/i40e/ice, Mellanox mlx5, NVIDIA BlueField 等の NIC ベンダー実装。

### 実測性能
talawah.io の HTTP ベンチマーク（4 vCPU c5n.xlarge）で DPDK ベースのスタックが **1.51M req/sec**、対するチューニング済みカーネルスタックは 358k req/sec。HFT（高頻度取引）系では DPDK が中央値 **850ns** vs 通常ソケット **18.4μs** ——21.6倍の改善。1コアで 10-30 Mpps（64B パケット）処理可能、これは AWS Nitro/Azure Boost のような SmartNIC ハードウェアオフロードに匹敵。

### F-Stack: FreeBSD TCP/IP を DPDK の上に載せた完全ユーザー空間スタック
F-Stack（Tencent 開発、2017〜）は DPDK 単独では持たない TCP/IP/HTTP プロトコル処理を解決する。FreeBSD 11 のネットワークスタック（Linux より高速とされる）をユーザー空間に移植、POSIX 風 API（`ff_socket`, `ff_recv`）とエプシロン互換層を提供。シングル 10GE NIC で 0.6M RPS。Tencent の DNS サーバ、CDN エッジで本番運用。設計は **share-nothing per-core**: 各 CPU コアが独立した TCB（TCP Control Block）テーブル・mempool を持ち、ロック競合ゼロ。Seastar（ScyllaDB の基盤）も同じ shard-per-core 設計だが Linux カーネル+SO_REUSEPORT+busy-poll で実現する点が異なる。

### 3つのアプローチの設計対比

| 手法 | 動作層 | 完全度 | プログラミング | 用途 |
|------|--------|--------|----------------|------|
| **DPDK** | PCI 直接、カーネル完全迂回 | 完全バイパス（L2 から） | DPDK API（C） | NFV, HFT, テレコム、SDN データプレーン |
| **XDP** | ドライバフック、カーネル内 BPF | 部分バイパス（早期drop/redirect） | eBPF（制限あり） | DDoS 防御、L4 LB、Cilium |
| **io_uring** | システムコール最適化 | カーネル維持、SQ/CQ 経由 | リング操作 | 汎用 I/O、ストレージ＋ネットワーク |

XDP は kernel に残るので汎用性が高くデプロイ容易だが、TCP は触れない（L2-L3 のみ）。io_uring（2019, Jens Axboe）は `recvmsg/sendmsg` のシステムコールバッチ化と zero-copy（IORING_OP_RECV_MULTISHOT, MSG_ZEROCOPY）でカーネルパスを維持しながら 2-3倍高速化、ソケット API 互換性を保つ。

### カーネルバイパスの代償
- **コアを焼く**: busy-poll は CPU 使用率 100% 固定（10W-40W/core）。アイドル時の電力効率は最悪。データセンタ規模では電力コストが直接 OPEX に響く（HFT は性能優先で許容、CDN は io_uring/XDP を選ぶ理由）
- **TCP の再実装が必要**: DPDK 単体には L4+ なし。F-Stack/mTCP/Seastar/VPP/SmartNIC 等の選択肢が必要。再輻輳制御、TCP オプションの完全実装、TLS 統合は重労働
- **デバッグが困難**: `tcpdump`/iptables/conntrack/sysctl/perf が効かない。DPDK 専用のテレメトリ（rte_metrics, dpdk-telemetry）を別途構築
- **NIC ベンダーロックイン**: PMD はベンダー固有、Intel→Mellanox 移植は実コスト
- **コンテナ/Kubernetes 統合が複雑**: CNI で SR-IOV/VFIO デバイス通過、HugePages 確保、isolcpus 設定が必要。Multus + SR-IOV CNI が標準解だが運用負担大

### 2026年の動向
- **DPDK 25.11 (LTS)**: ARM Neoverse V2（Graviton4）対応、RISC-V Vector 拡張サポート、TCP 用 GSO/GRO、QUIC ヘッダ処理オフロード API
- **SmartNIC が主役交代**: NVIDIA BlueField-3、AMD Pensando Elba、Intel IPU が DPDK ワークロードをハードウェア側に吸収。データセンタは「汎用 CPU 上の DPDK」から「SmartNIC ARM コア上の DPDK/VPP」へ
- **eBPF/XDP の躍進**: Cilium がサービスメッシュデータプレーンを XDP+eBPF で完全実装、Meta は L4 LB（katran）を XDP で運用。「kernel-bypass を捨てて kernel-acceleration へ」の揺り戻し
- **io_uring の本気化**: Linux 6.10+ で zero-copy send/recv、SQPOLL、IORING_REGISTER_PBUF_RING。汎用アプリでカーネルバイパスに迫る性能、運用容易性は圧倒的に上

## 気づき・洞察

**「カーネルを迂回する」の本質は責任の再分配**。汎用 OS が暗黙に提供していた抽象（割り込み、コピー、保護、輻輳制御、ファイアウォール、メトリクス）を、すべてアプリ作者が再実装する契約に切り替えるトレードオフ。性能を得るために「汎用性のオークションで全勝札を捨てる」設計判断であり、これは Nix（再現可能ビルドのために副作用を捨てる）、CRDT（強整合性を捨てて可用性を得る）、Rust 所有権（GC を捨てて静的解析に賭ける）と同じ「制約を受け入れて自由を得る」設計哲学のネットワーク版。

**3つの矛盾する力学のせめぎ合い**: ハードウェア進化（100GbE→400GbE→800GbE）でカーネル処理が物理的に追いつかない圧、SmartNIC 普及で「アプリより下」の処理がハードウェアに沈降する圧、eBPF/io_uring でカーネルを「捨てる」のではなく「改造する」道が拓けた圧——この3軸の交点に2026年のネットワーキングがある。**「カーネルバイパス vs カーネル内アクセラレーション」は別の問いに置き換わりつつある: 「処理を CPU/NIC/SmartNIC のどこに置くか」**。

**busy-poll の電力コスト＝コンピューティングの第二法則**: 性能を得るために電力を捨て、待機を不可能にする。これはニュートン的「等価交換」の物理。データセンタ全体最適では、HFT は許容、CDN/Web は io_uring 一択、テレコム/5G UPF は SmartNIC 委譲、という3層のシナリオ別最適化が固まってきた。

## 他分野との接続

- **cs（コンピュータアーキテクチャ）**: Spectre/Meltdown 緩和（KPTI）が DPDK 普及を加速した皮肉——カーネル境界の安全強化がコストを引き上げた結果、境界を越えない設計が経済的になった。投機実行サイドチャネル対策がネットワーキング設計を書き換えた間接的影響
- **cs（並行性）**: shard-per-core は Herlihy の wait-free 設計哲学と同源。共有状態を持たない＝ロック・キャッシュコヒーレンスのオーバーヘッドゼロ。F-Stack/Seastar/ScyllaDB/Redis cluster mode が同じ原理
- **anatomy（運動制御）**: busy-poll は脊髄反射と同型——皮質判断（割り込み駆動）を経由せず、専用回路（CPG＝中枢パターン発生器）が高速応答。汎用性を犠牲にしてレイテンシを得る設計の生体版
- **bread（発酵管理）**: 「自己組織化フィードバックループ」をユーザーが手動制御する点はサワードウの維持に近い。DPDK 利用者は OS が暗黙に管理していた制御ループ（バッファ、輻輳、再送）を自分で運転する
- **piano（演奏キュー）**: イベントセグメンテーション理論——演奏中の自動化された動作（暗譜キュー）と意識的判断の分離が、busy-poll（自動）と application logic（意識）の分離に対応

## 次に深掘りしたいこと

- F-Stack の TCB テーブル分散ハッシュアルゴリズム——RSS+Flow Director の N-tuple ハッシュとの相互作用
- Cilium のサイドカーレス・サービスメッシュ（Ambient Mesh の Linkerd 版とは別系統）——XDP+TC+kprobes での L7 処理実装
- io_uring の `IORING_OP_SEND_ZC` と DPDK の MBUF chain——zero-copy のコスト構造比較
- SmartNIC OS（NVIDIA DOCA、AMD SmartNIC Framework）の中身——ARM コア上のミニLinux で DPDK/VPP/eBPF を動かす Russian doll 構造
- 5G UPF (User Plane Function) のデータプレーン実装——VPP（FD.io）と DPDK の比較、ETSI MEC との整合
- AF_XDP の進化——カーネルパス維持しながら DPDK 並みの性能を狙う Linux ネイティブ解
- TCP の替わり: QUIC + DPDK の組み合わせ、Cloudflare quiche ライブラリの DPDK 統合動向

## 参考ソース

- talawah.io: "Linux Kernel vs DPDK: HTTP Performance Showdown"（実測ベンチマーク、Tier 2）
- F-Stack 公式（github.com/F-Stack/f-stack、Tencent運営、Tier 2）
- ArXiv: "Enabling Kernel Bypass Networking on gem5" (2301.09470)（学術論文、Tier 1）
- DPDK 公式ドキュメント（dpdk.org、Linux Foundation、Tier 1）
- nordvarg.com: "Kernel Bypass Networking: DPDK, io_uring, and XDP Compared"（技術ブログ、Tier 2、独立検証可能な数値）
