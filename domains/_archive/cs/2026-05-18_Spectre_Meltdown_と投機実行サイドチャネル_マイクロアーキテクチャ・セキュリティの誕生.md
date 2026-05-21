# Spectre/Meltdownと投機実行サイドチャネル：マイクロアーキテクチャ・セキュリティの誕生
**日付**: 2026-05-18
**分野**: cs
**タグ**: #spectre #meltdown #side_channel #speculative_execution #microarchitecture #security

## 学んだこと

### 2018年1月3日：CPUセキュリティ史の地殻変動
2018年1月3日、Paul Kocher、Jann Horn(Google Project Zero)、Daniel Genkin、Moritz Lipp、Yuval Yaromらの研究者グループが**Meltdown**(CVE-2017-5754)と**Spectre**(CVE-2017-5753, 5715)を公開した。これは現代CPU設計の根本的前提を覆す発見だった。

それまでセキュリティ研究は「メモリ保護、特権分離、暗号アルゴリズム」を中心に進んできた。Meltdown/Spectre は、これらすべてが正しく実装されていても、**マイクロアーキテクチャレベルでの情報漏洩**が起きることを示した。CPUの内部実装(キャッシュ、分岐予測器、投機実行ユニット)が攻撃面になる新時代の幕開け。

### 投機実行(Speculative Execution)とは
1990年代以降、CPUの性能向上はクロック速度ではなく**並列性の発掘**で達成されてきた。投機実行はその中核技術：

```c
if (x < array1_size)
    y = array2[array1[x] * 4096];
```

CPUは`x < array1_size`の結果を待たずに、**両方の分岐を投機的に実行**する。`array1_size`の値がキャッシュにあれば分岐結果は数サイクルで確定するが、メインメモリからのフェッチには数百サイクルかかる。この間に投機実行を進めておけば、結果が正しかった場合、その分の計算は無駄にならない。

予測が外れた場合、結果は破棄(retire されない)される。アーキテクチャ状態(レジスタ、メモリ)は変更されない——**ように見える**。しかし**マイクロアーキテクチャ状態**(キャッシュ、分岐予測器、TLB等)は変化したまま残る。これが攻撃の核心。

### Meltdown(CVE-2017-5754)：Intel特権境界の崩壊
Meltdownは**Intelに特有**(後にARM Cortex-A75にも)の脆弱性。動作原理：

1. ユーザーモードのプロセスが、カーネルメモリへの不正アクセスを試みる
2. CPUは投機実行で先にロードし、その後例外を検出して破棄
3. **しかし破棄前に、ロードした値に基づくキャッシュアクセスが実行されている**
4. キャッシュタイミング攻撃(Flush+Reload)で、どのキャッシュラインが温まったかを観測
5. 観測されたキャッシュ状態から、不正アクセスしたカーネルメモリの内容を再構成

```c
// 攻撃の擬似コード
char* kernel_addr = 0xffff8800_00000000;  // カーネル空間
char secret = *kernel_addr;               // 例外発生(投機実行は通る)
volatile int dummy = probe_array[secret * 4096];  // キャッシュに痕跡
// → catch例外
// → probe_array の各エントリへのアクセス時間を測定
// → 最も速いエントリのインデックスが secret
```

Intel CPUは「例外チェックを延期して投機実行を続行する」設計。これが攻撃を可能にした。AMDは例外チェックを早期に行う設計だったため、Meltdownには脆弱でなかった。

### Spectre(CVE-2017-5753, 5715)：プロセス間境界の崩壊
Spectreはより汎用的で、Intel/AMD/ARM/IBM Power のほぼすべてのCPUに影響。2つのバリエーション：

#### Variant 1: Bounds Check Bypass (CVE-2017-5753)
分岐予測器を「訓練」して、配列境界チェックを通過させる：

```c
if (x < array1_size)         // この条件を「真」と予測させる
    y = array2[array1[x] * 4096];
```

攻撃者は何度も`x`を範囲内の値で呼び出し、分岐予測器に「真」と学習させる。その後、`x`を範囲外(秘密データのオフセット)にして呼ぶと、CPUは「真」と予測して投機実行し、`array1[x]`の値を読み出してキャッシュに痕跡を残す。

