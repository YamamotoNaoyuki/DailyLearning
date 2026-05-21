# eBPF — カーネルを安全にプログラマブルにする革命
**日付**: 2026-04-27
**分野**: tech
**タグ**: #eBPF #Linuxカーネル #verifier #CO-RE #sched_ext #BPF_Arena #BPF_Token #Cilium #observability

## 学んだこと

### 起源 — cBPF からの再発明
**eBPF (extended Berkeley Packet Filter)** はその名に反して、すでに「BPFのフィルタ拡張」とは別物である。Steven McCanne と Van Jacobson が1992年の USENIX Winter で発表した古典 BPF (cBPF) は、`tcpdump` のためのレジスタマシン2本と64命令、合計4KBの最大プログラムサイズで設計された純粋なパケットフィルタ言語だった。Alexei Starovoitov が2014年（Linux 3.18）に持ち込んだ extended BPF は、これを**11個の64ビットレジスタ・10ステップ呼び出し規約・JITコンパイル前提・カーネルヘルパ呼び出し可能・任意フックポイントへのアタッチ**へと拡張し、結果として**カーネル内に組み込まれた汎用プログラマブル仮想マシン**へと変質した。Brendan Gregg が「Linuxの中で動く JavaScript」と呼んだのはこの意味だ。

### Verifier — 「**意図的なチューリング不完全性**」が安全性の源泉
eBPF の核心は **静的検証器 (verifier)** にある。プログラム読込時に kernel が以下を検査する:

1. **CFG 検証**: DAG として閉路を許さない（**ループは bounded loop のみ**、Linux 5.3 から `pragma unroll` 不要の bounded loop が許可、5.17 から有限回 `bpf_loop` ヘルパ）。
2. **抽象解釈**: 1命令ずつ全分岐を辿り、各レジスタ・スタックスロットの**取りうる値の範囲**を `struct bpf_reg_state` に追跡。ポインタ算術・境界外アクセス・初期化前メモリ参照を検出。
3. **メモリ安全**: マップ・スタック・パケットバッファ以外には触れない。ポインタ加算は範囲が型に閉じ込められる（`PTR_TO_PACKET` は packet end チェック後でしか使えない）。
4. **終了保証**: 命令数に上限（古典的に1万、現在は事実上100万に拡張）。
5. **カーネルヘルパ呼び出し型検査**: `bpf_helper_proto` で引数の型・範囲が宣言され、verifier がコンパイル時に整合性検証。

これは Rice の定理を**問題側を制限することで回避**した実装だ。任意のチューリング機械の停止性は判定不能だが、ループ展開・有界ヘルパ・型付きポインタという制約のもとでは、静的解析が完全に通る。**安全性は形式手法でなく言語設計で得られている**。

### JIT — 解釈実行されない
verifier 通過後、bytecode は**ターゲットアーキテクチャのネイティブコードに JIT コンパイル**される（x86_64, arm64, ppc64le, riscv 全て対応）。eBPF レジスタ R0-R10 は System V AMD64 ABI に意図的にマップされ、関数呼び出し境界がそのまま転写される。性能は**解釈オーバーヘッドゼロ**でカーネルモジュールと同等。kprobe/tracepoint アタッチでも μs オーダ。

### フックポイント — kernel イベントの90%以上に注入可能
| カテゴリ | フック | 用途 |
|---|---|---|
| Tracing | kprobe / kretprobe / uprobe / tracepoint / fentry / fexit | あらゆる関数 entry/exit |
| Networking | XDP / TC ingress/egress / cgroup_skb / sock_filter | パケット処理 |
| Security | LSM (BPF_PROG_TYPE_LSM, 5.7) | アクセス制御フック |
| Storage | block I/O tracepoint | I/O 監視 |
| Scheduling | **sched_ext** (6.12, 2024) | スケジューラ完全置換 |
| HID/USB | HID-BPF (6.3) | デバイスドライバ補正 |

