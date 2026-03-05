# Eclipse SDVエコシステム全体像——オープンソースで車を「ソフトウェア」にする
**日付**: 2026-03-05
**分野**: SDV（Software Defined Vehicle）
**タグ**: #EclipseSDV #SDV #Kuksa #Velocitas #VSS #Ankaios #Leda #uProtocol #S-CORE

## 学んだこと

### Software Defined Vehicleとは何か

Software Defined Vehicle（SDV）は、車の機能をハードウェアではなく**ソフトウェアで定義・更新する**アーキテクチャ思想だ。スマートフォンがOSのアップデートで新機能を獲得するように、車もOTA（Over-the-Air）で進化し続ける。Eclipse Foundationの**Eclipse SDV Working Group**は、この変革のためのオープンソースエコシステムを構築する業界最大の取り組みであり、BMW、Mercedes-Benz、Volkswagen、Bosch、Microsoft、AWSなど**63以上の組織**が参加している。

### 3つのアーキテクチャ柱

| 柱 | 焦点 | 内容 |
|---|------|------|
| **SDV.Edge** | 車内 | 車載ソフトウェアスタック、通信、ランタイム、オーケストレーション |
| **SDV.Ops** | クラウド | フリート管理、OTAアップデート、監視 |
| **SDV.Dev** | 開発 | 車両アプリ開発ツールチェーン、ワークフロー |

### テクノロジースタック（下から上へ）

```
┌─────────────────────────────────────────────┐
│     Vehicle Apps（Velocitas SDK）             │  ← アプリ層
│     Python/C++ のコンテナ化アプリ              │
├─────────────────────────────────────────────┤
│     通信層（Eclipse uProtocol）               │  ← 通信抽象化
│     Zenoh / MQTT / SOME/IP / gRPC            │
├─────────────────────────────────────────────┤
│     車両抽象化層（Eclipse Kuksa）              │  ← データハブ
│     Databroker（Rust/gRPC）+ VSSモデル         │
├─────────────────────────────────────────────┤
│     ワークロードオーケストレーション            │  ← コンテナ管理
│     Eclipse Ankaios / BlueChi / Kanto        │
├─────────────────────────────────────────────┤
│     OS & ランタイム（Eclipse Leda）            │  ← 車載Linux
│     Yocto Linux + containerd + systemd       │
├─────────────────────────────────────────────┤
│     ハードウェア抽象化                         │  ← プロトコル変換
│     CAN bus feeder, SOME/IP provider, ECU    │
├─────────────────────────────────────────────┤
│     車両ハードウェア                           │  ← 物理層
│     センサー、アクチュエーター、ECU、HPC        │
└─────────────────────────────────────────────┘
```

### 主要プロジェクト詳細

#### Eclipse Kuksa — 車両データ抽象化層（心臓部）

Kuksaの核心は**Databroker**。Rustで書かれ、gRPCサービスとして動作する車両データの中央ハブだ。全てのデータポイントは**COVESA VSS（Vehicle Signal Specification）**に従って階層的に整理される。

```
Vehicle.Speed                    → 車速（km/h）
Vehicle.Powertrain.ElectricMotor → EVモーター情報
Vehicle.Powertrain.TractionBattery.Charging.TimeToComplete → 充電完了時間
Vehicle.Cabin.Door.Row1.Left.IsOpen → ドアの開閉状態
```

CAN busやSOME/IPなどの低レベルプロトコルは**Feeder/Provider**がVSSデータポイントに変換してDatabrokerに投入する。アプリはDatabrokerのgRPC APIを通じて、車のメーカーや型式に依存しない統一的なインターフェースでデータにアクセスできる。

#### Eclipse Velocitas — 車両アプリ開発フレームワーク

VSSから**自動生成されたVehicle Model**を通じて、型安全にデータにアクセスする開発フレームワーク。Python SDK（3.10+）とC++ SDKが利用可能。

```bash
velocitas create -n MyApp -l python -e seat-adjuster
```

アプリはOCI準拠コンテナとしてパッケージされ、MQTTで非同期通信、gRPCで同期通信する。GitHub DevContainersとGitHub Actionsで開発→CI/CD→デプロイが一貫して行える。

#### Eclipse Ankaios — ワークロードオーケストレーション

車載HPCプラットフォーム向けのコンテナオーケストレーター。2025年に**v1.0.0 GA**がリリースされた。複数ノード/VMを単一APIで管理し、ワークロード間の依存関係を自動解決する。車両のKubernetesとも言える存在だが、リソース制約の厳しい組込み環境向けにスリムに設計されている。

#### Eclipse uProtocol — トランスポート非依存通信

