# Confidential Computing と TEE（信頼実行環境）

**日付**: 2026-04-25
**分野**: テクノロジー
**タグ**: #ConfidentialComputing #TEE #SGX #TDX #SEVSNP #Attestation #SideChannel

## 学んだこと

### Confidential Computing とは何を守るのか

従来のクラウドセキュリティは 3 状態のうち 2 つしか扱ってこなかった。

- **Data at rest**（保存中）—— ディスク暗号化（AES-XTS）で解決済み
- **Data in transit**（伝送中）—— TLS 1.3 で解決済み
- **Data in use**（処理中）—— メモリ上のプレーンテキスト、長年の空白地帯

Confidential Computing は **処理中のデータをも暗号化する** という第三の柱を実現する。脅威モデルは極端に厳しく、**ホスト OS・ハイパーバイザ・クラウド運用者・DMA 攻撃者さえも信用しない**。信頼の根は CPU そのもの（シリコンに焼き付けられた root key）に置く。

これが実務上意味するのは「暗号鍵・秘密データを使った計算を、他人のインフラ上で実行できる」こと。医療データのクラウド解析、複数企業間のデータ連合学習、公開鍵基盤のルート鍵管理など、従来は "自社 DC に囲い込む" しかなかった処理が、信頼を CPU ベンダに集約する形でクラウドに載せられるようになった。

### 3 世代のアーキテクチャ

実装は大きく 3 つの世代を踏んで進化してきた。

**第 1 世代: Intel SGX（2015）—— プロセス内エンクレーブ**

SGX は **enclave** と呼ばれる特殊なメモリリージョンを作り、そこに配置されたコードとデータだけを CPU が暗号化する。OS やハイパーバイザも enclave のメモリ内容を見られない。**メモリコントローラと CPU キャッシュの間** で透過的に暗号化する。

欠点は極めて重かった:
- メモリサイズ制限: 初期は 128MB の EPC (Enclave Page Cache) のみ、超過するとページングでスワップ、スワップ時も暗号化するので遅い
- アプリ側の大改造が必要: `ECALL`/`OCALL` で enclave と non-enclave を往復するコードを書く
- システムコールが使えない: enclave 内では OS を信用しないので `read`/`write` すら非信頼 OS 経由

Signal は private contact discovery（電話帳突合）に SGX を使ったが、これは例外的な成功例。Intel は 2021 年にコンシューマ CPU から SGX を廃止、サーバ向けも徐々に TDX へシフト。

**第 2 世代: AMD SEV / SEV-ES（2016-2020）—— VM 単位の暗号化**

SEV は **VM まるごと暗号化** する発想。VM ごとに CPU 内蔵の秘密鍵（ASID 単位）でメモリを暗号化する。ハイパーバイザは暗号化された状態でメモリを読み書きするが、平文は見られない。

利点は **lift-and-shift**: 既存 VM をそのまま confidential VM として動かせる。アプリ改造ゼロ。欠点は初期版では **レジスタが保護されなかった** こと——VMEXIT 時にレジスタ内容がハイパーバイザに見えた。SEV-ES (Encrypted State) でレジスタも保護された。

**第 3 世代: Intel TDX と AMD SEV-SNP（2021-）—— 完全性とアテステーション**

初期 SEV には **integrity（完全性）** の弱点があった。ハイパーバイザはメモリ暗号文を改ざんできる。暗号化されているとはいえ、ビットを反転させれば VM 内の計算結果を変えられる（オラクル攻撃）。

**SEV-SNP (Secure Nested Paging)** と **Intel TDX (Trust Domain Extensions)** は、**RMP (Reverse Map Table)** や **MKTME (Multi-Key Total Memory Encryption)** を使って、各物理ページが「どの VM/TD に属するか」を CPU が追跡する。ハイパーバイザが他 VM のページを書き換えることを検出・拒否する。

TDX では VM を **Trust Domain (TD)** と呼び、TD は CPU 内の **TDX モジュール**（Intel がエンクレーブで実行する仮想化層）を介してハイパーバイザとやりとりする。

### Remote Attestation —— 証明の仕組み

CC の核心は "処理中データの暗号化" だが、**それを verifier がどう確認するか** が最も難しい。これを解くのが **Remote Attestation（遠隔証明）**。

フロー:

