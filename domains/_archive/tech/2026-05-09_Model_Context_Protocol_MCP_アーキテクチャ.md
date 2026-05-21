# Model Context Protocol (MCP) アーキテクチャ
**日付**: 2026-05-09
**分野**: tech
**タグ**: #MCP #LLM #JSON-RPC #LSP #AgenticAI

## 学んだこと

Model Context Protocol（MCP）は2024年11月にAnthropicが公開した、LLMアプリケーションと外部データ・ツールを接続するための**オープン標準**である。一年余りで業界標準化が進み、2025年12月にAnthropicはMCPをLinux Foundation傘下の「Agentic AI Foundation」に寄贈した。Block, OpenAI, AWS, Google, Microsoftなどが創設メンバーに名を連ね、もはや一企業のプロトコルではなく**AIエージェント時代の共通インフラ**となった。

### LSPの設計思想を踏襲したアーキテクチャ

MCPの根本的なアイデアは、Microsoftが開発エディタ向けに作った**Language Server Protocol（LSP）**から来ている。LSPは「エディタごと×言語ごとのN×Mの組み合わせ爆発」を「N+M」に圧縮した。MCPも同様に、「LLMクライアントごと×ツールごと」のN×Mを「N+M」にする。

クライアント（Claude, ChatGPT, Cursor, VS Code等）はMCPサーバーに対し**JSON-RPC 2.0**で双方向接続を開く。サーバーはツール（関数呼び出し可能な機能）、リソース（ファイル・DB等の読み取り可能なコンテキスト）、プロンプトテンプレートの3種を公開する。クライアントは標準化された方法でこれらを発見し（`tools/list`）、呼び出す（`tools/call`）。

### トランスポート層の進化

初期MCPは`stdio`（ローカルプロセス間）と`HTTP+SSE`（Server-Sent Events）の2つのトランスポートを持っていたが、SSEは単方向ストリームのため、サーバー→クライアントの通知に問題があった。2025年仕様で**Streamable HTTP**が導入され、単一のHTTPエンドポイントで双方向ストリーミング・再接続・セッション復元が可能になった。これによりServerless環境（Cloudflare Workers, AWS Lambda）への展開が現実的になった。

### 2025-11-25仕様の重要機能

- **Tasks**: 長時間タスクの抽象化。リクエストにtaskを付与すると、クライアントは後でステータス照会と結果取得ができる。サーバー定義のTTL内で結果が保持される。これは「8分かかるビルド」のようなケースで、HTTP接続を保ち続ける必要がなくなる。
- **OAuth 2.1ベースの認可フレームワーク**: 動的クライアント登録（RFC 7591）、PKCE強制、リソースメタデータ（RFC 9728）を組み込み、エンタープライズSSOとの統合が標準化された。
- **Elicitation**: サーバーがクライアント経由でユーザーに追加情報を求められる。「どのGoogleカレンダーを使う？」のような対話的なフローが可能。
- **Sampling**: サーバーがクライアント側のLLMに推論を依頼できる。サーバーが自前のLLMを持つ必要がなくなる。

### 採用規模

Python・TypeScriptのSDKは月間9700万ダウンロード、稼働中のサーバーは1万以上。Claude, ChatGPT, Cursor, Gemini, Microsoft Copilot, VS Codeでファーストクラスのクライアントサポート。

## 気づき・洞察

MCPの本質は「**エージェント時代のIPC（プロセス間通信）プロトコル**」である。OSがプロセス間通信を標準化したからこそマルチプロセス・マイクロサービス時代が来たように、MCPはLLMが外部世界とやり取りする方法を標準化する。これにより、各ツール開発者は一度MCPサーバーを書けば、すべてのMCPクライアントから使える。

特に注目すべきは**LSPからの設計借用**だ。LSPは10年以上の実戦で「JSON-RPC 2.0は冗長だが拡張容易で実装簡単」「双方向通知は重要」「言語ごとに能力宣言（capability negotiation）が必要」といった教訓を蓄積していた。MCPはこれらを丸ごと継承することで、初期から堅牢な設計になっている。LSPが「過去の遺産」ではなく「未来への種」だったことを示す好例。

OpenAIの「Function Calling」が独自仕様だったのに対し、MCPがオープン標準として採用された理由は、**プロトコル戦争を避ける合理性**だった。各ベンダーが独自規格を持つと、ツール開発者の負担が増え、エコシステムが断片化する。AnthropicがMCPを公開したことで、競合他社（OpenAI, Google, Microsoft）も「自社規格で囲い込むより、共通規格で参加した方がエコシステム全体が育つ」と判断した。

## 他分野との接続

- **CS（Lamport論理時計, HLC）**: MCPのTask機能は分散系の非同期処理パターン。クライアントがタスクIDで状態を追跡する設計は、メッセージング・キューの概念に近い。
- **CS（Curry-Howard対応）**: MCPの型付きスキーマ（JSON Schema）はLLMが「正しい引数」を構成する手助けをする。型は推論の制約条件。
- **音楽（楽譜と演奏の関係）**: 楽譜がプロトコルで、演奏者と作曲者の通信規約。MCPも「LLMが世界と話す」ための楽譜記法。
- **解剖学（小脳と内部モデル）**: 小脳が運動の内部モデルを構築するように、MCPサーバーは「ツールの内部モデル」をLLMに提供する。

## 次に深掘りしたいこと

- MCPサーバーを自作してClaude Codeと接続する実践
- Streamable HTTPのセッション管理と復元の内部実装
- MCPセキュリティ：プロンプトインジェクション・confused deputy問題への対策（特に2025年に話題になったMCPサーバー経由の攻撃事例）
- A2A（Agent-to-Agent）プロトコルとMCPの位置づけの違い

## 主要参考ソース

- [Specification - Model Context Protocol (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [One Year of MCP: November 2025 Spec Release](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)
- [Introducing the Model Context Protocol - Anthropic](https://www.anthropic.com/news/model-context-protocol)
- [Why the Model Context Protocol Won - The New Stack](https://thenewstack.io/why-the-model-context-protocol-won/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol/modelcontextprotocol)
