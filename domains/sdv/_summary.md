# 🚗 SDV（Software Defined Vehicle） 分野サマリー

**最終更新**: 2026-03-05
**エントリ数**: 1

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

---

## キーコンセプト
- SDVは「車の脳」を作るプロジェクト——ハードウェア制御を統合するソフトウェアプラットフォーム
- VSSの階層構造は「複雑なシステムを名前空間で整理する」普遍的パターン
- Eclipse SDV ≒ マルチエージェント協調パターンの物理的実装
- Linuxがサーバーを変えたように、Eclipse SDVは2030年代の車載ソフトウェアの標準を狙う

## 未解決の疑問
- COVESA VSSのEV専用ブランチ（ElectricMotor, TractionBattery）の詳細
- Eclipse Leda + Raspberry PiでのSDV環境構築ハンズオン
- Kuksa DatabrokerのRust/gRPCアーキテクチャ詳細
- CAN busプロトコルの基礎——車両ネットワークの物理層
- S-CORE v1.0ロードマップとQNX統合
