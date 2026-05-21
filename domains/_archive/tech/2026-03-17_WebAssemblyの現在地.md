# WebAssembly（Wasm）の現在地 — ブラウザ外への拡張とWASI
**日付**: 2026-03-17
**分野**: テクノロジー
**タグ**: #WebAssembly #WASI #Wasm #サーバーレス #コンポーネントモデル

## 学んだこと

### Wasmの設計思想と原点

WebAssembly（Wasm）は2017年にW3C標準として登場した**バイナリ命令フォーマット**。設計目標は4つ:

1. **ポータブル**: ハードウェア・OS非依存のバイトコード
2. **安全**: サンドボックス内で実行、ホストリソースへの直接アクセス不可
3. **高速**: ネイティブに近い実行速度（AOT/JITコンパイル）
4. **コンパクト**: バイナリフォーマットによる高効率な転送・パース

当初はブラウザ内でのC/C++/Rust実行を主目的としていたが、2026年現在、**ブラウザの外**での利用がWasmの最大の成長領域となっている。

### Wasm 3.0の主要新機能（2025年9月リリース）

- **Memory64**: 64ビットアドレス空間（4GB制限の撤廃）
- **Multiple Memories**: 複数のメモリ空間をモジュール内で管理
- **Exception Handling**: 構造化例外処理のネイティブサポート
- **WasmGC**: ガベージコレクション型（struct/array）の直接サポート——Go、Kotlin、Dartなどの言語サポートを大幅改善

### WASI — WebAssembly System Interface

WASIはWasmをブラウザ外で動かすための**システムインターフェース仕様**。POSIXに代わるWasm向けのOS抽象層。

#### WASIのバージョン進化

| バージョン | リリース | 主な特徴 |
|-----------|---------|---------|
| WASI Preview 1 | 2020年 | ファイルI/O、環境変数、時計。POSIX風の薄いラッパー |
| WASI 0.2.0 (Preview 2) | 2024年1月 | **Component Model統合**。WIT（WebAssembly Interface Types）導入 |
| WASI 0.3.0 (Preview 3) | 2026年2月頃 | **ネイティブ非同期I/O**。`stream<T>`/`future<T>`型。Wasmtime 37+で実験サポート |
| WASI 1.0 | 2026年末〜2027年初 | 安定版リリース目標 |

#### WASIが提供するAPI群

- **wasi-filesystem**: ファイルシステムアクセス
- **wasi-sockets**: TCP/UDPソケット（HTTP、TLS含む）
- **wasi-clocks**: 壁時計、モノトニック時計
- **wasi-random**: 暗号的乱数生成
- **wasi-nn**: ニューラルネットワーク推論（ML推論用）

### コンポーネントモデルとWIT

**コンポーネントモデル**はWasmの最も野心的な拡張。個々のWasmモジュールを**相互運用可能なコンポーネント**として合成するアーキテクチャ。

**WIT（WebAssembly Interface Types）** はコンポーネント間のインターフェース定義言語（IDL）:

```wit
// WITの例: プラグインインターフェース
package my:plugin@1.0.0;

interface processor {
    record input-data {
        name: string,
        value: f64,
    }
    process: func(data: input-data) -> result<string, string>;
}

world plugin {
    export processor;
}
```

これにより:
- **言語非依存の合成**: RustのコンポーネントとGoのコンポーネントを「リンク」して一つのアプリにできる
- **安全なプラグインシステム**: サンドボックス内で未信頼コードを実行。アクセスできるリソースを厳密に制限
- **型安全なFFI**: 高レベルな型（string、record、variant、list等）をWasm境界を超えて安全にやり取り

### 主要ランタイム比較

2026年初頭のベンチマークに基づく:

| ランタイム | 開発元 | メモリ | コールドスタート | スループット | 特徴 |
|-----------|--------|--------|---------------|------------|------|
| **Wasmtime** | Bytecode Alliance | 15MB | 3ms | 12,000 req/s | コンポーネントモデル実装最先端。セキュリティ重視。Craneliftコンパイラ |
| **Wasmer** | Wasmer Inc. | 12MB | 2ms | 13,000 req/s | AOT/JIT最適化。LLVM/Cranelift/Singlepass選択可。Wasmer Edgeプラットフォーム |
| **WasmEdge** | CNCF | 8MB | 1.5ms | 15,000 req/s | エッジ特化。最小フットプリント。Docker統合。TensorFlow互換レイヤー |
| **Wasm3** | — | 最小 | 最速 | 低め | インタプリタ方式。IoT/組込み向き |

