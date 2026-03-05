# 📚 テクノロジー・開発 分野サマリー

**最終更新**: 2026-03-05
**エントリ数**: 5

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

---

## キーコンセプト
- コンテキスト管理＝「限られた机の上の資料配置」
- 標準化による接続コストの劇的削減
- 「どのパターンを使うか」より「いつパターンを切り替えるか」が鍵

## 未解決の疑問
- Google A2Aプロトコルの詳細とMCPとの比較
- 分散型識別子（DID）の技術的仕組み
- AIエージェントの「人格」と説明可能性の関係
