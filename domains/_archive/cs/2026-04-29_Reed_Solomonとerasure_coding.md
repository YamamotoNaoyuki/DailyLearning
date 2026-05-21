# Reed-Solomon と Erasure Coding ― 分散ストレージの代数学

**日付**: 2026-04-29
**分野**: cs
**タグ**: #ReedSolomon #ErasureCoding #GaloisField #DistributedStorage #ECC

## 学んだこと

### Erasure Code とは何を解く問題か
分散ストレージ（S3, HDFS, Ceph, Backblaze）が直面する問題: **n 台のディスクを使うとき、k 台までの故障に耐えるにはどれだけ冗長性が必要か**。

最も単純な答えは **複製 (replication)**: 同じデータを 3 台に置けば 2 台までの同時故障に耐える。コスト: 3x。これが HDFS のデフォルト戦略だった。

しかし大規模ストレージでは 3x のオーバヘッドは経済的に重い。**Erasure code** はこの問題を符号理論で解く: **k 個のデータブロックに対し m 個のパリティブロックを足す**ことで、合計 n = k+m 個のうち**任意の k 個が残れば**元データを復元できる (Maximum Distance Separable, MDS 性質)。

例: k=10, m=4 なら、10 個のデータブロックを符号化して 14 個に。任意の 4 ブロック故障まで耐え、ストレージ効率は **n/k = 1.4x**（複製の 3x より大幅に省スペース）。これが大規模クラウドストレージで標準採用される理由である。

### Reed-Solomon 符号 ― 1960 年の発明、現代の主役
**Reed-Solomon 符号** は Irving Reed と Gustave Solomon が 1960 年に MIT Lincoln Laboratory で発明した誤り訂正符号で、当時は深宇宙通信（ボイジャー）や CD のスクラッチ訂正のために設計された。21 世紀になって、QR コード、衛星通信、そして**分散ストレージ**で復活した。

Reed-Solomon の数学的本質はこうだ: **k 個のデータシンボル**を係数とする多項式 P(x) を考える。この多項式を n 点で評価することで n 個のシンボルを得る:

```
P(x) = d_0 + d_1·x + d_2·x² + ... + d_{k-1}·x^{k-1}
評価点: P(α_0), P(α_1), ..., P(α_{n-1})
```

ラグランジュ補間の理論より、**任意の k 点が分かれば多項式は一意に決まる**。だから n 個のうち k 個が残れば（残りは消失 = erasure として扱う）、**多項式を再構成して元データ d_0...d_{k-1} を復元できる**。これが MDS 性質の代数的根拠である。

### Galois Field ― なぜ通常の演算ではダメか
ところで「シンボル」とは何か? バイト（8 ビット）として扱いたい。しかし通常の整数演算（mod 256）には**逆元の問題**があり、ラグランジュ補間が成立しない。

そこで **有限体 GF(2⁸)**（ガロア体、Galois Field）を使う:

- 要素は 0〜255（バイト）
- **加算 = XOR**: a ⊕ b
- **乗算は既約多項式 mod**: バイトを GF(2)[x] の 8 次未満多項式とみなし、既約多項式（典型例: x⁸+x⁴+x³+x+1, AES 標準）で割った余り

GF(2⁸) では:
- **加法逆元** = 自分自身（XOR で消える）
- **乗法逆元**は常に存在（0 以外）― これが体の定義
- 演算は**閉じている**（256 元の中で完結）

具体例: GF(2⁸) で 0xAB ⊗ 0x07 を計算するには、0xAB と 0x07 を多項式表現に変換し、多項式積を取り、既約多項式 0x11D で剰余を取る。実装ではこれを **対数表 (log table) と逆対数表 (anti-log table)** で高速化する。

### 符号化の手順 ― 行列表現
実装では多項式評価を**行列乗算**として表現する。**Vandermonde 行列**または **Cauchy 行列** を生成行列 G とし:

```
G · d = c
[I_k]      [d]      [d]
[V  ] · [d] →  [Vd]
```

ここで I_k は単位行列（データはそのままコピー）、V は m×k のパリティ行列。これにより **systematic code**（データ部分が改変されずに残る符号）になる。

復号: n 個のうち欠落していない k 個の行を選んで部分行列 G' を作る。G' は k×k で正則（Vandermonde の性質より）なので **逆行列** G'⁻¹ を計算し、d = G'⁻¹ · c' で復元。これが Reed-Solomon の実装の核心である。