`fentry/fexit` (5.5) は trampoline 経由で**通常の C 関数呼び出しと同じオーバーヘッド**しかなく、kprobe より桁違いに高速。

### BPF Maps — kernel/user 共有のデータ構造
eBPF プログラムは**ステートレス**（呼び出し間で変数を保持しない）。永続データは map に置く。種類:

- **Hash / Array / LRU Hash**: 通常の連想配列
- **Per-CPU 変種**: ロックなし、CPU毎に独立カウンタ→集約読出時に合計
- **Ring Buffer (BPF_MAP_TYPE_RINGBUF, 5.8)**: kernel→user の高速イベント送信。Andrii Nakryiko 設計。**64-core ノードでも7%以下のオーバーヘッド**で `perf_event_array` を駆逐。
- **Sockmap / Sockhash**: ソケット FD を格納し redirect/sockops で利用、Cilium L4 LB の心臓部
- **Stack / Queue**: FIFO/LIFO セマンティクス
- **BPF Arena (BPF_MAP_TYPE_ARENA, 6.9, 2024)**: kernel と user 空間で**共有メモリページ**を直接マップ、グラフ・連結リストのような複雑データ構造を BPF 内で組める。前来 BPF プログラムは map API しか使えず、グラフ走査が困難だった——これを解消。

### CO-RE (Compile Once – Run Everywhere)
かつては**カーネルバージョンごとに BPF を再コンパイル**する必要があった——kernel struct のフィールド offset が版によって変わるため。BCC は libclang を埋め込み、ターゲットマシンで JIT コンパイルしていた（重く、開発依存も大きい）。**Andrii Nakryiko の CO-RE** はこれを覆した:

- カーネルが **BTF (BPF Type Format)** を `/sys/kernel/btf/vmlinux` に出力
- BPF プログラムは clang `-target bpf -g` で BTF 付きで一度ビルド
- libbpf がロード時に**ターゲットカーネルの BTF と照合し、フィールドアクセス命令を relocate**
- CONFIG_DEBUG_INFO_BTF=y がディストリ標準（Ubuntu 20.10+, Fedora 32+, Amazon Linux 2 backport, RHEL 9）

これにより eBPF は「**カーネルバージョン間で配布可能なバイナリ**」になった。Cilium / Tetragon / Falco / Pixie の業界採用爆発の前提条件。

### sched_ext — スケジューラごと差し替える
2024年の Linux 6.12 にマージされた **sched_ext** (David Vernet, Meta) は、CFS や EEVDF の代替スケジューラを **BPF で書ける**ようにした。`SCX_OPS_*` ヘルパ群を実装した BPF プログラムをロードすると、Linux のタスクスケジューリング決定が **ユーザ空間からロード可能なコードへ完全に委譲**される。意義は3点:

1. **実験コスト**: 新スケジューラを試すのにカーネル再ビルド・再起動不要
2. **ワークロード特化**: ゲーミング向け **scx_lavd**（レイテンシ最適化、Valve Steam Deck）、データセンター向け **scx_layered**（Meta、ジョブクラス間で CPU 隔離）
3. **教育**: Operating Systems コースで実機で観察可能

Linux Plumbers Conference 2025 では GPU 認識・energy-aware 抽象化が議論され、2026年に拡張予定。**sched_ext は eBPF が「カーネルのプログラマビリティそのものを商品化した」象徴**。

### BPF Token — 非特権 eBPF への扉
従来 eBPF プログラムロードには `CAP_BPF` + `CAP_PERFMON`/`CAP_NET_ADMIN` 等の root 級 capability が必要だった。コンテナ環境では**特権コンテナ強制**で攻撃面が拡大していた。**BPF Token (6.9)** は、特権プロセスが「**この種類の BPF をこの程度ロードしてよい**」という制限付きトークンを発行し、非特権プロセスがそれを受け取って指定範囲の eBPF を実行できる仕組み。**delegation モデル**であり、Kubernetes Pod がノードの kube-bpf-controller からトークンを受領、Pod 内のオブザーバビリティエージェントがそれで eBPF を起動する設計が進む。