#### Variant 2: Branch Target Injection (CVE-2017-5715)
間接ジャンプの予測先(BTB, Branch Target Buffer)を毒する。攻撃者は自分のコードで特定アドレスへのジャンプを訓練し、被害プロセスが同じCPU上で間接ジャンプを実行する際、攻撃者の意図したコードに「投機実行で」分岐させる。

これにより、犠牲プロセス(別ユーザー、別VM、別コンテナ)のアドレス空間を読み出せる。クラウド環境の同居VM間で機密情報を盗む攻撃に応用可能。

### サイドチャネルの古い系譜
Meltdown/Spectreは「投機実行」という新要素だが、**サイドチャネル攻撃自体はPaul Kocher が1996年に既に提案していた**(Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS, and Other Systems)。
Kocherの1996論文は、RSAの秘密鍵を計算時間の差から推定する方法を示した。これがpower analysis attacks(電力消費分析), cache attacks, branch prediction attacks へと発展。20年後にMeltdown/Spectreでマイクロアーキテクチャ全体に拡張された。

### Flush+Reload：キャッシュタイミング測定の原理
攻撃の「測定」部分は、**Flush+Reload**技法を使う：

1. **Flush**: 攻撃者が`clflush`命令で`probe_array`の全エントリをキャッシュからフラッシュ
2. **Victim**: 投機実行で`probe_array[secret * 4096]`がキャッシュにロード
3. **Reload**: 攻撃者が`probe_array`の各エントリを`rdtscp`命令で時間測定しながらアクセス
4. **判定**: 最も短時間でアクセスできたエントリのインデックスが`secret`

「4096を掛ける」のは、L1キャッシュのラインサイズ(64バイト)を遥かに超えてエントリを散らすため。隣接したエントリにすると、ハードウェアプリフェッチが攻撃を撹乱する。

### 緩和策(Mitigation)とその代償

#### KPTI (Kernel Page Table Isolation)
旧称KAISER。Meltdownへの対策。ユーザーモードとカーネルモードで**別のページテーブル**を使う。これによりカーネル空間がユーザープロセスから物理的に隔離される。
代償：システムコールごとにページテーブル切替(TLBフラッシュ含む)が必要 → I/O集約的なワークロードで**5-30%の性能低下**。

#### Retpoline (Google)
Spectre Variant 2への対策。間接ジャンプを「return trampoline」に置き換える：
```asm
; 元: jmp *%rax
; Retpoline版:
call set_up_target  ; リターンアドレスをスタックに積む
set_up_target:
    mov %rax, (%rsp)
    ret  ; リターンアドレス(攻撃者が制御不能)を使う
```
分岐予測器ではなく**Return Stack Buffer (RSB)**を使う形に書き換える。RSBは攻撃で訓練しにくい構造のため、安全。

#### IBRS, IBPB, STIBP
- **IBRS (Indirect Branch Restricted Speculation)**: より高い特権レベルへ移行する際に分岐予測状態をクリア
- **IBPB (Indirect Branch Predictor Barrier)**: コンテキストスイッチ時に分岐予測器をフラッシュ
- **STIBP (Single Thread Indirect Branch Predictors)**: SMTでスレッド間の分岐予測器共有を禁止

これらはマイクロコード更新で提供されるが、いずれも性能低下を伴う。

#### LFENCE/SFENCE 挿入
Variant 1への対策。境界チェックの直後に`lfence`命令を挟むことで、投機実行をシリアライズ。コンパイラ(MSVC, GCC, Clang)が自動挿入するモードを提供。

### 後続の発見：MDS, ZombieLoad, Foreshadow, RIDL...
Meltdown/Spectreは「氷山の一角」だった。2018-2020年に類似の脆弱性が大量に発見された：
- **Foreshadow (L1TF)**: L1キャッシュからの投機的読み出し
- **ZombieLoad/MDS**: Microarchitectural Data Sampling, ロードバッファからの漏洩
- **RIDL, Fallout**: ストアバッファ/フィルバッファからの漏洩
- **CrossTalk**: コア間でのレジスタ漏洩
- **PACMAN**: Apple M1のPointer Authenticationの突破

これらはすべて**「マイクロアーキテクチャの内部状態が、特権境界を超えて観測可能」**という共通テーマを持つ。

