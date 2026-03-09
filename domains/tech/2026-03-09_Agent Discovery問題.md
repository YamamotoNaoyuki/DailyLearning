# Agent Discovery問題
**日付**: 2026-03-09
**分野**: テクノロジー・開発
**タグ**: #AgentDiscovery #A2A #AgentCard #DNS #サービスディスカバリ #ANS #BANDAID #AAIF

## 学んだこと

### 1. Agent Discovery問題とは何か

エージェントが他のエージェントを「見つける」ための基盤が未成熟であるという根本的課題。現在のインターネットスタック（DNS、IP、CA）は、静的なサービス間通信を前提に設計されており、大量のエフェメラルで自己指向型のエージェントが動的に発見・接続し合う世界を想定していない。

Solo.ioのChristian Posta（AgentGateway開発者）は、A2Aプロトコルが「Agent Card」による能力記述を定義しつつも、**発見（Discovery）・命名（Naming）・解決（Resolution）** の3つを意図的に仕様外としていることを指摘。これがA2Aの「Missing Pieces」であり、エコシステムの実運用における最大のギャップである。

### 2. Agent Card — .well-known/agent-card.json

A2Aプロトコルの核心的な発見メカニズム。RFC 8615（Well-Known URIs）に準拠し、エージェントサーバーが以下のパスでAgent Cardを公開する:

```
https://{agent-server-domain}/.well-known/agent-card.json
```

**Agent Cardの構造:**
- **基本情報**: name, description, url, provider, version, documentationUrl
- **A2Aケイパビリティ**: streaming, pushNotifications等のサポート宣言
- **認証**: Bearer, OAuth2等のスキーム詳細
- **スキル**: AgentSkillオブジェクト群（id, name, description, inputModes, outputModes, examples）

**歴史的マイルストーン**: 2025年4月、agent-card.jsonがIANA .well-knownレジストリに登録された最初のAIエージェント固有エントリとなった。A2Aは2026年1月にRelease Candidate v1.0に到達。

**限界**: Agent Cardは「受動的発見」——クライアントがドメインを事前に知っている必要がある。「〇〇ができるエージェントはどこにいるか？」という**能動的発見**には対応していない。

### 3. DNS的アプローチ — 3つの競合提案

#### 3a. ANS（Agent Name Service）— OWASP GenAI Security Project

DNSにインスパイアされた、PKI（公開鍵基盤）ベースの分散発見メカニズム。

**アーキテクチャ:**
- **ANSName**: プロトコル、エージェント能力、プロバイダー、バージョンのメタデータをエンコードした構造化命名
- **Agent Registry**: ANSNameとエンドポイント情報のマッピングを保持
- **Certificate Authority (CA) / Registration Authority (RA)**: エージェントごとにPKI鍵ペアとデジタル証明書を発行
- **Protocol Adapter Layer**: MCP、A2A等の外部プロトコルごとに専用アダプタを持ち、低結合でクロスプロトコル発見を実現

**発見フロー:**
1. エージェントAがターゲットのANSNameをANS Serviceに送信
2. ANS ServiceがAgent Registryでマッチングレコードを検索
3. ターゲットエージェントの暗号署名と証明書を検証
4. 検証成功時にエンドポイント情報を返却

**特徴**: プロトコル非依存。証明書の失効はCRL/OCSPで管理。DNSの「名前→アドレス解決」をエージェントの「能力→エンドポイント解決」に拡張した設計。

#### 3b. DNS-AID / BANDAID — IETF Draft（Infoblox提案）

既存のDNSインフラを**そのまま**活用するアプローチ。新しいレコードタイプを導入せず、既存のSVCB/HTTPSレコードを拡張する。