### Cilium — eBPF が変えた Kubernetes ネットワーキング
**Cilium** (Isovalent → Cisco 2023年買収、CNCF Graduated) は K8s ネットワーキングの本番実装。革命の核:

- **iptables → BPF マップ**: NetworkPolicy 評価が **O(n) → O(1)**。1万 Pod のクラスタで kube-proxy が秒単位だった処理をマイクロ秒に。
- **kube-proxy 置換**: Service IP 解決を XDP/TC で行い、Linux conntrack を介さない高速 LB
- **Cilium 1.19 (2026年)**: IPsec/WireGuard ストリクトモード、Hubble (eBPF ベース可観測性) のフル統合、Ztunnel 統合（Istio Ambient mesh の sidecar-less 実装）

採用は 2025 年時点で AWS EKS / Azure AKS / Google GKE / Alibaba ACK の**全主要マネージド K8s でデフォルトまたは選択肢**となり、**本番運用クラスタの 60% 以上**が Cilium を採用との Tigera 調査。

### XDP — NIC 直後でのパケット処理
**eXpress Data Path** は network device driver の RX 直後（skbuff 確保前）にフックする極限の早期処理。Cloudflare は 2023 年に DDoS 緩和に XDP を採用し、**3.8 Tbps 攻撃を自動緩和、秒速1,000万パケットドロップ**。Facebook の Katran L4 LB、Google の Maglev 後継 SLB も XDP ベース。

### Falco / Tetragon / Beyla / Pixie — 観測性スタック
- **Falco** (CNCF Graduated): syscall を eBPF で監視、**10,000+ events/sec を CPU 5%未満**で処理。Kubernetes 監査の業界標準。
- **Tetragon** (Cilium プロジェクト): 高レベル YAML ポリシー → eBPF エンフォースメントコードへ変換、**カーネル内リアルタイム強制**
- **Grafana Beyla → OBI (OpenTelemetry eBPF Instrumentation)**: 2024年 Grafana が CNCF に寄贈、OpenTelemetry のゼロ計装エージェントとして 2026年 1.0 目標
- **Aya (Rust)**: Rust 所有権 + eBPF 安全性モデルが噛み合い、エコシステム拡大中

## 気づき・洞察

### 「カーネルを修正せず拡張する」設計哲学
Linux カーネルは Linus の頑強な品質ゲートで「**新機能は upstream に時間がかかる**」歴史的問題を抱えていた。eBPF は逆方向の解決——**カーネルそのものは安定させたまま、特定フックポイントに動的コードを注入**。これは Bell Labs が UNIX 時代に試みたカーネルモジュールの極限拡張だが、verifier による安全保証が決定的に違う。**カーネル拡張の歴史におけるパラダイムシフト**。

### Verifier = 制約の受容が自由を生む
eBPF が安全な理由は「賢い静的解析」ではなく「**解析可能な範囲しか許さない**」設計。bounded loop、有限ヘルパ、型付きポインタ。これは Rust の所有権が「全ての並行処理を扱う」のでなく「**安全に書ける範囲を強制する**」のと同じ。**形式手法の現実的勝利**は、問題自体を解析可能領域に収めることで起きる。CRDT が SEC を諦めず可換律で済む操作だけ扱うのと同じ哲学。

### CO-RE = ABI なきカーネルへの ABI
Linux カーネルは伝統的に「**ユーザ空間 ABI は安定、カーネル内部は流動**」を貫いてきた。これがカーネルモジュールエコシステムを破壊し、out-of-tree ドライバの宿命的な保守困難を生んだ。CO-RE は「**field-level ABI**」を BTF というメタ情報経由で提供する妥協点。カーネルの自由度を保ちつつ拡張性を提供する設計の傑作。

