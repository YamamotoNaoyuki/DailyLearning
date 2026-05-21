# WebGPUとブラウザGPUコンピューティング
**日付**: 2026-04-22
**分野**: tech
**タグ**: #WebGPU #GPGPU #WGSL #ブラウザ #並列計算

## 学んだこと

### WebGPUの位置づけ
WebGPUはWebGLの後継として策定された、モダンGPUをブラウザから直接扱うためのW3C仕様である。2024年にGAとなり、2026年時点ではmacOS Tahoe 26 / iOS 26 / iPadOS 26 / visionOS 26に加え、Chrome・Firefoxの主要ブラウザで標準サポートされる。WebGLがOpenGL ES 2.0の薄いラッパーだったのに対し、WebGPUはVulkan / Metal / Direct3D 12といった「明示的(explicit)」ネイティブAPIの共通抽象として設計されている。

### 設計思想：「明示的」APIの思想輸入
WebGLはドライバに多くの暗黙的な状態管理・ハザード検出を任せていたため、アプリケーション側は「描画コマンドがいつ発行され、どのリソースが競合しうるか」を制御できなかった。WebGPUは次の点で明示性を取り戻す：
- **コマンドバッファ方式**: GPU命令は `GPUCommandEncoder` に一旦記録され、`GPUQueue.submit()` で明示的にディスパッチされる。JS側のDrawCallオーバーヘッドをまとめて減らせる。
- **バインドグループ(Bind Group)**: シェーダが参照するバッファ/テクスチャ/サンプラをあらかじめ束ねて定義する。WebGL時代の「毎フレームuniform設定」のコストを消せる。
- **パイプラインステートオブジェクト(PSO)**: シェーダ+頂点レイアウト+ブレンド状態をまとめてコンパイルしておき、描画時は切り替えるだけ。ドライバの再コンパイルを避ける。

### WGSLというシェーダ言語の選択
WebGPUはGLSLを捨て、**WGSL (WebGPU Shading Language)** を新規定義した。Rust風の静的型と明示的なメモリアドレス空間を持つ：
```wgsl
@group(0) @binding(0) var<storage, read_write> data: array<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    data[gid.x] = data[gid.x] * 2.0;
}
```
- 理由は **セキュリティと移植性**。SPIR-VをそのままWebに持ち込むと、ブラウザ側でSPIR-Vの全挙動を安全に検証する負担が大きい。WGSLを経由させて、各実装(Chrome Dawn, Firefox wgpu)がMetal/Vulkan/D3D12シェーダに変換する。
- `storage` / `uniform` / `workgroup` / `private` / `function` といったアドレス空間が型に現れ、GPUのメモリ階層を言語レベルで露出する。

### コンピュートシェーダとGPGPUの実用化
WebGPUは「計算だけ」のパスも第一級市民として扱う。`GPUComputePipeline` + `dispatchWorkgroups(x, y, z)` で数千〜数万のワークグループを並列起動する。これがブラウザAI推論の基盤になっている：
- **ワークグループ**: 同一ワークグループ内のスレッドは共有メモリ(`workgroup`アドレス空間)とバリア同期が使える。GEMM(行列積)のタイル化に不可欠。
- **SIMDグループ(サブグループ)**: 2026年の拡張でサブグループ操作が標準化に近づき、ワープ単位のreduction/scanがWGSLから直接呼べる。これで注意機構(attention)のソフトマックスを高速化できる。
- Q2 2026の実測で、WebGPU実装はWebGLに対して計算集約的タスクで3〜5倍の性能を出す。

### AI推論の民主化
ブラウザAI文脈で最大のユースケースは**ローカルLLM/画像生成モデル**。WebLLM・Transformers.jsなどのライブラリはWebGPU経由で数GBのモデル重みをGPU VRAMにロードし、ユーザーのマシン上で推論する。サーバコストもユーザーのプライバシーも改善される。これは「モデル推論をエッジに寄せる」というパラダイムの決定打になった。

## 気づき・洞察

**Web技術の「透明性から明示性への回帰」が明確に出ている**。HTTP/1.1の暗黙的コネクション管理 → HTTP/2のストリーム明示化、WebGLの暗黙的state machine → WebGPUの明示的コマンドエンコーダ、JSのGC任せ → WebAssemblyでの線形メモリ…。Webプラットフォームは成熟するにつれ、パフォーマンスとセキュリティの両立のため「抽象の薄皮を剥がしてアプリに制御権を渡す」方向に動いている。これは「抽象化=善」という素朴な信念の逆を行く。

**「ブラウザが最強のAI推論ランタイムになる未来」が見えてきた**。WebGPUは単なるグラフィクスAPIではなく、「ユーザーのGPUに安全にアクセスする標準」である。ブラウザはサンドボックス・UI・ネットワーク・GPU・ストレージ(OPFS)をひとつのランタイムで持つ。これは実はOSが持っていた機能の超集合に近い。

**WGSLの選択は政治的でもある**。SPIR-Vを採用すればVulkan/OpenCLの既存エコシステムと直結できたが、Appleの参加とセキュリティ要件のため独自言語になった。これは過去のJSの歴史と似ている：「全員が譲歩する新言語」が結局標準化を成し遂げる。

## 他分野との接続

- **cs(分散システム)**: WebGPUのコマンドバッファは、分散システムのログ先行書き込み(WAL)と構造が似ている。「状態変更を直接適用せず、一旦イベントとして記録→後でatomicに適用」。イベントソーシング/CQRSの思想がGPUパイプラインにも現れる。
- **piano(演奏技法の並列制御)**: ワークグループ内のスレッド同期は、両手で異なるリズムを刻むポリリズムの制御に似ている。どちらも「独立に動くが特定のポイントで同期する」という構造。
- **anatomy(固有受容覚)**: GPUが同期的CPUから非同期的に動くように、小脳による運動制御も意識から独立して動く。「上位レイヤーは仕様だけ渡す、下位は自律実行」というレイヤー分離が共通。

## 次に深掘りしたいこと

- WGSL v1.0 以降の拡張仕様(subgroups / f16 / indirect dispatch)の実装状況
- WebGPU上でのFlash Attention実装の実性能
- WebNN APIとWebGPUの棲み分け(高レベルニューラルネットAPI vs 汎用計算)
- Dawn(Chrome)とwgpu(Firefox/Rust)の実装差の詳細

## 参考ソース
- [W3C WebGPU Specification](https://www.w3.org/TR/webgpu/) - 公式仕様
- [WebGPU Explainer](https://gpuweb.github.io/gpuweb/explainer/) - 設計思想
- [Get started with GPU Compute on the web (Chrome for Developers)](https://developer.chrome.com/docs/capabilities/web-apis/gpu-compute) - コンピュートシェーダ入門
- [WebGPU API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API) - リファレンス
- [WebGPU is now supported in major browsers (web.dev)](https://web.dev/blog/webgpu-supported-major-browsers) - 対応状況