**BANDAID（Brokered Agent Network for DNS AI Discovery）の設計:**
- **リーフゾーン規約**: `_agents.example.com` 以下にサービスレコードを配置
- **SVCB/HTTPSレコード**: `chat._agents.example.com` のようなラベルでエージェントのメタデータをエンコード
- **カスタムパラメータ**: cap（ケイパビリティ）、policies、realm等をSVCBレコードのパラメータとして格納
- **DCV（Domain Control Validation）**: エフェメラル（セッションベース委任）と永続的（長期認可シグナリング）の2モデル

**哲学**: 「DNSは数十年の運用成熟度を持つ最も広く展開された相互運用可能なサービス発見メカニズム」——新プロトコルを作るより、既存インフラを賢く使う。リファレンス実装がGitHub（infobloxopen/dns-aid-core）で公開済み。

**DNS-AIDとBANDAIDの関係**: DNS-AIDが初期ドラフト、BANDAIDがブローカーモデルを追加した発展版。IETF 124で正式にプレゼンテーション済み。

#### 3c. Solo.io agentregistry — Kubernetes/クラウドネイティブアプローチ

Solo.ioがKubeCon North America 2025/2026で発表し、オープンソースとして寄贈。

**3層構造:**
1. **Agent Registry**: 承認済みA2Aエージェントの中央リポジトリ。「エージェントのApp Store」
2. **Agent Naming Service（ANS）**: スキル・セキュリティ・能力ベースのインテリジェント発見。名前ではなく「何ができるか」で検索
3. **Agent Gateway**: セキュリティ・オブザーバビリティ・ガバナンスのデータプレーン

### 4. 中央集権型 vs 分散型レジストリ — 5つのアプローチの比較

2025年の論文「Evolution of AI Agent Registry Solutions」（arXiv:2508.03095）が5つの主要アプローチを体系的に比較:

| アプローチ | 方式 | 特徴 |
|-----------|------|------|
| **MCP Registry** | 中央集権（GitHub mcp.json） | シンプル、既存認証活用。単一障害点リスク |
| **A2A Agent Cards** | 分散型（各ドメインの.well-known） | 自己記述型。能動的発見に非対応 |
| **AGNTCY Agent Directory** | 分散型（IPFS Kademlia DHT） | OCI artifact storage、Sigstore署名。最も分散化 |
| **Microsoft Entra Agent ID** | エンタープライズSaaS | Azure AD統合、ゼロトラストポリシー。ベンダーロックイン |
| **NANDA Index AgentFacts** | 暗号検証型 | プライバシー保護、クレデンシャル付きアサーション |

**コンテキスト依存の選択**: エンタープライズ（Azure既存）→ Entra Agent ID。オープンコミュニティ→ NANDA Index。プロトコル固有エコシステム→ MCP Registry。

### 5. AAIF（Agentic AI Foundation）とレジストリの未来

**AAIF**: 2025年12月、Linux Foundation傘下で設立。Anthropic、OpenAI、Blockが創設メンバー。MCPプロトコル、Goose（Blockのエージェントフレームワーク）、AGENTS.md規約を統合。

**AAIFの役割:**
- ベンダー中立なオープンソースエージェントAIプロジェクトのホスト
- 単一企業が支配しないガバナンスモデル
- オープンプロトコルの標準化——異なるビルダーのシステムがシームレスに連携

**Kong MCP Registry**: AAIFスタンダード準拠。Kong Konnect上でMCPサーバーを一元登録・ガバナンス。エージェントが承認済みツールを動的に発見しつつ、セキュリティ・オーナーシップ・ポリシー制御を維持。

### 6. Google Gemini Enterprise（旧Agentspace）のプラットフォームアプローチ

Googleは「プラットフォーム内レジストリ」として実装:
- **Agent Engine**: ADKエージェントとA2Aエージェントの登録・管理
- **マーケットプレイス**: 数千の審査済みパートナー製AIエージェントの発見・デプロイ
- **Cloud API Registry**: MCP サーバー・ツールの発見・ガバナンス（Apigee API Hub経由）

プラットフォーム型は発見問題を「解決」するが、エコシステムをプラットフォーム内に閉じ込めるトレードオフがある。

### 7. 現状の収斂と課題

