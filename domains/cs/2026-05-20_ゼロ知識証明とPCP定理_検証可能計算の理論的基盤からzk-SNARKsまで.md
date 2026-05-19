# ゼロ知識証明とPCP定理 — 検証可能計算の理論的基盤からzk-SNARKsまで

**日付**: 2026-05-20
**分野**: cs
**タグ**: #zero-knowledge-proofs #zk-SNARKs #PCP定理 #verifiable-computation #interactive-proof #complexity-theory #cryptography

## 学んだこと

### ゼロ知識証明（ZKP）の定義
**Goldwasser-Micali-Rackoff (1985, "The Knowledge Complexity of Interactive Proof-Systems")** で導入。1989年 STOC ジャーナル版で正式化。Goldwasser は 2012 年 Turing 賞（Micali と共同）受賞。**「真偽以外の何も漏らさずに真偽を証明する」** プロトコル。

**3つの性質**:
1. **完全性（Completeness）**: 命題が真なら、誠実な証明者は誠実な検証者を **高確率で説得できる**
2. **健全性（Soundness）**: 命題が偽なら、（計算能力に制約のある）悪意ある証明者は **無視できる確率でしか説得できない**
3. **ゼロ知識性（Zero-Knowledge）**: 検証者が「証明者と対話した後の状態」を、**証明者なしでシミュレートできる**——つまり、対話から学ぶことは何もない（シミュレーション・パラダイム）

### 古典例 — Schnorr's Identification Protocol (1989)
Σ-protocol の典型。証明者は秘密 $x$（離散対数）の知識を、$y = g^x$ だけ公開して証明する:
1. 証明者: ランダム $r$ を選び $a = g^r$ を送信（**コミット**）
2. 検証者: ランダム挑戦 $c$ を送信（**チャレンジ**）
3. 証明者: $z = r + cx$ を送信（**レスポンス**）
4. 検証者: $g^z = a \cdot y^c$ を検証

**ゼロ知識性の証明**: シミュレータは $z$ と $c$ をランダムに選び、$a = g^z / y^c$ を逆算できる。実プロトコルの transcripts と区別不能 → 「対話からは秘密 $x$ について何も学べない」。

### Interactive Proof System (IP) → IP = PSPACE
**Shamir (1990, JACM)** の歴史的結果: **IP = PSPACE**——多項式時間検証者と無限計算能力の証明者の対話で、**多項式空間で解ける任意の問題を検証できる**。これは「NP（クッキー・レビン定理：1つの証拠で検証）」を遥かに超える。**Sum-check protocol**（Lund-Fortnow-Karloff-Nisan 1990）が中心技法——多変数多項式の和を多項式時間で確率的検証。

### Multi-Prover Interactive Proofs (MIP) → NEXP
**Babai-Fortnow-Lund (1991)**: 互いに通信できない複数の証明者 + 検証者で、**MIP = NEXP**（指数時間非決定性チューリングマシンが解ける問題全部）。これが PCP 理論への扉を開いた。

### PCP 定理 — Probabilistically Checkable Proofs
**Arora-Safra (1992) + Arora-Lund-Motwani-Sudan-Szegedy (1992-98) で確立、Sudan 2007 Nevanlinna 賞、Arora 2010 Gödel 賞、Khot 2014 Nevanlinna 賞**

**定理**: **NP = PCP[O(log n), O(1)]**——任意の NP 問題は、**O(log n) ビットのランダム性 + O(1) ビットの proof アクセス** で確率的に検証できる証明形式に変換可能。**3-4 ビットを読むだけで証明全体の妥当性を 99% 以上の信頼度で判定** できる。

**実際のサイズ**: 元の証明 $\pi$（NP 問題のサーティフィケート）を **多項式時間で「PCP-encoded $\pi'$」に変換**、$|\pi'| = \text{poly}(|\pi|)$。検証者は $\pi'$ の任意の **O(1) 個の位置** をランダムに選んで読むだけ。

**応用**: PCP 定理は **近似アルゴリズムの非近似性証明** に革命をもたらした。MAX-3SAT の **(7/8 + ε)-近似は NP困難**（Håstad 1997）、MAX-CLIQUE の任意定数倍近似は NP困難。**「最適化問題の難しさ」を実数の精度として表現する** ツール。

### Succinct Interactive Arguments と Computational Soundness
Kilian (1992): **Linear PCP** + **collision-resistant hash function** で、**多項式サイズ証明** ではなく **対数サイズ（poly-logarithmic）argument** を構築。Soundness は計算的（poly-time prover を仮定）。

**Micali (1994)**: Fiat-Shamir 変換でこれを **非対話的** に変換 → CS proofs。

### zk-SNARK の構成 (4 stages, Bitansky et al. 2012)
**zk-SNARK** = Zero-Knowledge Succinct Non-interactive ARgument of Knowledge