新しいプロトコルを作るのではなく、既存のZenoh、MQTT、SOME/IPの**上に統一APIをマッピング**するレイヤー。車内（Zenoh/SOME/IP）からクラウド（MQTT）までシームレスに通信を抽象化する。2025年Q1のコミュニティイベントではプレゼンの半数以上がuProtocol統合に関するものだった。

#### Eclipse Leda — SDV Linuxディストリビューション

Yocto/Pokeyベースのブート可能なLinuxイメージ。Kuksa Databroker、Velocitasアプリ、Ankaios/Kantoオーケストレーション等を統合した「接着剤」ディストリビューション。QEMU（ARM64, x86_64）、Raspberry Piで動作し、CAN busのエミュレーションもサポート。

### Eclipse S-CORE — 業界初の統合リファレンススタック

2024年にBMW、Mercedes-Benz、ETAS、Accenture、Qorixの5社で設立。2025年11月に**v0.5**をリリース（プロジェクト開始からわずか4ヶ月）。2026年末に**v1.0**（プロダクション対応）を予定し、2030年頃の車両プログラムへの搭載を目指す。

CES 2026では参加企業が11社から**32社**に拡大。Stellantis、Qualcomm、QNX、Red Hat、LG、Infineonなどが新たに加わった。QNXがS-COREの基盤OSとして発表されている。

### SDV Hackathon 2025の事例

102名が参加し、実際のプロトタイプを構築：
- **1位 CarByte Engineering**: Compute Node + MCU Node + HPC Nodeの3層システム。リアルタイム車両情報の音声インターフェース付きADAS機能
- **2位 SDVenturers**: 心拍数・視線追跡による感情検出→ドライバーの感情状態に応じてECUの挙動を適応的に変更

## 気づき・洞察

Eclipse SDVのアーキテクチャは、まさにこれまで学んできた**マルチエージェント協調パターン**の物理的実装だ。各プロジェクトが専門的な「エージェント」として機能し、VSS（共通データモデル）とgRPC/uProtocol（通信プロトコル）で協調する。Orchestrator-Workerパターンそのものだ。

特に印象的なのは**VSS（Vehicle Signal Specification）**の設計思想。`Vehicle.Cabin.Door.Row1.Left.IsOpen`のようなドット区切りの階層構造は、ファイルシステムのパスや、このDailyLearningシステムの`domains/<分野>/`構造と同型だ。**「階層的に整理された名前空間」は、複雑なシステムを扱う普遍的パターン**なのだ。

「オープンソースで車を作る」というビジョンは、Linuxがサーバーの世界を変えたのと同じ構造的変革を自動車産業にもたらそうとしている。Linuxが20年かけてサーバーOS市場を制覇したように、Eclipse SDVは2030年代の車載ソフトウェアの標準になる可能性がある。

EV作成という最終目標から見ると、Eclipse SDVは「車を作る」のではなく「車の脳を作る」プロジェクトだ。物理的なモーター制御やバッテリー管理のハードウェアは別途必要だが、**それらを統合的に制御するソフトウェアプラットフォーム**としてEclipse SDVが機能する。

## 他分野との接続

- **テック（マルチエージェント）**: Eclipse SDVのプロジェクト群はOrchestrator-Workerパターンの実装。Kuksa = Orchestrator（データハブ）、各Vehicle App = Worker。HITL/HOTLの議論は自動運転の安全性設計にも直結する
- **テック（境界付き自律性）**: 自動運転車はBounded Autonomyの最も厳しいユースケース。EU AI Actの高リスクカテゴリに該当する
- **解剖学（肩甲骨）**: 17の筋肉で支えられた肩甲骨の協調運動と、複数のEclipse SDVプロジェクトが協調して車両を制御する構造は、どちらも「分散した専門コンポーネントの協調による統合制御」
- **音楽（ラヴェル）**: VSSの階層的信号定義は楽譜のスコアに似ている。各パート（センサー）が自分の役割を演奏し、Databroker（指揮者）が全体を統合する
- **哲学（枯山水）**: SDVの「余白」はuProtocolのトランスポート非依存設計。具体的な通信プロトコルを規定しない「空」が、多様な実装を受け入れる柔軟性を生む

## 次に深掘りしたいこと

- COVESA VSSの詳細構造——EV専用ブランチ（ElectricMotor, TractionBattery）の深掘り
- Eclipse Leda + Raspberry PiでのSDV環境構築ハンズオン
- Kuksa Databrokerのアーキテクチャ——Rustで書かれたgRPCサーバーの設計思想
- CAN busプロトコルの基礎——車両ネットワークの物理層を理解する
- S-CORE v1.0のロードマップとQNX統合の詳細