1. **Measurement**: TD/enclave の起動時、CPU が初期メモリイメージのハッシュ（MRTD on TDX, MRENCLAVE on SGX）を計算
2. **Quote**: CPU が自身のプライベート鍵（Intel/AMD が工場で焼き込んだ）で Measurement+nonce+公開鍵に署名
3. **Verification**: クライアントは Intel PCS (Provisioning Certification Service) や AMD KDS (Key Distribution Service) から CPU の証明書を取得、Quote の署名を検証
4. **Secret provisioning**: 検証済みと判断したら、クライアントは enclave の公開鍵で秘密（復号鍵・API トークン）を暗号化して送る

これにより "自分が喋っている相手は、改ざんされていない特定のコードを載せた、正規の Intel/AMD TEE である" が数学的に保証される。**CPU ベンダが信頼の根** という批判はあるが、既存の PKI 同様、root CA を信じる構造。

### 2025 年の衝撃: TEE.Fail 攻撃

2025 年後半に発表された **TEE.Fail** は、DDR5 メモリバスをインターポーザ（物理ハードウェア）で盗聴することで Intel SGX/TDX と AMD SEV-SNP から秘密を取り出す攻撃。DDR4 時代の攻撃（Plundervolt, SEVurity など）を DDR5 に拡張した。

重要なのは **CC の脅威モデルが "物理アクセスを防げない"** こと。CC はクラウド運用者の **ソフトウェア層** の攻撃を防ぐが、物理的にサーバにアクセスできる相手には元々弱い。DRAM バス上の deterministic encryption の弱点が実用レベルで悪用できることが示された。対策として、Intel/AMD は NVIDIA GPU TEE（Hopper H100 の Confidential Computing）と組み合わせたり、bus-level MAC を強化する次世代チップに向かっている。

### 実用例と採用

- **Signal**: 連絡先発見に SGX
- **Azure Confidential VM**: AMD SEV-SNP と Intel TDX GA
- **GCP Confidential Space**: ワークロード単位の atttestation 対応
- **AWS Nitro Enclaves**: 独自方式（Nitro Hypervisor が信頼の根、SEV 系ではない）
- **Fortanix, Edgeless, Anjuna, Enarx**: confidential workload を抽象化するランタイム
- **AI 推論**: NVIDIA H100/H200 の GPU TEE と CPU TEE を組み合わせ、顧客データを学習/推論中も見せないマネージド AI

## 気づき・洞察

### "信頼の起源" を物理層に押し下げる思想

従来のセキュリティは **ソフトウェア層の信頼** で組み立てられてきた——OS を信じ、ハイパーバイザを信じ、運用者を信じる。CC は **信頼をシリコンに押し下げる**。OS もハイパーバイザも攻撃者と見なす。

これは重大な哲学転換。"信頼の根を下に" という方向は、TPM → Secure Boot → TEE と一貫した進化。次に来るのは **信頼を物理層より下に**（量子鍵配送、物理層暗号）か、**上に戻す**（TEE の上に zkSNARK で検証可能計算）か、二通りあり得る。

### 脅威モデルの進化が "可能性の地図" を塗り替える

CC 以前のクラウドは「運用者を信じる」前提で設計された。CC 以後は **"運用者を信じなくてもデータを預けられる"** 世界。これは巨大な可能性を開く:

- 銀行と銀行がデータ交換せずに連合学習
- 医療機関間で患者データを動かさず解析
- CIA/NSA クラスの機密データをパブリッククラウドへ
- Web3 的「信頼最小化」をパフォーマンスを犠牲にせず実現

ZKP（ゼロ知識証明）が **完璧だがスロー** な暗号解法を提供するのに対し、TEE は **"CPU ベンダを信じる" 代わりにほぼフルスピード**。実用上は "TEE で計算し、ZKP で重要部分だけ検証" というハイブリッドが主流になりつつある。

### サイドチャネルは永遠の敵

TEE.Fail, Foreshadow, Plundervolt, SGAxe, CrossTalk——TEE の歴史は **サイドチャネル攻撃との終わりなき軍拡**。キャッシュタイミング、電圧グリッチング、メモリバス盗聴。

これは **"完全な秘匿計算は情報理論的に困難"** という深い真実の表れ。計算は物理プロセスなので、電力・時間・電磁波・熱として漏れる。TEE は「プログラムから見える抽象」を守るが、**物理レベルで見えるシグナルは守りきれない**。これは CC の本質的限界であり、"完璧" ではなく "経済的に合理的な困難さ" を提供する技術、と理解すべき。

