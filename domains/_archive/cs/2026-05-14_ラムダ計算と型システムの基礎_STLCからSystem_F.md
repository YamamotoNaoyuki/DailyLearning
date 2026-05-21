# ラムダ計算と型システムの基礎 ― STLC から System F、Curry-Howard へ
**日付**: 2026-05-14
**分野**: cs
**タグ**: #LambdaCalculus #TypeTheory #SystemF #CurryHoward #ProofTheory

## 学んだこと

### ラムダ計算 ― 計算の最小エッセンス
**ラムダ計算 (λ-calculus)** は Alonzo Church が **1932-1936 年**に導入した、関数定義と適用だけで計算を表現する形式系。3 つの構成要素：
1. **変数**: x, y, z, …
2. **抽象**: λx. M（「x を受け取って M を返す関数」）
3. **適用**: M N（「関数 M に引数 N を渡す」）

これだけで **チューリング完全**――再帰、データ構造、論理、自然数のすべてが Church 符号化で表現できる。**「計算とは関数適用そのものである」** という哲学が λ-calculus の核心で、関数型プログラミング（Lisp, Haskell, OCaml, F#, Scala）の理論的基盤。

**β-簡約 (β-reduction)**：(λx. M) N → M[x := N]――関数適用を変数置換に還元する。この操作の繰り返しが「計算」。

### 型なしラムダ計算のパラドックス
Church の元々の動機は **形式論理の基礎**を作ること。しかし型なしラムダ計算では **自己適用 (self-application)** が許される：

Ω = (λx. x x)(λx. x x)

これは無限に β-簡約し続け、停止しない。さらに **Curry のパラドックス**：(λx. x x)(λx. x x) は **論理として解釈すると矛盾を導く**。Russell のパラドックスの λ 計算版。

**型システムはこのパラドックスを排除する装置**として誕生した。

### 単純型付きラムダ計算 (STLC, Simply Typed Lambda Calculus)
Church が **1940 年**に導入した STLC は、各項に **型 (type)** をつける：
- 基本型: σ, τ（例: Int, Bool）
- 関数型: σ → τ（「σ を受け取って τ を返す関数」の型）
- 型付け規則:
  - 変数: Γ ⊢ x : σ if (x : σ) ∈ Γ
  - 抽象: Γ, x : σ ⊢ M : τ ⟹ Γ ⊢ λx : σ. M : σ → τ
  - 適用: Γ ⊢ M : σ → τ, Γ ⊢ N : σ ⟹ Γ ⊢ M N : τ

STLC では **(λx. x x)** が型付けできない（x は σ → τ かつ σ という二つの型を同時に持つ必要があり矛盾）。**自己適用を構文レベルで排除**することで、すべての項が **強正規化 (strong normalization)** ―― 任意の簡約順序で必ず停止 ―― という性質を持つ。

**強正規化定理 (Tait 1967)**：STLC の任意の項は有限ステップで正規形に到達する。**つまり STLC ではチューリング完全性を失う代わりに停止性を獲得**――これがプログラミング言語型システムの基本トレードオフ。

### Curry-Howard 同型対応 ― プログラム = 証明
Curry (1934) と Howard (1969) が独立に発見した **計算と論理の構造同型**：

| プログラミング側 | 論理側 |
|---------------|-------|
| 型 σ | 命題 σ |
| 項 M : σ | σ の証明 M |
| 関数型 σ → τ | 含意 σ ⇒ τ |
| 直積型 σ × τ | 連言 σ ∧ τ |
| 直和型 σ + τ | 選言 σ ∨ τ |
| 空型 ⊥ | 偽 ⊥ |
| 関数適用 | Modus Ponens |
| β-簡約 | 証明の正規化 |

**「型を持つプログラムを書くこと」と「命題を直観主義論理で証明すること」は同じ操作**。これは数学基礎論と計算理論を貫く深い橋。Coq、Lean、Agda などの定理証明支援系はこの対応を基盤に実装される。

### 多相性の必要性 ― STLC の限界
STLC では `λx. x`（恒等関数）も `λx : Int. x` と `λx : Bool. x` が別の項で、**型ごとに同じコードを書き直す**必要がある。これは **アドホック多相 (ad-hoc polymorphism)** の不経済。