### sched_ext は OS の商品化を示す
スケジューラはかつて「OS の心臓」であり、研究と本番は別世界だった。sched_ext で「**Steam Deck はゲーム向けスケジューラ**」「**Meta は社内スケジューラ**」という多元化が現実に始まった。**OS 単一性の終焉**——OS は基底 API を提供し、上層のポリシーは workload owner が定義する時代。これはマイクロカーネル思想の遅延した勝利でもある。

### 攻撃面の二面性
カーネル境界をプログラマブルにすることは**攻撃面拡大**そのもの。verifier バグは即 LPE。**CVE-2024-26581** (nftables BPF) や 2025 年 sched_ext 周辺の verifier escape 報告は、eBPF を「特権で動くサンドボックス」と再認識させる。Google が io_uring を全面停止した判断（前日学習）と対照的に、eBPF は verifier の継続改善に賭けている——どちらが正解かは履歴が決める。

## 他分野との接続

- **CS (NP完全性)**: verifier の「**全分岐を抽象解釈**」は計算量爆発の典型。bounded loop と命令数上限で**問題を解析可能領域に収める**設計は、NP困難を回避するヒューリスティクスと同じ思想
- **CS (Hindley-Milner型推論)**: BPF verifier の `bpf_reg_state` による型・範囲推論は、HM が型を伝播するのと相同。**プログラム検証は型システムの一般化**
- **tech (io_uring)**: 両者ともユーザ・カーネル境界を共有メモリで貫通する設計。eBPF で SQE を処理する `IORING_OP_BPF` 提案は両者の収斂を示唆
- **anatomy (基底核と手続き記憶)**: sched_ext の「ポリシーをプラグイン化」は、基底核が習慣的運動パターンを大脳皮質から分離する構造に類比——**OS の自動化された判断**を切り出して可塑化する
- **golf (ランダム練習)**: sched_ext で複数スケジューラを切替実験する開発体験は、golf のランダム練習と同じ**文脈間切替の認知効果**を再現する
- **bread (Detmolder Verfahren)**: eBPF プログラムの段階的精緻化（小プログラム→検証→チェーン化）は、ライ麦の3段階発酵と同じ **段階別パラメータ調整**の思想

## 次に深掘りしたいこと
- **bpftrace** の DSL 実装と awk-like スクリプトの内部表現
- **scx_layered / scx_rusty** の実装読解と独自スケジューラの試作
- **eBPF on Windows** (Microsoft) のアーキテクチャ差異と互換性レイヤ
- **HID-BPF** での周辺機器ドライバ補正の実例 (PS5 DualSense, Apple Magic Trackpad)
- **PREEMPT_RT + eBPF** の相互作用——リアルタイム保証下での verifier 制約
- **eBPF を WASM で書く試み** (Pyroscope の WASM-as-source) と二段階 IR のメリット

## 参考ソース
- Linux カーネル文書, "BPF Verifier": https://docs.kernel.org/bpf/verifier.html
- ebpf.io 公式, "What is eBPF?": https://ebpf.io/what-is-ebpf/
- Andrii Nakryiko, "BPF CO-RE Reference Guide": https://nakryiko.com/posts/bpf-core-reference-guide/
- David Vernet, "sched_ext: a BPF-extensible scheduler class" (LPC 2023): https://lpc.events/event/17/contributions/1454/
- eunomia, "eBPF Ecosystem Progress in 2024–2025": https://eunomia.dev/blog/2025/02/12/ebpf-ecosystem-progress-in-20242025-a-technical-deep-dive/
- LWN, "BPF tokens and delegation": https://lwn.net/Articles/947173/
- LWN, "BPF Arena": https://lwn.net/Articles/961593/
- Cloudflare blog, "L4Drop: XDP DDoS Mitigations": https://blog.cloudflare.com/l4drop-xdp-ebpf-based-ddos-mitigations/
- Cilium docs: https://docs.cilium.io/
- McCanne & Jacobson, "The BSD Packet Filter" (USENIX 1993): https://www.tcpdump.org/papers/bpf-usenix93.pdf
