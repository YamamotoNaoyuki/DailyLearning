# 🚗 SDV（Software Defined Vehicle） 分野サマリー

**最終更新**: 2026-03-07
**エントリ数**: 5

**分野の方針**: Eclipse SDVを中心としたオープンソースのSoftware Defined Vehicleエコシステムを学ぶ。最終目標はEclipse SDVのオープンソースプロジェクトを活用した電気自動車の作成。車両アーキテクチャ、Vehicle Signal Specification、コンテナ化、ワークロードオーケストレーション、車両アプリ開発を横断的に学ぶ。

---

## 蓄積された知識
- **Eclipse SDV Working Group**: Eclipse Foundation主導。BMW、Mercedes-Benz、VW、Bosch、MS、AWSなど63+組織が参加
- **3つの柱**: SDV.Edge（車内）、SDV.Ops（クラウド）、SDV.Dev（開発）
- **Eclipse Kuksa**: 車両データ抽象化層の心臓部。RustのDatabrokerがgRPCサービスとして全データポイントを管理。COVESA VSS準拠
- **COVESA VSS**: 車両信号の階層的データモデル。`Vehicle.Speed`、`Vehicle.Powertrain.ElectricMotor.*`など。プロトコル非依存
- **Eclipse Velocitas**: 車両アプリ開発フレームワーク。Python/C++ SDK。OCI準拠コンテナ。MQTT/gRPC通信
- **Eclipse Ankaios**: 車載ワークロードオーケストレーター。v1.0.0 GA。複数ノード/VMを単一APIで管理
- **Eclipse uProtocol**: トランスポート非依存通信。Zenoh/MQTT/SOME/IPの上に統一APIをマッピング
- **Eclipse Leda**: Yocto/PokeyベースのSDV Linuxディストリビューション。QEMU、Raspberry Pi対応
- **Eclipse S-CORE**: 業界初の統合リファレンススタック。v0.5（2025年11月）、v1.0は2026年末予定。CES 2026で32社に拡大
- **Eclipse Zenoh**: 高性能pub/sub/queryプロトコル。Rust製。v1.1.0。ITU-TがV2Xに最適と認定
- **Eclipse BlueChi**: Red Hat貢献。C製。マルチノードsystemdサービスコントローラー。機能安全対応
- **SDV Hackathon 2025**: 102名参加。CarByte Engineeringが3層アーキテクチャ+音声インターフェースで1位
- **CAN bus**: 1983年Bosch開発。2本のツイストペア(CAN-H/CAN-L)による差動信号。ノイズ耐性が高い
- **アービトレーション**: IDが小さいほど高優先度。非破壊的——衝突してもデータが失われない
- **通信速度**: 125kbps(500m)〜1Mbps(40m)のトレードオフ。データフレーム最大8バイト
- **CAN FD**: 2012年Bosch開発。データ64バイト、最大8Mbps。BRS(Bit Rate Switch)で後方互換性維持
- **OBD-II**: CANの上位層プロトコル。車載診断規格
- **KUKSA DBC Feeder**: CAN生データ→DBCファイルで解釈→VSS変換。ハードウェアとソフトウェアの翻訳層
- **SOME/IP**: BMW開発（2011年）。サービス指向の車載ミドルウェア。AUTOSAR標準。TCP/UDP over Ethernet
- **CAN vs SOME/IP**: 信号ベース(8B) vs サービスベース(無制限)。1Mbps vs 100Mbps-10Gbps。固定的 vs 動的発見
- **SOME/IPメッセージ**: 16バイト固定ヘッダー + 可変長ペイロード。Service ID + Method ID + Client ID + Session ID
- **4つの通信パターン**: Request/Response(RPC)、Fire & Forget、Event Notification(Pub/Sub)、Field(Getter/Setter/Notifier)
- **SOME/IP-SD（Service Discovery）**: Offer Service、Find Service、Subscribe Eventgroup、Subscribe Ack。動的サービス発見
- **vsomeip**: COVESA提供のオープンソース実装。kuksa-someip-providerがKuksa DatabrokerへのSOME/IPブリッジ
- **3層アーキテクチャ**: SOME/IP（通信）→ VSS（データモデル）→ Kuksa（データブローカー）がEclipse SDVの車内通信骨格
- **100BASE-T1**: IEEE 802.3bw(2017)。元BroadR-Reach。1ペアUTPで100Mbps全二重。車載Ethernetの物理層
- **PAM3+エコーキャンセレーション**: 3値信号と自分の送信信号の差し引きで1ペア全二重を実現
- **車載メリット**: 重量30%減、コスト最大80%減、帯域100倍（vs CAN）。IT業界のツール（Wireshark等）が利用可能
- **1000BASE-T1**: IEEE 802.3bp。1Gbps。カメラ映像・LiDAR用。ゾーンアーキテクチャのバックボーン
- **フルスタック**: 100BASE-T1(物理)→TCP/UDP(トランスポート)→SOME/IP(ミドルウェア)→VSS(データモデル)→Kuksa(ブローカー)→Velocitas(アプリ)
- **ゾーンアーキテクチャ**: ドメイン（機能別）からゾーン（物理位置別）へのE/E再編。ゾーンECU（I/Oゲートウェイ）+ HPC（集中計算）構成
- **ゾーンECU**: Mixed-Criticality対応（ハイパーバイザーによるASIL分離）。CAN/LIN→Ethernet変換ゲートウェイ機能。AUTOSAR Classic + Adaptive共存
- **HPC**: 車両に1〜3台。数百TOPS級SoC。ADAS・統合ボディ制御・インフォテインメントのアプリケーションロジックを集約
- **ワイヤーハーネス削減**: Tesla Model S→Model 3で3km→1.5km（50%減）。VW SSPで40%削減・ECU50%以上削減目標
- **10BASE-T1S**: IEEE 802.3-2022。マルチドロップ（バス型）Ethernet。PLCA（物理層衝突回避）。ゾーン内ラストマイルでCAN/LIN代替
- **OEM動向**: Tesla（5年以上リード、モジュラーワイヤリング特許）、VW SSP（2026冬季テスト→2027量産、Rivian提携）、ハイブリッド型の段階的移行が主流
- **Ankaios×ゾーン**: サーバー(HPC)/エージェント(ゾーンECU)モデルがゾーンアーキテクチャと同型。宣言的ワークロード管理
- **Eclipse SDV×ゾーン**: Kuksa（ゾーン透過的データアクセス）、uProtocol（異種通信統合）、Leda（ゾーンECU向けOS候補）

---

## キーコンセプト
- SDVは「車の脳」を作るプロジェクト——ハードウェア制御を統合するソフトウェアプラットフォーム
- VSSの階層構造は「複雑なシステムを名前空間で整理する」普遍的パターン
- Eclipse SDV ≒ マルチエージェント協調パターンの物理的実装
- Linuxがサーバーを変えたように、Eclipse SDVは2030年代の車載ソフトウェアの標準を狙う

## 未解決の疑問
- DBC（Database CAN）ファイルの書き方とKuksa Feederの設定
- TSN（Time-Sensitive Networking）——車載Ethernetのリアルタイム性保証。IEEE 802.1Qbv Time-Aware Shaperの動作
- Ankaiosマルチノード構成の実践——HPC + ゾーンECU 4台をQEMU/Dockerで再現
- AUTOSAR Adaptive ara::comとSOME/IP-SDの関係
- ゾーンECU向けSoC比較——NXP S32G、Renesas R-Car S4、Qualcomm Ride Flex
- VW SSP + Rivian提携のソフトウェアプラットフォーム技術選択