**解決策**: 型自体を変数として量化する → **System F**。

### System F ― 第二階ラムダ計算
**System F**（Jean-Yves Girard, 1972 / John Reynolds, 1974 が独立に発見）は STLC に **全称型 ∀X. τ** を追加する：

- 型抽象: ΛX. M : ∀X. τ（「型 X を受け取って M を返す」）
- 型適用: M [σ]（「∀X. τ の M に型 σ を渡して τ[X := σ] にする」）

恒等関数は：

id = ΛX. λx : X. x : ∀X. X → X

`id [Int] 5 = 5`、`id [Bool] True = True`――**一つの定義で多型に動く**。これが **パラメトリック多相 (parametric polymorphism)** ――Haskell、ML、Rust、Java Generics の基盤。

### System F の表現力
System F は STLC を厳密に拡張し、以下を表現できる：
- **Church 符号化された自然数・リスト・木**などの代数的データ型
- **存在型 ∃X. τ**（モジュール/抽象データ型）
- **多相恒等関数、map、fold** などの高階多相関数

しかも **強正規化性は保持される**（Girard 1971 の証明、後に Tait, Krivine が改善）。STLC ほどの簡潔さは失うが、表現力と停止性のバランスが優れる。

### 型推論不可能性 ― System F の代償
System F の致命的欠点：**型推論が決定不能 (undecidable)**（Wells 1994）。Hindley-Milner システム（ML, Haskell）は System F のサブセット（**rank-1 polymorphism** のみ、∀ がトップレベルにのみ現れる）に制限することで型推論可能性を回復した [[Hindley_Milner型推論とlet多相]]。

Haskell の **Rank-N Types** 拡張は System F に近づくが、型推論を諦め型注釈を要求する。**「型推論可能性 vs 表現力」**の根本トレードオフ。

### System F の上位系 ― System Fω と Calculus of Constructions
- **System Fω**：型レベルで関数（型コンストラクタ）も多相化。Haskell の type families の基盤
- **依存型 (dependent types)**：型が値に依存（例: `Vector n` のように長さ n を型に含む）。Coq, Lean, Agda, Idris
- **Calculus of Constructions (CoC)**（Coquand & Huet, 1988）：System Fω + 依存型。Coq の理論基盤。**Curry-Howard が高階直観主義論理まで拡張**

### 実用言語への現れ
- **Haskell**: ベースは Hindley-Milner、拡張で System F、System Fω、依存型に近づける
- **Rust**: System F 風の generics + trait（型クラス、ad-hoc 多相）+ ライフタイム（線形/affine 型の影響）
- **Scala**: System Fω 相当の higher-kinded types、暗黙引数で type class エミュレート
- **Java/C# Generics**: rank-1 多相のみ、しかも **type erasure**（実行時に型情報が消える）――System F の弱められた形

### Calculus of Constructions と CoC
CoC は λ-calculus 階層の極限：
- 値の関数（普通の関数）
- 値から型を作る関数（依存型）
- 型から型を作る関数（type constructors）
- 型から値を作る関数（型クラスインスタンス）

これらすべてが **一つの統一構文**で表現される。Coq、Lean が理論基盤として採用。**数学の証明を機械検証可能にする道具**で、Four Color Theorem (Gonthier 2008)、Feit-Thompson Theorem (Gonthier 2012) など歴史的証明の形式化に使われた。

### 最新動向 ― 線形型と量子計算
**線形型 (Linear types)**（Girard 1987）：変数を **正確に 1 回だけ使う**ことを型で強制する。Rust の所有権モデル、Haskell GHC の Linear Haskell 拡張、量子プログラミング言語（Qiskit, Q#）の基盤。「リソースを使い切る」プログラミングを型で保証する。

**Quantitative Type Theory** (McBride, 2016)：使用回数を 0, 1, ω の三段階で扱う一般化。Idris 2 が採用。**「計算資源そのものを型で管理する」**未来。

## 気づき・洞察

