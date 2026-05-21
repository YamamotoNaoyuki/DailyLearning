# WebAssembly Component Modelとポリグロット合成
**日付**: 2026-04-30  
**分野**: テクノロジー  
**タグ**: #wasm #ComponentModel #WIT #WASI #CanonicalABI #BytecodeAlliance

## 学んだこと

### Component Modelが解決する「Wasmの3つの欠陥」

Wasm Core (1.0/2.0) は**32ビット線形メモリ + 数値型のみ + 単一モジュール = 単一空間**という設計だった。これは「ブラウザJSサンドボックス内の高速計算カーネル」としては完璧だが、サーバ・エッジでポリグロットなコンポーネント合成を目指すと3つの構造的欠陥に突き当たる：

1. **型が貧弱**: `i32 / i64 / f32 / f64` だけ。文字列もリストも構造体も「線形メモリ上のバイト列＋ポインタ＋長さ」を呼び出し規約で合意するしかない。Rust↔Goで `String` をやり取りするだけで、両言語のメモリレイアウト・所有権・GC仮定が衝突する。
2. **メモリが共有**: モジュールAがモジュールBの線形メモリを書き換え可能。「ライブラリを直接リンク」と同じ脅威モデル。サードパーティ・プラグインを安全にロードできない。
3. **動的合成不可**: WIT以前は「どんなインターフェースを公開しているか」を機械可読に表現する手段がなく、ホスト言語ごとの ad-hoc バインディングが必要だった。

Component Model はこの3点に **WIT (IDL) + Canonical ABI (型変換規則) + 「コンポーネントは独立した線形メモリを持ち、shared-nothing で interface 経由でのみ通信」** という三位一体で答えた。発想は OSプロセス + RPC に近いが、**プロセス境界のオーバーヘッドはなし**（同一Wasmランタイム内、関数呼び出し相当）という妙味がある。

### WIT (WebAssembly Interface Type)

WIT は Rust の trait/Go の interface に近い IDL。プリミティブに加え `record`（structure）、`variant`（tagged union, 型付き enum）、`enum`、`flags`（bitset）、`list<T>`、`option<T>`、`result<T,E>`、そして **`resource`** をサポートする。

```wit
package example:image-processor@0.1.0;

interface processor {
    record dimensions { width: u32, height: u32 }
    variant filter {
        blur(f32),
        sharpen,
        rotate(f32),
    }
    resource image {
        constructor(data: list<u8>);
        dimensions: func() -> dimensions;
        apply: func(f: filter);
        encode: func() -> list<u8>;
    }
}

world plugin {
    export processor;
    import wasi:logging/logging@0.1.0;
}
```

**resource** は Component Model の白眉だ。「外に値を渡したいが、内部表現を晒したくない」型——たとえば DB接続、ファイルハンドル、画像バッファ——を **opaque handle (i32)** として外に出し、メソッド呼び出しは Canonical ABI が handle table 経由で正しいインスタンスにディスパッチする。これは **線形型（ownership）の再発明**で、Rust のborrow checker が型システムレベルで提供したものを ABI レベルで提供している。

### Canonical ABI: 型変換の取扱説明書

Canonical ABI は WIT 型↔線形メモリのマッピングを完全に specify する。たとえば `string` は **(ptr: i32, len: i32)** に、`list<T>` も同様、`record` は **flat lowering** または **指標化された heap layout** に、`variant` は discriminant + 各 case のメモリレイアウトに——と、すべて確定的に決まっている。

呼び出し規約は2層で動く：
- **lift**: 線形メモリ上のバイト列 → WIT 型（受信側）
- **lower**: WIT 型 → 線形メモリ上のバイト列（送信側）

`canon lift` と `canon lower` は Wasm の組み込み命令で、ホストランタイム（Wasmtime等）が実行時に lifter/lowerer を生成する。**重要なのは、コンポーネントAの線形メモリとBの線形メモリは絶対に直接共有されない**こと——必ず canonical 表現を通って一旦中間バッファに展開される。これがゼロコピーには反するが、メモリ隔離による安全性を生む。WASI 0.3 で導入される `stream<T>/future<T>` は、この境界をまたいで非同期にデータを流すための新たなプリミティブ。

### Wasmtime と cargo-component の現状（2026年4月時点）

Wasmtime はBytecode Alliance の **Core Project** に昇格（2025年）し、Component Model および WASI 0.2 の参照実装として最先端を走る。WASI 0.2.11 が 2026-04-07 にリリース、WASI 1.0 が 2026年末〜2027年初頭目標。

