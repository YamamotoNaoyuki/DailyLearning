# eBPFとLinuxカーネル可観測性 — Verifier・BTF・CO-RE
**日付**: 2026-05-08
**分野**: tech
**タグ**: #eBPF #Linux #observability #kernel #BTF #CO-RE

## 学んだこと

### eBPFの本質：カーネルをプログラム可能にする「サンドボックス」
eBPF (extended Berkeley Packet Filter) は、Linuxカーネル内部で**ユーザー定義のコードを安全に実行する仮想マシン**である。元々は1992年のBPFがパケットフィルタリング専用であったのを、Alexei Starovoitovらが2014年に汎用化したもの。今では「eBPF」はネットワーキング、トレーシング、セキュリティ、スケジューラ拡張までカバーする。

カーネルモジュールとの違いが本質：
- **カーネルモジュール**: カーネル空間で何でもできる（=何でも壊せる）。クラッシュ=システム停止
- **eBPF**: 検証器(Verifier)が**事前に**プログラムの安全性を数学的に証明してからJITコンパイル → 暴走しない

これは「サンドボックスをカーネル内部に持ち込む」という発想で、Cloudflareのネットワーク処理、Metaのプロファイリング、Ciliumのコンテナネットワーキング、Pixie/Datadog/Parcaの可観測性製品の基盤になっている。CNCFの2026年Q1レポートではeBPFベースソリューションのproduction採用が前年比300%増。

### Verifier — eBPF安全性の核心
Verifierは**ロードされたBPFバイトコードを実行前に静的解析**し、以下を保証する：
- **終了性**: ループは有限ステップで必ず終わる（古くは無限ループ禁止、近年はbounded loopsをサポート）
- **メモリ安全性**: ポインタ算術が許可されたメモリ領域内に収まる
- **型安全性**: ヘルパー関数の引数型が一致

Verifierは抽象解釈（Abstract Interpretation）でレジスタの値域を追跡する。例えば「このポインタは map_lookup_elem の戻り値で NULL かもしれない」を認識し、NULL チェックなしで dereference するコードを reject する。

実用上のハマりどころ：
- ポインタ算術には事前 bounds check が必須（`if (ptr + N > end) return 0;` を必ず書く）
- 制御フローが複雑すぎると "verifier complexity limit" エラー
- 大きなループは展開（unroll）するか、`bpf_for_each_map_elem` のようなhelper経由で

### BTF (BPF Type Format) — カーネル内蔵の型情報
BTFは**カーネルのデータ構造（struct/enum等）の型情報をカーネル自身に埋め込む**フォーマット。`/sys/kernel/btf/vmlinux` で公開されており、実行中のカーネルがどんな型を持っているかをBPFプログラムが照会できる。

DWARFと違うのは「軽量・カーネル内アクセス前提」設計。サイズはvmlinuxで数MB程度で、カーネルバイナリと同梱可能。

### CO-RE (Compile Once, Run Everywhere) — eBPFの最大の進化
従来のBCCツール群は **ターゲットマシン上でカーネルヘッダから再コンパイル** していた（Clang/LLVMをサーバー全台にインストール…）。

CO-REは：
1. BPFプログラムを開発マシンで一度だけClangコンパイル
2. ELFに**型参照を「再配置可能」な形で残す**（`__builtin_preserve_access_index`）
3. 実行時、libbpfが**ターゲットカーネルのBTFと突き合わせて**フィールドオフセットを書き換え

これにより「同じバイナリが kernel 5.4 と 6.1 と 6.6 で動く」が実現。kernel struct のフィールドが追加されてもオフセットが変わるだけなのでCO-REが吸収する。

### プログラムタイプとアタッチメント
代表的なフックポイント：

| 種類 | 場所 | オーバーヘッド | 安定性 |
|------|------|---------------|--------|
| **Tracepoint** | カーネル内の静的フック点 | 低（未使用時ゼロ） | 安定（ABI維持） |
| **Kprobe** | 任意のカーネル関数 | 中（debug exception） | 不安定（関数名で結合） |
| **Fprobe** | 関数entry（ftrace経由） | 低（NOP→trampoline） | 不安定 |
| **Uprobe** | ユーザー空間関数 | 高（context switch） | 不安定 |
| **XDP** | NICドライバ層 | 極低（パケット到着直後） | 専用 |