Wasmtimeがコンポーネントモデル対応でリード、WasmEdgeがエッジデバイスで優位。

### エッジ・サーバーレスでの本番採用

#### Cloudflare Workers
- 330+のグローバルロケーションでWasmを実行
- マイクロ秒レベルのコールドスタート
- 2025年末に**Workers AI**を追加——Llama 2やStable DiffusionをWasm+WebGPUでエッジ推論
- V8のWasmエンジン上で動作

#### Fastly Compute
- マイクロ秒レベルのWasmインスタンシエーション
- Wasmtimeベース（Bytecode Allianceの創設メンバー）
- Rust/Go/JavaScriptでのコンパイルサポート

#### Akamai（Fermyon買収）
- 2025年12月にFermyon（Spinフレームワーク開発元）を買収
- 4,000+のグローバルエッジロケーションでWasm FaaSを展開
- SpinはCNCFオープンソースプロジェクトとして継続

**バイナリポータビリティ**の威力: 同一の`.wasm`ファイルをCloudflare Workers、Fastly Compute、Akamaiに変更なしでデプロイ可能。

### Docker + Wasm統合

Docker DesktopはcontainerdのWasm shimを通じてWasmワークロードをネイティブサポート:

```yaml
# docker-compose.yml
services:
  api:
    image: my-rust-api:latest
    runtime: io.containerd.wasmtime.v1  # Wasmランタイム指定
    ports:
      - "8080:8080"

  database:
    image: postgres:16  # 従来のLinuxコンテナ
    ports:
      - "5432:5432"
```

- **ハイブリッドデプロイ**: 同じ`docker-compose.yml`でWasmモジュールとLinuxコンテナを同時起動
- **runwasi**: containerd shimとしてWasmEdge/Wasmtime/Spinをプラグイン
- **SpinKube**: KubernetesでSpinアプリをCRDとしてデプロイ（CNCF Sandbox）

2026年の戦略は「置き換え」ではなく**「共存」**。コンテナは汎用インフラ基盤、Wasmは高性能・高密度コンピュートの選択肢。

### パフォーマンス — ネイティブとの比較

- **Wasm vs ネイティブ**: AOT/JITコンパイル時にネイティブの**80-95%**の実行速度
- **Wasm vs JavaScript**: 計算集約タスクで**8-10倍**高速（Rust→Wasmの場合）
- **コールドスタート**: Wasmモジュールはマイクロ秒単位。Linuxコンテナのミリ秒〜秒単位と桁違い
- **メモリ密度**: 同一ハードウェアで**10-100倍**のインスタンスを同時実行可能
- **実例**: FigmaがレンダリングエンジンをC++→Wasmに移行し、大規模ドキュメントのロード時間を**3倍高速化**

### 言語サポート（2026年現在）

| 言語 | 成熟度 | 備考 |
|------|--------|------|
| **Rust** | 最高 | `wasm32-wasi`ターゲットが最も成熟。Component Model対応。Wasm開発の第一選択 |
| **C/C++** | 高 | Emscripten（ブラウザ向け）、Clang standalone（WASI向け） |
| **Go** | 高 | TinyGo推奨（標準GoランタイムはWasmサイズが大きい）。WASI対応 |
| **Python** | 中 | Pyodide（ブラウザ）、ComponentizeをComponent Model対応で開発中 |
| **C#/.NET** | 中 | Blazor WebAssembly。NativeAOT-LLVM経由でWASI対応 |
| **Kotlin** | 中 | WasmGC利用。Kotlin/Wasmが公式サポート |
| **Swift** | 初期 | SwiftWasm。Component Model対応は進行中 |

40+言語がWasmにコンパイル可能だが、**Rust/C/C++が本番品質**、Go/Pythonは急速にキャッチアップ中。

### セキュリティモデル — ケイパビリティベースセキュリティ

Wasmのセキュリティは**コンテナとは根本的に異なるアプローチ**:

| 観点 | コンテナ | Wasm |
|------|---------|------|
| 分離メカニズム | Linuxカーネル（namespaces + cgroups） | サンドボックス命令アーキテクチャ |
| デフォルト | 多くのリソースにアクセス可能 | **一切アクセス不可**（明示的付与が必要） |
| セキュリティモデル | deny-list的 | **allow-list的（ケイパビリティベース）** |
| 攻撃面 | カーネルAPI全体 | 限定的なWASI API |
| 特権昇格 | 可能性あり | 構造的に困難 |

