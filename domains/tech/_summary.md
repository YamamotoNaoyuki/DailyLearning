# 📚 テクノロジー・開発 分野サマリー

**最終更新**: 2026-03-07
**エントリ数**: 8

---

## 蓄積された知識
- **コンテキストウィンドウ戦略**: RAG、プロンプトキャッシング、チャンク戦略、要約の階層化
- **Lost in the Middle問題**: コンテキスト中央部の情報は見落とされやすい
- **MCP（Model Context Protocol）**: AI統合のオープンスタンダード。「AIのUSB-C」。N×M→N+M
- **MCPの現在**: Linux Foundation (AAIF) へ寄贈。OpenAIも公式採用
- **マルチエージェント6パターン**: Prompt Chaining / Routing / Parallelization / Orchestrator-Worker / Evaluator-Optimizer / Reflection
- **Orchestrator-Worker**: 動的なタスク分解が特徴。実行中に新タスク発見を想定。Claude Codeチーム機能がこのパターン
- **実運用は組み合わせ**: 単一パターンでは不十分。パターン選択でトークン使用量が200%以上変動
- **市場規模**: マルチエージェントシステム 78億ドル(2025)→520億ドル(2030)。エンタープライズの40%が2026年末にAIエージェント搭載予測
- **HITL（Human-in-the-Loop）**: 明示的な人間の承認なしに最終実行を禁止。ゲートキーパー。高リスク領域向け
- **HOTL（Human-on-the-Loop）**: 事前定義された制約内で自律動作、異常時のみ介入。戦略的スーパーバイザー
- **Bounded Autonomy**: サンドボックス＋Digital DNA（Constitutional Guardrails）＋Governance-as-code
- **EU AI Act**: 2025年8月完全適用。高リスクエージェントに人間の監督が法的義務
- **警告**: 2027年末までにエージェントAIプロジェクトの40%以上がキャンセル予測。ガバナンスの欠如が主因
- **エージェント信頼モデル**: 階層型 vs ピアツーピア vs ハイブリッド型（2025年主流）
- **FIREモデル**: 4つの信頼情報源——Interaction/Role-based/Witness/Certified
- **ゼロトラスト for AI**: 従来のIAMはエフェメラルな委任チェーンに対応不足。全インタラクションに認証・認可を要求
- **ARIA**: Agent Relationship-based Identity and Authorization。委任関係を暗号的に検証可能なグラフで管理
- **DID + VC**: 分散型識別子と検証可能クレデンシャルによる新フレームワークが登場
- **Google A2A（Agent-to-Agent）**: 2025年4月発表。異なるフレームワーク・ベンダーのAIエージェント間の相互運用プロトコル。50+パートナー
- **Agent Card**: JSON形式のケイパビリティ記述。「何ができるか」を機械可読で公開。OpenAPIスキーマに相当
- **A2A vs MCP**: 垂直（MCP: エージェント↔ツール）vs 水平（A2A: エージェント↔エージェント）。競合ではなく補完関係
- **A2A技術スタック**: HTTP + JSON-RPC + SSE。v0.3でgRPCサポート追加。Linux Foundation傘下、Apache 2.0
- **A2AとAAIF**: A2AとAI Agent Interoperability Framework（Linux Foundation）が競合的な立場に
- **ACP（Agent Communication Protocol）**: 2025年5月IBM発表。BeeAIプラットフォームの通信基盤。JSON-RPC over HTTP/WebSockets
- **ACP→A2A統合**: 2025年9月にACPチームとA2Aチームが統合を発表。事実上ACPがA2Aに合流
- **2軸体制への収斂**: MCP（垂直: エージェント↔ツール）+ A2A（水平: エージェント↔エージェント）の2軸体制に市場が収斂
- **プロトコル統合の教訓**: エコシステムの厚さとオープンガバナンスが勝敗を決める。技術的優位性より採用の広さ
- **MCP+A2A統合アーキテクチャ**: エージェントがA2Aサーバー（能力公開）+ MCPクライアント（ツール接続）の二重構造を持つ
- **AgentGateway**: Solo.io発、Linux Foundation寄贈。A2A+MCPの両プロトコルを単一エンドポイントで統合するAIネイティブデータプレーン
- **Agent Registry**: Agent Cardの管理・キュレーション・ポリシーエンフォースメントの中枢。MCPサーバーとA2Aエージェントの統一登録
- **セキュリティの非対称性**: MCP=OAuth 2.1義務化 vs A2A=宣言型（柔軟だが統一性なし）。ゲートウェイ層での統一化が必須
- **レイヤードアーキテクチャ**: Layer1 MCP(ツール接続) → Layer2 Gateway(セキュリティ) → Layer3 A2A(オーケストレーション) → Layer4 ビジネスロジック
- **Agent Discovery問題**: エージェントの発見・命名・解決メカニズムが未成熟。DNS的な分散発見の確立が次のマイルストーン
- **A2A採用拡大**: 支持企業50社(2025/4)→100社超(2026/2)。ServiceNowが両プロトコル統合を実装

---

## キーコンセプト
- コンテキスト管理＝「限られた机の上の資料配置」
- 標準化による接続コストの劇的削減
- 「どのパターンを使うか」より「いつパターンを切り替えるか」が鍵

## 未解決の疑問
- 分散型識別子（DID）の技術的仕組み——エージェント認証の基盤。Entra Agent ID、AWS AgentCore Policyとの関連
- AgentGatewayの実装詳細——Rust実装のソースコード分析、プロキシ設定のベストプラクティス
- Agent Discovery問題の解決案——分散発見メカニズム、DNS的アプローチの可能性
- AAIF（AI Agent Interoperability Framework）の全体像
- WebMCPの動向——ブラウザベースMCP拡張、プロトコル戦争の第3の軸