### 計算量とハードウェア最適化
Reed-Solomon の符号化・復号で支配的な計算は GF(2⁸) 上の行列乗算。素朴に実装すると:

- **GF 乗算**: O(1) だが大量に発生
- **符号化**: O(k·m·N) （N はファイルサイズ）
- **復号**: O(k³) （行列逆元）+ O(k·N)（再計算）

実用上のボトルネックは GF 乗算の頻度。これを高速化する技法:

1. **Log/Antilog テーブル**: a·b = antilog(log(a) + log(b))。256 エントリのテーブル参照×2＋加算
2. **SIMD 命令**: Intel SSSE3 の `PSHUFB`, AVX2 の `VPSHUFB` で 16〜32 バイトの GF 乗算を 1 命令で
3. **CLMUL 命令**: PCLMULQDQ で 64 ビットの carry-less multiplication が直接可能
4. **GF-Complete (Plank et al.)**: 最適化された GF ライブラリ。実装によって**数十倍の性能差**

クラウドストレージ規模では符号化スループットが直接コストになるため、CPU レベル最適化が重要。実用ライブラリとして **Klaus Post の reedsolomon** (Go), **Intel ISA-L** (C, AVX-512 対応) が広く使われる。

### Reed-Solomon vs LRC (Local Reconstruction Code)
RS の弱点: **修復に k 個のブロックが必要**。1 ノード故障の修復にも k ノードからネットワーク帯域を使う。クラウドではこの**修復帯域**が問題になる。

**Locally Repairable Codes (LRC)** はこの問題を解く。Microsoft Azure が論文 (Huang et al., 2012) で発表した方式:
- データを複数のローカルグループに分け、各グループに**ローカルパリティ**を追加
- 1 ノード故障の修復は**そのグループ内**で完結（k より少ないブロックで OK）
- グローバルパリティは複数同時故障時のみ使用

Azure Storage は LRC(12, 2, 2) を採用: 12 データ + 2 ローカル + 2 グローバル = 16 ブロック。1 ノード故障は 6 ブロックで修復可能。RS なら 12 ブロック必要だった。

Facebook (Meta) の **Xorbas** や Hadoop 3 の Erasure Coding 実装も LRC 系。**修復コストとストレージ効率のトレードオフ**を実装で調整するのが実運用上の鍵。

### 実装事例 ― Backblaze, S3, HDFS
- **Backblaze Reed-Solomon**: k=17, m=3。20 ドライブのうち 17 から復元可能。同社の自家製ストレージポッドで採用
- **AWS S3 Standard**: 公式には非公開だが、k+m が 12+4 や 14+4 程度の RS と推測されている。"11 nines" の耐久性 (99.999999999%) を達成
- **HDFS Erasure Coding (3.0+)**: RS-6-3 や RS-10-4。Replicaton と並行運用可能
- **Ceph**: プラグイン式で RS, LRC, Shingled (SHEC) を選べる
- **Storj, Filecoin** などの分散ストレージプロトコル: RS と XOR ベースの fountain codes を組み合わせる場合も

### Fountain Codes との比較
**Fountain codes / LT codes / Raptor codes** は確率的な「**長さ無制限の符号語列**」を生成し、受信者は十分な数を集めれば復元できる方式。

- **Reed-Solomon**: n が固定、k 個ぴったりで MDS
- **Fountain**: 符号語数 N は無制限、k(1+ε) 個でほぼ確実に復元

ストレージの場合、**ブロック数が固定で MDS が望ましい**ため RS が好まれる。一方、ネットワークでパケット損失をブロードキャストで補償する用途では fountain codes が優位。

### Erasure code 採用の経済学
Backblaze の数字を引用すると、3 倍複製の HDFS から RS-17-3 に移行することで:
- ストレージコスト: **3.0x → 1.18x**（約 60% 削減）
- 故障耐性: **2 ノードまで → 3 ノードまで**（3 倍複製は 2 ノード喪失で復元不可）
- CPU コスト: 符号化・復号の計算負荷増（数 % 増程度）
- ネットワークコスト: 修復時の帯域大幅増

数百 PB のスケールで運用すると、**ストレージ削減のメリットが CPU/ネットワークコストを大幅に上回る**。これが現代クラウドストレージで erasure code が標準化された経済的根拠である。