1. **Arithmetic Circuit → R1CS**: 計算を $(A, B, C)$ 行列の連立で表現、$Az \cdot Bz = Cz$（要素積）
2. **R1CS → QAP** (Quadratic Arithmetic Program): 多項式 $A(x), B(x), C(x)$ に変換、$A(x) \cdot B(x) - C(x) = H(x) \cdot Z(x)$
3. **QAP → Linear PCP → Linear IP**: Linear interactive proof（LIP）に圧縮
4. **LIP → SNARK**: pairing-based 暗号（楕円曲線 e: G1 × G2 → GT）で **非対話的・短い・検証高速**

**Groth16** (2016) は **最小サイズ証明**: 3つの楕円曲線群要素（合計 256 バイト程度）。**検証は3回の pairing 演算（数 ms）**。trusted setup（per-circuit）が必要だがサイズと速度では現役最強。

### zk-STARK — Trusted Setup なしの代替
**STARK** = Scalable Transparent ARgument of Knowledge（Ben-Sasson, Bentov, Horesh, Riabzev 2018）

**Trusted Setup 不要**: 任意ランダム性のみ。**Quantum-resistant**（ハッシュ関数のみ依存、楕円曲線非依存）。証明サイズは zk-SNARK より大きい（数十 KB - 数百 KB）が、**透明性と量子耐性が決定的利点**。

**FRI**（Fast Reed-Solomon Interactive Oracle Proofs）が中心技法。**Reed-Solomon 符号**（cs 2026-04-29 学習）の構造を利用して、多項式の評価が低次か高次かを対数時間で確率的検証。

### 実用システム
- **Zcash (2016-)**: 最初の商用 zk-SNARK 応用。プライベートトランザクションを Sapling/Orchard プロトコルで実装、トランザクション内容（送金額・送り先）を完全秘匿しつつ正当性証明
- **Filecoin (2020-)**: Proof of Storage を zk-SNARK で構築、ストレージプロバイダがデータを実際に保持していることを暗号学的に証明
- **Ethereum L2 (2022-)**: zkSync, StarkNet, Polygon zkEVM, Scroll が rollup でメインチェーンの計算負荷を圧縮。**zkEVM** = EVM 計算を zk-SNARK で証明
- **Aleo, Mina Protocol**: zk-SNARK ネイティブブロックチェーン
- **Tornado Cash (2019-)**: ミキサー、規制問題（OFAC 制裁）に発展

### Verifiable Computation の3つの軸
1. **Succinctness（短さ）**: 証明サイズ vs 計算サイズ。SNARK は対数、STARK は対数²、PCP は多項式
2. **Verification cost**: 検証時間。SNARK: O(1) ペアリング、STARK: O(polylog n)
3. **Setup**: trusted（SNARK Groth16）、universal trusted（PLONK, Marlin）、transparent（STARK, Bulletproofs）

**PLONK (Gabizon-Williamson-Ciobotaru 2019)**: **Universal trusted setup**——一度の setup で **任意の回路** に再利用可能。Groth16 の per-circuit setup の制約を解消。Aztec、Aleo、Polygon zkEVM で採用。

### Bulletproofs（Bünz et al. 2018）
**Trusted setup 不要、対話的だが Fiat-Shamir で非対話化、楕円曲線のみ依存**。zk-SNARK より証明サイズ大（数 KB）、検証時間長（リニア）、だが setup不要 + 表現力豊富。**Range proof**（「この数値が [0, 2^64) に属する」を秘匿証明）に特化。Monero が confidential transactions で採用。

### 2026年の動向
- **Halo2 / Plonky2 / RISC Zero**: 汎用 zkVM（zero-knowledge virtual machine）。任意のプログラムを zk-SNARK 化できる
- **Folding schemes (Nova, ProtoStar, HyperNova)**: 再帰的 SNARK の効率化、IVC（Incrementally Verifiable Computation）
- **zkML**: 機械学習推論の検証可能化、Worldcoin/Modulus Labs の実装
- **ZK-friendly hash functions**: Poseidon, Reinforced Concrete, Anemoi（algebraic hash で arithmetization 効率化）
- **GPU/FPGA/ASIC accelerators**: prover の高速化、Ingonyama、Cysic 等のスタートアップ

## 気づき・洞察

**「示さないことで示す」の極致**: ZKP は **暗号学の根本逆説**——通常、何かを証明するには情報を**追加**する。ZKP は情報を**漏らさず**証明する。シミュレーション・パラダイム（「対話から学べることは何もない＝シミュレータが対話を再現できる」）は **「学習可能性」を否定的に定式化** した。これは Cage の 4'33"（演奏で音を出さない）、フォーレ・レクイエムの Dies irae 削除（書くべきものを書かない）、TLS 1.3 の機能削除（複雑性を捨てて安全性を得る）と同じ「不在による主張」の系譜——ただし暗号学的に厳密化されている。

**PCP 定理の哲学的衝撃**: 「証明全体を読まずに正しさを確信できる」——直感に完全に反するが数学的に証明されている。これは **「真理の局所性」の発見** ——巨大な数学的真理も、適切に符号化すれば任意のビット位置からほぼ確実に検証できる。情報理論の Reed-Solomon 符号（部分情報から全体復元）、ホログラム（全体情報の局所符号化）と同型の発想。**「数学的真理は適切にエンコードされれば局所的に検出可能」**。