**収斂の方向性:**
- **短期（2026）**: .well-known/agent-card.json + プラットフォーム内レジストリの併用
- **中期（2027-2028）**: DNS-AID/BANDAIDのIETF標準化 + ANSの能力ベース発見の統合
- **長期**: 分散型（DHT/ブロックチェーン）と中央集権型のハイブリッド

**未解決の技術的課題:**
- **メタデータモデルの乱立**: MCP(mcp.json) vs A2A(agent-card.json) vs NANDA(AgentFacts) — 統一スキーマなし
- **スケール問題**: 現在のインターネットスタックは「数兆の高速移動する自律エージェント」を想定していない
- **失効伝播の遅延**: 証明書失効やポリシー変更のリアルタイム伝播が困難
- **セマンティック発見**: 「何ができるか」を機械が理解して検索する仕組みの標準化

## 気づき・洞察

**「DNSの教訓」がそのまま適用される**: DNSは中央集権型ルートサーバー + 分散型キャッシュ/委任のハイブリッドで成功した。エージェント発見も同じパターンに収斂する可能性が高い。完全分散（DHT）も完全中央（プラットフォーム）も極端すぎる。

**A2Aの戦略的な「未定義」**: A2Aが発見・命名・解決を仕様外にしたのは弱点ではなく戦略。プロトコル層とインフラ層を分離し、発見メカニズムの競争と進化を許容している。HTTPがDNSを規定しなかったのと同じ構造。

**「受動的発見 → 能動的発見」の進化**: .well-known はURLを知っている前提（受動的）。ANSやagentregistryはスキルベース検索（能動的）。この進化は、Webの「URLを知っている → 検索エンジンで見つける」と同じ道筋を辿っている。

**セキュリティが発見の前提条件**: ANSのPKI、BANDAIDのDCV、Entra Agent IDのゼロトラスト——全アプローチがセキュリティをオプションではなくファーストクラスの要件として組み込んでいる。前回学んだ「セキュリティの非対称性」問題（MCP=OAuth必須 vs A2A=宣言型）の解決が発見層で図られている。

## 他分野との接続

- **哲学（枯山水）**: 「余白の設計」——A2Aが発見メカニズムを意図的に未定義にしたことは、枯山水の「描かないことで想像を誘う」設計思想と通じる。プロトコル設計における引き算の美学。

- **音楽（オーケストレーション）**: エージェント発見はオーケストラの「チューニング」に似ている。演奏（実行）の前に、誰がどの楽器を持ち、どこに座っているかを確認する必要がある。ANSはコンサートマスターのような「基準音」を提供する存在。

- **ゴルフ（コースマネジメント）**: プレー前のコース情報の「発見」——ヤーデージブック、グリーンの傾斜、風向き。静的情報（コースレイアウト = Agent Card）と動的情報（当日の風 = リアルタイム能力状態）の両方が必要な点が、エージェント発見と同構造。

- **家探し**: 不動産ポータル（SUUMO等）は「物件レジストリ」。検索条件（エリア、価格、間取り）による能力ベース発見と、仲介業者（ブローカー）による信頼性担保の2層構造が、Agent Registry + ANS/Trust Layerと酷似。

## 次に深掘りしたいこと

- **BANDAID IETF Draftの詳細読解**: SVCBレコードのカスタムパラメータ仕様、実際のDNSクエリ例
- **AGNTCY Agent Directory**: IPFS Kademlia DHTベースの完全分散型発見の実装詳細。Sigstoreによる署名検証フロー
- **NANDA Index AgentFacts**: プライバシー保護型発見の暗号学的仕組み。選択的開示（Selective Disclosure）との関連
- **Agent Discovery + DID統合**: 前回学んだ分散型識別子（DID）が発見層とどう統合されるか。DIDDocumentとAgent Cardの関係
- **実装ハンズオン**: Solo.io agentregistryのKubernetes上でのデプロイと、Agent Cardの登録・発見フローの実体験