### "Secure by Default" は到達できない

CC でも、**ユーザが不用意なコードを enclave に入れれば秘密は漏れる**。Enclave 内のバグが非 enclave へ情報を漏らす、サイドチャネルが温存される、鍵管理をミスる、アテステーション検証を省略する——全て実在する失敗モード。

技術の役割は **"セキュアに運用する余地" を作る** ことであり、セキュリティそのものを提供することではない。これは暗号学全般に言える普遍法則。

## 他分野との接続

### cs分野（前日の HM 型推論）との接続

HM 型推論は **"プログラムから型を静的に導出" する早期エラー検出**。TEE は **"プログラム実行を動的に検証可能にする" 実行時保証**。静的型と動的アテステーションはともに **"実行前/中に "正しさ" を証明する"** 構造——forward model の思想が言語処理と信頼計算の両方に現れている。

### cs分野（RSA/ECC）との接続

TEE のアテステーションは結局 **公開鍵暗号の署名検証**。SGX Quote は EC-P-256 で署名、TDX Quote も ECDSA。CPU ベンダが発行する中間 CA + root CA というツリー構造は、Web の TLS とまったく同じ。**"信頼の根" を物理的に近い場所（シリコン）に置く** が新しいだけで、暗号の基礎は 1970 年代のまま。

### tech分野（Passkeys）との接続

Passkeys は **TPM/Secure Enclave** に秘密鍵を保管し、本体ソフトに渡さない——これも小型 TEE。CC はこの哲学を **任意のアプリケーション計算** まで拡張した版。Secure Enclave → SGX → TDX → Confidential GPU という進化は **"保護される計算領域のサイズが拡大"** する一貫した方向。

### anatomy分野（筋の深層と表層の分業）との類比

体内でも **筋・臓器は筋膜・被膜で包まれ、外界と境界を持つ**。TEE の enclave はこの生物学的な "被膜" に相当する——内側の処理は外から見えず、**ゲート（筋膜のチャネル、OCALL）** 経由でのみ情報が出入りする。両者とも "境界を明示し、境界越えに翻訳を挟む" という設計戦略。

### house-hunting分野（免震構造）との類比

免震構造は建物全体を地盤から "切り離し" て地震動を遮断する。AMD SEV-SNP が VM まるごと暗号化するのは、これと同じ **「単位全体を外部から切り離す」** 発想。一方、SGX のようなプロセス内エンクレーブは "建物内の一室だけ免震" する発想で、より細粒度だが改造コストが高い。**どの粒度で切り離すかが設計上の中心問題**。

## 次に深掘りしたいこと

- TEE.Fail の詳細: DDR5 のメモリ暗号化がなぜ deterministic で、どうすれば randomized にできるか
- NVIDIA H100 Confidential GPU の内部機構（GPU 内部の MMU 分離、NVLink 上の暗号化）
- zkTLS / zkVM との境界: TEE と ZKP のハイブリッド設計の最新動向
- Arm CCA (Confidential Compute Architecture, Realms) の設計と TDX との比較
- 実際の attestation 実装: Intel DCAP、AMD KDS の証明書チェーンを手元で検証する手順
- 鍵管理の失敗パターン: confidential workload における鍵ローテーションと災害復旧

## 参考ソース

- [Trusted Execution Environment (TEE) — Microsoft Learn](https://learn.microsoft.com/en-us/azure/confidential-computing/trusted-execution-environment)（Tier 1、公式ドキュメント）
- [Confidential VMs Explained: An Empirical Analysis of AMD SEV-SNP and Intel TDX — ACM](https://dl.acm.org/doi/10.1145/3700418)（Tier 1、査読論文）
- [An experimental evaluation of TEE technology: SGX, SEV, and TDX — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0167404825001464)（Tier 1、査読論文）
- [Benchmarking Confidential Computing: TDX vs SEV-SNP — IEEE](https://ieeexplore.ieee.org/iel8/11207229/11207226/11207298.pdf)（Tier 1、IEEE）
- [TEE.Fail attack breaks confidential computing — BleepingComputer](https://www.bleepingcomputer.com/news/security/teefail-attack-breaks-confidential-computing-on-intel-amd-nvidia-cpus/)（Tier 2、セキュリティ専門メディア）
- [Cisco Confidential Computing Overview White Paper](https://www.cisco.com/c/en/us/products/collateral/servers-unified-computing/computing-overview-wp.html)（Tier 1、企業技術文書）