Rust 側のツールチェーンは `cargo-component`（→ `cargo component build`）が標準で、内部的に `wit-bindgen` を呼んで WIT から Rust trait を自動生成する。Wasmtime ホスト側は `wasmtime::component::bindgen!` マクロで対応する Rust 側の型を自動派生し、**コンポーネント (.wasm) を1つのバイナリとしてロードして関数呼び出しできる**。

Cloudflare Workers/Fastly Compute/Akamai (Fermyon 買収後) などのエッジプラットフォームが Component Model を順次採用。SpinKube (CNCF Sandbox) で K8s + Wasm Component の統合が進む。Docker は containerd shim 経由でコンテナと Wasm Component の併存を実現。

### コンポーネントのコンポジション

Component Model 最大の魅力は **静的合成**。`wasm-tools compose` で複数の `.wasm` コンポーネントを **import↔export を結線して1つの新コンポーネント**にビルドできる。これにより：

- Rustで書いた image-processor.wasm
- Goで書いた storage-adapter.wasm
- Pythonで書いた ml-inference.wasm

を**ホスト言語非依存**に組み合わせ、結合後はランタイムが介在しない静的呼び出しになる。これは LLM プラグインアーキテクチャ（MCPサーバを Wasm Component で配布）への自然な道で、2026年に WASI-NN との組み合わせで**ブラウザ・エッジで隔離されたAI推論をプラグイン的に差し込む**実装パターンが立ち上がりつつある。

## 気づき・洞察

Component Model は表面的には「Wasm版のCOMやCORBA」に見えるが、本質はもっと深い。**「ABI を IDL から機械的に生成するのではなく、IDL → ABI の規則自体を canonical に固定する」**という設計判断が肝だ。COM/CORBA は IDL コンパイラの実装に各言語の ABI 詰め込みを任せた結果、互換性破綻と巨大な仕様書を生んだ。Component Model は **Canonical ABI を仕様の中核**に据えた——これは「言語間 FFI の数学的基礎」を作ろうという試み。

もう一つの本質は **shared-nothing + linear types**。Rust の借用チェッカが「単一所有権」を型で保証するように、Component Model は **resource handle を介して所有権の譲渡・借用を ABI レベルで保証**する。これは並行・分散システムの不変式（Erlang のメッセージパッシング、Pony の reference capabilities、Rust の Send/Sync）と同型。**「言語間でも同じ安全性を持ち込める」**点が革命的。

そして「ABIの canonical化」は **Nix の入力ハッシュ→出力ハッシュ関数化**と同じ哲学だ：副作用・実装依存を排除し、**入力（WIT）から出力（バイト列）への純粋関数**に持ち込むことで、合成・キャッシュ・検証が可能になる。

## 他分野との接続

- **CRDT / イベントソーシング**: Component の resource handle は「オブジェクトIDを介した状態操作の隔離」で、CmRDT の操作ベースモデルと構造的に近い。
- **Confidential Computing (CC)**: TEE が「物理的隔離」で実現する secret protection を、Component Model は「論理的隔離（線形メモリ分離）」で同じ脅威モデルに対抗する。CC + Component Model = 多層防御。
- **Passkeys / Capability-based security**: 「秘密鍵をエンクレーブに封入」と「resource handle を opaque に保つ」は、どちらも **暴露面を最小化する** 設計哲学。
- **MCP**: MCP サーバを Wasm Component として配布する未来——MCP の N×M→N+M を **ホストOS非依存に** 完成させる。これは tech 分野で繰り返される「標準化＋分離＋合成」パターンの最終形。

## 次に深掘りしたいこと

- WASI 0.3 の `stream<T>/future<T>` の Canonical ABI 上の表現と、Tokio/async-std との相互運用
- `wasm-tools compose` の依存解決アルゴリズム
- Component Model + WASI-NN によるブラウザ内LLM推論プラグインアーキテクチャ
- WebMCP との関係（WebMCP は browser navigator API、Component Model は server/edge ランタイム——統合パターンは？）
- ジェネリクス対応（現状WIT は monomorphic、ジェネリック WIT 提案 "templates" の進捗）

---

### 主要参考ソース
- [WebAssembly Component Model 公式仕様](https://github.com/WebAssembly/component-model) (Bytecode Alliance/W3C)
- [Component Model book](https://component-model.bytecodealliance.org/) (公式)
- [WASI Preview 2 Stable / 0.2.11 リリース 2026-04-07](https://github.com/WebAssembly/WASI)
- [The State of WebAssembly 2025-2026 — Platform Uno](https://platform.uno/blog/the-state-of-webassembly-2025-2026/)
- [WASI Preview 3 at the Edge (2026)](https://techbytes.app/posts/wasm-components-wasi-preview-3-edge-optimization-2026/)