- **「型システムは禁止の体系」という見方**——型システムは「**ある種のプログラムを書けなくする**」装置。STLC は自己適用を禁じ、強正規化を得る。System F は表現力を増し、型推論を失う。**増えるのは表現、失われるのは決定可能性**――これはほぼ普遍的トレードオフ
- **「Curry-Howard は装飾ではなく本質」**——「型 = 命題、プログラム = 証明」は教養的アナロジーに見えるが、**実は型システム設計の本来の駆動力**。論理が許す推論規則だけを言語に許せば、型システムは健全性 (soundness) を自動的に得る。**論理学が型システム設計の最終仲裁者**
- **「System F の表現力」の謎**——わずか「型を変数化する」だけで Church 符号化された自然数・リスト・木が表現可能になる事実は深い。**変数化が新しい言語を作る**――抽象化の真の力。**言語の表現力は構文の数ではなく抽象化の段数で決まる**
- **「型推論不可能性」の意味**——System F が「型推論不能」というのは「機械が型を見つけられない」だけで、「人間が書けばコンパイル通る」。**自動化の限界が表現力の上限を決める**ことは、言語設計の現代的制約。AI 補助の型推論はこの境界を押し広げつつある
- **「依存型は数学そのもの」**——Coq/Lean では「自然数とは何か」を語る型と「自然数のリストとは何か」を語る型が連続的につながる。**ZF 集合論なしで数学を再構築**する試みが進行中（Univalent Foundations, Homotopy Type Theory）

## 他分野との接続

- **piano (内的聴感)**: 音楽の意味論的「型システム」――各音にメタ情報（機能・調性内の役割・音色目標）が型として付随する。「鳴らせる音」と「鳴らせない音」の文法的判断は、コンパイラの型検査に対応
- **anatomy (多裂筋と脊柱起立筋)**: 「ローカル」と「グローバル」の二層構造は、STLC の **rank-1 多相**（局所的）と System F の **任意 rank**（全体的）の構造に対応。**スコープと粒度の階層**は身体にも言語にも現れる
- **tech (Apache Arrow)**: Arrow のスキーマは「型システムの実体化」。RecordBatch は **型注釈付き λ-項**――値とその型の対が運ばれる
- **music (モーツァルト K.488 ギャラント様式)**: ギャラント様式は「許される進行と禁じられた進行」の **音楽の型システム**――4 度進行、解決規則、終止形式。型システムの簡潔さが優雅な音楽を生む
- **golf (傾斜地ライ)**: 「**フォームを変えず傾斜にフォームを合わせる**」は、関数を多相化（傾斜という型パラメータで abstracting）する操作の物理版
- **other (ペルシャ絨毯)**: 絨毯の文様の組み合わせ規則は「絨毯デザインの型システム」――組合せ論的な「型」が幾何学的意味を担う

## 次に深掘りしたいこと

- Homotopy Type Theory (HoTT) と Univalent Foundations の数学基礎論的意味
- 線形型と所有権モデル：Rust の borrow checker は System F の何を継承しているか
- Lean 4 vs Coq vs Agda の設計思想比較（自動化、戦術言語、依存型の表現力）
- 機械学習における型システム（PyTorch の TensorType, JAX の dtype）と System F の関係

---

## 参考ソース
- Pierce, B. C., *Types and Programming Languages* (MIT Press, 2002) (Tier 1: 標準教科書)
- Girard, J.-Y., Lafont, Y., & Taylor, P., *Proofs and Types* (Cambridge UP, 1989) (Tier 1)
- Reynolds, J. C. (1974). "Towards a theory of type structure." *Lecture Notes in Computer Science* 19, 408–425. (Tier 1)
- [Simply typed lambda calculus (Wikipedia)](https://en.wikipedia.org/wiki/Simply_typed_lambda_calculus) (Tier 2)
- [System F (Wikipedia)](https://en.wikipedia.org/wiki/System_F) (Tier 2)
- [CS345H: Polymorphism and System F (UT Austin)](https://www.cs.utexas.edu/~bornholt/courses/cs345h-24sp/lectures/8-system-f/) (Tier 1: 大学講義)
- Software Foundations Volume 2 (Pierce et al.) [Plf-Stlc](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html) (Tier 1)