### Intelの設計哲学の修正
Meltdown後、Intelは新世代CPU(Cascade Lake以降)で「Meltdown耐性」をハードウェアで実装するようになった。さらにIce Lake以降では**CET (Control-flow Enforcement Technology)**、Sapphire Rapids以降では**Intel TDX (Trust Domain Extensions)** など、ハードウェアセキュリティ機能が拡充されている。
これは2018年以前の「性能優先・セキュリティは抽象化レイヤーが守る」哲学から、「ハードウェアもセキュリティに責任を持つ」哲学への大転換。

## 気づき・洞察

### 「正しさ」の定義が変わった
Meltdown以前、CPUの「正しさ」とはアーキテクチャ仕様(ISA)に対する忠実さだった。投機実行で発生するキャッシュ状態の変化は「観測不可能」と扱われていた。
しかしMeltdownは、その「観測不可能」が**間接的に観測可能**であることを示した。これはコンピュータサイエンスのセマンティクスにおける根本的問題——**「副作用なし」の定義をどこまで厳密にするか**という問い。
形式手法(昨日学んだTLA+)で投機実行の正しさを記述する難しさは、まさにこの「観測モデル」の問題に直結する。

### 「速さ」と「安全」の根本的トレードオフ
過去25年のCPU性能向上は、投機実行、out-of-order、分岐予測、巨大キャッシュ——いずれも「予測して先取りする」技術に依存してきた。
Meltdown/Spectreが示したのは、**これら「先取り」の本性が、本質的にサイドチャネル攻撃面である**こと。完全な対策は「投機実行を諦める」しかなく、それは1990年代のCPU性能に戻ることを意味する。
結果として、現実は「許容可能なリスクと許容可能な性能低下のバランス」を選び続ける。これは暗号工学における「Provably secure vs Practically secure」のトレードオフと同型。

### Domain-specific security の必要性
クラウド事業者(AWS, GCP, Azure)はMeltdown/Spectre対応に巨額のコストを払い、しばらくは「同居テナント」の境界が信用できない状態だった。これは「マルチテナントCPUは本質的に危険」という新しい認識を生み、**Confidential Computing**(2026-04-25のtech学習)や**専用ハードウェアアクセラレータ**(AWS Nitro, Google Asylo)への投資を加速させた。

## 他分野との接続

- **tech（Confidential Computing/TEE）**: Meltdown/Spectreが「マルチテナント環境の脆弱性」を露呈したことで、TEEの重要性が増した
- **cs（暗号・サイドチャネル）**: 1996年のKocherのタイミング攻撃が20年越しに花開いた——研究の長期的価値
- **cs（MESIキャッシュ整合性 4/30）**: キャッシュ共有こそが攻撃面。整合性プロトコルの理解はサイドチャネル防御の基盤
- **tech（TigerBeetleとDST）**: 「決定論性」を保証する設計は、サイドチャネル攻撃の実行時挙動の分析にも応用可能
- **anatomy（CPG）**: 「投機的に並行に動かす」マイクロアーキテクチャは、CPGが「外部入力を待たずに動く」のと構造的に似ている
- **bread（時間窓）**: 投機実行の「windowが閉じる前に観測する」攻撃は、オーブンスプリングの「時間窓」と似た時間構造を持つ

## 次に深掘りしたいこと
- ARM v9 アーキテクチャのMTE (Memory Tagging Extension) とその限界
- 投機実行を完全に放棄したCPUの提案(SafeSpec, InvisiSpec) と性能評価
- 量子CPU(超伝導量子ビット)のサイドチャネル耐性——古典CPUの教訓は通用するか

## 主要参考ソース
- [Spectre Attacks: Exploiting Speculative Execution (Kocher et al., 2018)](https://spectreattack.com/spectre.pdf)
- [Meltdown and Spectre - 公式サイト](https://meltdownattack.com/)
- [Spectre attacks: exploiting speculative execution - Communications of the ACM](https://dl.acm.org/doi/10.1145/3399742)
- [Spectre (security vulnerability) - Wikipedia](https://en.wikipedia.org/wiki/Spectre_(security_vulnerability))
- [How the Spectre and Meltdown Hacks Really Worked - IEEE Spectrum](https://spectrum.ieee.org/how-the-spectre-and-meltdown-hacks-really-worked)
- [Meltdown and Spectre Side-Channel Vulnerability Guidance - CISA](https://www.cisa.gov/news-events/alerts/2018/01/04/meltdown-and-spectre-side-channel-vulnerability-guidance)
- Kocher, P. (1996). "Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS, and Other Systems." *CRYPTO '96.*