XDPは**カーネルのネットワークスタックに入る前**にパケットを処理できる。これによりCloudflareのDDoS緩和（数百Gbps）が可能になっている。

### 実装上のベストプラクティス
- 可能な限り**Tracepoint > Fprobe > Kprobe**の順で選ぶ（安定性重視）
- BPF mapはユーザー空間とのデータ共有チャネル。Per-CPU mapでロックフリーに
- ring buffer（BPF_MAP_TYPE_RINGBUF）が新しいイベント転送方式（perf bufferより効率的）
- 2026年現在、kernel 6.1+が production推奨（Ubuntu 24.04, Amazon Linux 2023, Bottlerocket）

## 気づき・洞察

eBPFの設計思想は「カーネル開発の民主化」だ。従来、カーネル機能を拡張するには (1) 上流にパッチを送る、(2) カーネルモジュールを書く、しかなかった。前者は数年かかり、後者は危険すぎる。eBPFは**「両者の中間」を制度化**した。

Verifierは「形式手法（formal methods）の実用例」として最も成功しているもののひとつだろう。完全な証明ではないが、抽象解釈で十分な安全性保証を達成している。これは**信頼境界をどこに置くか**の見本。OS内部にコードを動的注入できる、という機能の代償として、Verifierという「番人」が必要だった。

CO-REは「**ABIではなくBTFで結合する**」というパラダイムシフト。従来のC ABIは「コンパイル時のヘッダと実行時のカーネルのバイナリ互換」を要求するが、CO-REは「実行時に構造をマッチング」する。これはJVMやCLRが解決した問題（プラットフォーム独立性）をネイティブコードで再発見した形。

「**安全性 × 性能 × 動的拡張性**」を三つ巴で満たすのが難しいから、kernel hacking はこれまで「危険な専門家の領域」だった。eBPFはその三角形を初めて崩した。今やrate limiter, packet capture, syscall tracing, security policy enforcement が全部 eBPF で書ける。

## 他分野との接続

- **CS (Verifier = abstract interpretation)**: VerifierはRice's theorem（停止性は決定不能）の壁を、保守的な抽象化で回避している。ZGCが colored pointer の上位ビットでGC状態を持たせるのと類似で、「**型システム/静的解析を実装の制約として活用する**」設計
- **CS (CO-RE = late binding)**: 関数オーバーロードの動的ディスパッチ、JVMのインライン化、CO-REのフィールドオフセット解決はすべて「実行時情報による特殊化」
- **piano (slow practice = verifierの抽象解釈)**: 演奏前にゆっくり弾いて運指の安全性を検証するプロセスは、Verifierが実行前にbytecodeを抽象解釈で安全性証明するプロセスに似ている
- **bread (sourdough microbiome = カーネル subsystem の協調)**: Lactobacillusとyeastが代謝経路を分担して安定発酵を実現するのは、eBPFのprogram typesが各サブシステム（NET/TRACE/CGROUP）で役割分担して可観測性を実現する構図に近い

## 次に深掘りしたいこと

- BPF schedulers (sched_ext): Linux 6.12でmainline化された、eBPFでカーネルスケジューラを書ける機能
- bpfilter: iptables/nftablesをeBPFで再実装する話
- Verifier の内部実装（register state tracking、bounds analysis）の詳細
- BPF Type Format の deduplication アルゴリズム

## 主要参考ソース

- [What is eBPF? An Introduction (ebpf.io)](https://ebpf.io/what-is-ebpf/) — Tier 1: 公式
- [Linux eBPF Tracing Tools - Brendan Gregg](https://www.brendangregg.com/ebpf.html) — Tier 1: Netflix Senior Performance Architect、業界権威
- [eBPF Tracepoints, Kprobes, or Fprobes - iximiuz Labs](https://labs.iximiuz.com/tutorials/ebpf-tracing-46a570d1) — Tier 2: 専門家解説
- [How to Build Portable eBPF Programs with CO-RE](https://oneuptime.com/blog/post/2026-01-07-ebpf-core-portable-programs/view) — Tier 2: 実装解説