```bash
# ケイパビリティの明示的付与の例
wasmtime run --dir /data::/data --env API_KEY=xxx my-module.wasm
# /data以外のファイルシステムにはアクセス不可
```

ただし2026年には新たな攻撃面も:
- **リニアメモリ脆弱性**: バッファオーバーフロー的な攻撃がWasm内で発生
- **JITコンパイラバグ**: JIT最適化ロジックの脆弱性によるサンドボックスエスケープ

### WasmとAI推論

- **wasi-nn**: WASI標準のニューラルネットワーク推論API。バックエンドにOpenVINO、ONNX Runtime、TensorFlow Liteを利用
- **ブラウザ内LLM**: WebLLM（MLC-AI）がWasm+WebGPUでブラウザ内LLM推論を実現。7トークン/秒（プロンプト評価）
- **エッジAI推論**: WasmEdgeのTensorFlow互換レイヤーでモデルをエッジデバイスに配布
- **SaaSのクライアントシフト**: 2025-2026年、GPU費用削減のためAI推論をWasm経由でクライアントに移すSaaS企業が増加

### Fermyon Spin — 開発者体験の革新

```bash
# Spinアプリの開発サイクル
spin new -t http-rust my-api    # テンプレートからプロジェクト生成
spin build                       # Wasmにコンパイル
spin up                          # ローカル実行
spin deploy                      # Fermyon Cloud / Akamaiにデプロイ
```

SpinはWasmツールチェーンの複雑さを抽象化し、**Docker的な開発者体験**をWasmに持ち込んだ。Matt Butcher（Fermyon CEO）は「2026年は平均的な開発者がWasmの力を実感する年になる」と発言。

## 気づき・洞察

**「Wasmはコンテナを殺す」は不正確。正しくは「Wasmはコンテナの弱点を補完する」**。コールドスタート、メモリ密度、セキュリティ粒度でWasmが優位な領域が明確になり、2026年の答えは「コンテナ OR Wasm」ではなく「コンテナ AND Wasm」のハイブリッド。

WASIの進化（Preview 1→2→3→1.0）は、**POSIXに代わる新しいシステムインターフェース標準**を作ろうとしている壮大な試み。ケイパビリティベースのセキュリティモデルは、1960年代の研究に遡る概念だが、Wasmで初めて実用的な大規模採用に至りつつある。

コンポーネントモデルは**言語間の壁を溶かす接着剤**。これまで「RustとPythonを同一プロセスで安全に合成する」ことは非現実的だったが、WIT+コンポーネントモデルがそれを実現しようとしている。

## 他分野との接続

- **ピアノ演奏/音楽**: ブラウザ内でのリアルタイムオーディオ処理にWasmが使われている。Web Audio APIとWasmの組み合わせで、シンセサイザーやエフェクターをブラウザ内にネイティブ品質で実装可能
- **AI/エージェント（techドメイン内）**: MCPサーバーをWasmコンポーネントとしてパッケージングする構想がある。ケイパビリティベースセキュリティはエージェントの権限管理と親和性が高い（Bounded Autonomyの実装基盤として有望）
- **哲学**: 「一つの言語に縛られない」というWasmの設計思想は、多元主義的な哲学観と通じる。一つの正解（言語）を押し付けず、多様性を受け入れつつ共通基盤で統合する
- **パン**: 標準化（WASI=レシピの標準化）と、環境に応じた適応（ランタイム=各オーブンの特性に合わせた焼き方）の二層構造は、パン作りの構造と相似的

## 次に深掘りしたいこと

- **SpinKubeの実践**: KubernetesでWasmワークロードを運用する具体的なアーキテクチャパターン
- **コンポーネントモデルの実装詳細**: cargo-componentでRustコンポーネントを作り、WITで合成する実践的手順
- **WASI 0.3の非同期モデル**: `stream<T>`/`future<T>`の実装と、既存の非同期ランタイム（Tokio等）との関係
- **Wasm + Confidential Computing**: Intel SGX/TDXとの組み合わせによる機密Wasm実行
- **WASIXとWASI Preview 2の競合**: Wasmer独自拡張のWASIXがWASI標準にどう影響するか
- **MCP × Wasm**: MCPサーバーをWasmコンポーネントとして配布・実行するアーキテクチャの可能性