**「効率と信頼の交換」**: zk-SNARK は trusted setup（信頼）を払って succinctness（効率）を得る。STARK は trusted setup を捨てて証明サイズ大を受け入れる。Bulletproofs はその中間。**「何を信じるか」を設計判断にする** ——暗号学の成熟は「絶対的安全」幻想を捨て、信頼アサンプションを明示化した。

**応用拡大の歴史的瞬間**: ZKP は1985年に理論として生まれ、**30年間ほぼ純粋数学** だった。Zcash (2016) で初めて大規模実用化、2020年代に **L2 rollup でメインストリーム** 化。理論から実用への遅延30年は、ニュートン物理（17世紀→産業革命19世紀）、量子力学（1900年代→トランジスタ1950年代）と同じパターン。**抽象理論が実用化を要求する技術的閾値の到達** が条件。

**「検証可能計算」が暗号通貨を超える**: zk-rollup, zkML, zkVM, zkID（プライバシー保護身分証明）は **「外部委託計算の信頼問題」** の汎用解。クラウドコンピューティング、AI推論、政府サービスのデジタル化すべてに「結果が正しいことを証明したいが過程は秘匿したい」需要が存在する。ZKP は次世代のインフラ技術——TLS が90年代後半に「ネット商取引のための暗号」として普及したように、ZKP は2030年代に「検証可能計算のための暗号」として普及する可能性。

## 他分野との接続

- **tech（DPDK・カーネルバイパス）**: 両者とも **「制約を受け入れて自由を得る」** 設計哲学。ZKP は計算過程の秘匿を制約として受け入れ検証可能性を得る、DPDK は OS の汎用性を捨てて性能を得る
- **music（フォーレ Dies irae 削除）**: 「不在による主張」の構造的同型——書かないことで示す、見せないことで証明する
- **anatomy（自然免疫の TLR4 シグナル）**: 受容体は「結合した分子そのもの」より「結合パターン」で応答を決める——形態認識の確率的判断。ZKP の検証者が「ビット位置の応答パターン」から正しさを判定するのと同型
- **bread（発酵管理）**: ATIs のような分子レベルの「見えない」変化を、間接指標（pH、TTA、香気プロファイル）から判定するのは ZKP の「中身を見ずに正しさを検証する」と同じ思想
- **golf（コースマネジメント）**: TrackMan が「ボールの軌跡を完全観測せずに4つの数値から軌跡を予測する」のは **間接観測による検証**——PCP の「局所アクセスでの全体検証」と同型

## 次に深掘りしたいこと

- **Sum-Check Protocol の詳細**: Lund-Fortnow-Karloff-Nisan 1990 の構造、多変数多項式の確率的検証の数学
- **Probabilistically Checkable Proofs of Proximity (PCPP)**: PCP の「証明全体」検証ではなく「割り当ての近接性」検証への一般化
- **Folding Schemes (Nova/HyperNova) の数学**: 再帰的 zk-SNARK の代数的構造、IVC への応用
- **zkML の実装課題**: ニューラルネット推論を arithmetic circuit に変換する効率化、ReLU 等の非線形性の処理
- **Plonky2 / Halo2 の内部**: STARK + SNARK ハイブリッド、再帰性を持つ実用システム
- **Bulletproofs の Inner Product Argument**: 内積引数の対数サイズ証明、Pedersen commitment の構造
- **Post-Quantum ZKP**: 格子ベース、ハッシュベース、コードベースの量子耐性 ZKP
- **Universal Composability (UC) フレームワークでの ZKP の合成**: Canetti のセキュリティモデル

## 参考ソース

- Goldwasser, Micali, Rackoff "The Knowledge Complexity of Interactive Proof-Systems" SIAM J. Computing 18(1), 1989（Tier 1、原典）
- Arora, Safra "Probabilistic Checking of Proofs" J. ACM 45(1), 1998（Tier 1、PCP定理）
- Justin Thaler "Proofs, Arguments, and Zero-Knowledge" Foundations and Trends in Privacy and Security, 2023（Tier 1、800頁の体系書、無料公開）
- Ben-Sasson, Bentov, Horesh, Riabzev "Scalable Zero Knowledge with No Trusted Setup" CRYPTO 2018（Tier 1、STARK 論文）
- Groth "On the Size of Pairing-based Non-interactive Arguments" EUROCRYPT 2016（Tier 1、Groth16）
- Gabizon, Williamson, Ciobotaru "PLONK: Permutations over Lagrange-bases" 2019（Tier 1）
- Bünz et al. "Bulletproofs: Short Proofs for Confidential Transactions" IEEE S&P 2018（Tier 1）
- ZKProof Standards: Information-Theoretic Proof Systems Parts I & II（Tier 1、業界標準化団体）