## 気づき・洞察

Reed-Solomon の真の美しさは「**データを多項式の係数として見る**」という抽象化の暴力性にある。バイト列を**代数的対象**に持ち上げ、**任意の k 点で完全に決まる**という多項式の数学的性質を使ってデータを再構成する。これは情報理論と代数の婚姻の頂点で、1960 年に発明されたとは思えないほど「現代的」な発想である。

注目すべきは、**同じ Reed-Solomon が CD のスクラッチ訂正・QR コード・深宇宙通信・分散ストレージという全く異なる文脈で使われている**こと。これは「**抽象化の力**」を示す好例で、「erasure（消失）」という抽象が、物理的に異なる失敗モード（読み取り誤り、データ損傷、ノード障害）を統一的に扱える。**理論はインフラを横断する**。

GF(2⁸) という有限体の発見もまた興味深い。連続的な実数体で考えると不可能なこと（XOR が加法、ビット長が固定）が、**離散的な有限体**ではきれいに成立する。コンピュータが本質的に有限離散的なシステムであることを思えば、有限体は計算機科学の自然な代数的言語である。AES 暗号も RS 符号も同じ GF(2⁸) を使う ― 暗号と符号化は同じ代数構造の双子のような関係。

最後に深い洞察。**erasure code は冗長性の効率化**だが、これは情報の本質と関わる。Shannon の **チャネル容量定理**（昨日の cs エントリ "Shannon情報理論" の延長）は、雑音のあるチャネルで信頼できる通信の理論限界を与える。RS code はその限界に向けて構築された具体的アルゴリズムの一族であり、**理論的限界 (Shannon limit) と実装可能性 (RS の構造) のギャップを埋める作業が符号理論の歴史**そのものである。LDPC や turbo codes でこのギャップはほぼ埋まったが、それでも**ストレージという特定の文脈ではシンプルな RS が依然として最適解**であり続けている。

## 他分野との接続

- **cs / Bloom Filter** (2026-04-28): どちらも「**冗長性で確率的・代数的に情報を保護する**」発想。Bloom は false positive を許容、erasure code は損失を許容して計算可能性を保つ
- **cs / Shannon情報理論** (2026-04-25): チャネル容量定理が erasure code の理論的限界を与える。実装は限界への漸近的接近
- **cs / MVCC** (2026-04-27): バージョン保持と冗長性は両方「**過去の状態を構造化保存**」する技法。MVCC は時間軸、erasure code は空間軸
- **tech / Apache Iceberg** (今日): Iceberg のデータレイヤは erasure code（S3 内部）の上に構築されている。階層化されたストレージの抽象
- **anatomy / 腱とコラーゲン** (今日): 腱の階層的繊維構造も「冗長性による頑健性」 ― 一部のフィブリル損傷が全体に伝播しないように設計されている。生物学的 erasure code

## 次に深掘りしたいこと

- **LDPC codes と Quantum Error Correction** ― 量子計算の文脈での誤り訂正符号。surface code は erasure code の量子版
- **Network Coding** ― ストレージではなくネットワークでの符号化。ノード間で符号化されたパケットを中継する
- **Storage Tiering と erasure code parameter tuning** ― ホットデータは複製、コールドデータは RS という階層化戦略

## 参考ソース

- [Plank, J. S. (2013). Erasure Codes for Storage Systems (USENIX ;login:)](https://www.usenix.org/system/files/login/articles/10_plank-online.pdf) — Tier 1: USENIX 公式
- [Wicker, S. & Bhargava, V. (2018). The Comeback of Reed Solomon Codes (IEEE)](https://ieeexplore.ieee.org/document/8464690/) — Tier 1: IEEE 査読
- [Plank, J. S. & Greenan, K. (2013). Accelerating Galois Field Arithmetic for RS Erasure Codes (IEEE)](https://ieeexplore.ieee.org/document/6061147/) — Tier 1: IEEE 査読
- [Reed-Solomon error correction (Wikipedia)](https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction) — Tier 2: 概要把握
- [klauspost/reedsolomon (GitHub) — Go 実装](https://github.com/klauspost/reedsolomon) — Tier 2: 実装参照
- [Erasure Coding for Distributed Systems (transactional.blog, 2024)](https://transactional.blog/blog/2024-erasure-coding) — Tier 2: 専門エンジニア記事
