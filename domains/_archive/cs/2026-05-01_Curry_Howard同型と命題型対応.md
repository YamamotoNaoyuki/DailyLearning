# Curry-Howard 同型 — 命題は型、証明はプログラム
**日付**: 2026-05-01
**分野**: cs
**タグ**: #CurryHoward #型理論 #ラムダ計算 #直観主義論理 #依存型

## 学んだこと

### 中心命題：Propositions as Types
**Curry-Howard 対応** (Curry-Howard correspondence / isomorphism) は、**論理学の命題と型理論の型、論理証明とプログラム、証明の正規化と計算の評価が一対一に対応する**という驚くべき同型構造を主張する。

最小限の標語：
- **命題 (proposition) ↔ 型 (type)**
- **証明 (proof) ↔ プログラム/項 (term)**
- **証明の簡約 (cut elimination, β-reduction in natural deduction) ↔ プログラムの評価 (β-reduction in lambda calculus)**

論理体系と計算体系が「**同じ数学的対象を別の言語で記述しているにすぎない**」という発見である。

### 歴史
**Haskell Curry** が 1934 年、コンビネータ論理 (combinatory logic) と単純型論理 (Hilbert-style implicational logic) の対応に気づいた。当初は **`P → Q` という命題と関数型 `P → Q` の同型**だけが見えていた。

**William Howard** が 1969 年（公刊は 1980 年の Curry 記念論文集）に、**自然演繹 (natural deduction) と単純型ラムダ計算 (simply-typed λ-calculus) が完全に同型**であることを示した。命題演算の論理結合子 ∧, ∨, ⊃ がそれぞれ積型 ×, 直和型 +, 関数型 → に対応する。

**Per Martin-Löf** が 1972 年以降、**直観主義型理論 (Intuitionistic Type Theory, ITT)** で **依存型 (dependent types) と一階述語論理 (∀, ∃)** への拡張を完成させた。これが **Coq, Agda, Lean, Idris** といった証明支援系の理論的基盤。

**Philip Wadler** が 2015 年 Communications of the ACM で "**Propositions as Types**" を発表し、この同型を「Discovery, not Invention（発見であって発明ではない）」として広く知らしめた。

### 対応表
| 論理 (Intuitionistic Logic) | 型理論 (Type Theory) |
|---|---|
| 命題 P, Q | 型 P, Q |
| 含意 P ⊃ Q | 関数型 P → Q |
| 連言 P ∧ Q | 積型 P × Q（タプル） |
| 選言 P ∨ Q | 直和型 P + Q（Either） |
| 真 ⊤ | 単位型 unit (1) |
| 偽 ⊥ | 空型 Void (0, never) |
| 全称 ∀x:A. P(x) | Π型 (x:A) → P(x)（依存関数） |
| 存在 ∃x:A. P(x) | Σ型 (x:A) × P(x)（依存ペア） |
| 推論規則 | 型付け規則 |
| 証明の簡約 | β-reduction |
| 論理的妥当性 | 型可能性 |
| 矛盾の証明 (cut) | 関数適用 |

### 含意の例：MP は関数適用
論理の **Modus Ponens (MP)**：
> P ⊃ Q が真であり、P が真なら、Q が真である。

型理論の関数適用：
> `f: P → Q` と `x: P` から `f(x): Q` が導ける。

両者は同じ操作。「P の証明を Q の証明に変換する手順」と「P 型の値を Q 型の値に変換する関数」は本質的に同じ。

### 例：De Morgan の法則と関数型プログラム
論理：
> ¬(P ∨ Q) ⊃ (¬P ∧ ¬Q)

型理論で書き換え（¬P を `P → ⊥` と定義）：
> `((P + Q) → Void) → ((P → Void) × (Q → Void))`

これを Haskell 風に実装：
```haskell
demorgan :: ((Either p q) -> Void) -> (p -> Void, q -> Void)
demorgan f = ( \p -> f (Left p), \q -> f (Right q) )
```

つまり「**De Morgan の法則の証明＝関数の実装**」。両方を書き、型検査が通れば証明は完成。

### 古典論理 vs 直観主義論理：排中律と call/cc
直観主義論理は **排中律 P ∨ ¬P を公理として持たない**。Curry-Howard 同型は元来この直観主義論理に対応する。

**Griffin (1990)** は古典論理と Scheme の `call/cc` (call-with-current-continuation) との対応を発見した：
- **古典論理の二重否定除去 ¬¬P ⊃ P** ↔ **continuation の操作**
- 排中律 ↔ Felleisen の `C` 演算子

これは **Curry-Howard-Lambek 対応**として一般化され、**論理 = 型理論 = 圏論**の三項同型に拡張された（Lambek の定理：直観主義論理はカルテシアン閉圏に対応）。

### 依存型と Martin-Löf 型理論
**Π型 (dependent function type)**: 入力に依存して出力の型が変わる関数。
```
(n : Nat) → Vector A n
```
これは「**任意の n に対して長さ n のベクトルを返す関数**」を意味し、**全称命題 ∀n. P(n) の証明**でもある。

**Σ型 (dependent pair type)**: ペアの第二要素の型が第一要素に依存する。
```
(n : Nat) × (Vector A n)
```
これは「**ある n が存在して長さ n のベクトルがある**」=**存在命題 ∃n. P(n) の証明**。

### 同一性型 (Identity Type) と Univalence
**Id_A(a, b)**: 「`a` と `b` は等しい」という命題に対応する型。空ではない場合のみ、両者は等しい。

**Voevodsky の Univalence Axiom (2009-)**: 「**同型な型は等しい**」。これは Homotopy Type Theory (HoTT) の中心公理で、ITT の表現力を圏論的同値レベルまで引き上げる。Coq、Agda、Lean、Cubical Agda で実装研究が進む。

### 実用面：証明支援系
- **Coq (1989-)**: フランス INRIA。**4 色定理**（2005, Gonthier）、**Feit-Thompson 定理**（2012）の機械的証明、**CompCert** 検証 C コンパイラ（Leroy 2008–）。
- **Agda (2007-)**: スウェーデンチャルマース工科大学。プログラミング寄り。
- **Lean (2014-)**: Microsoft Research → CMU の de Moura。**mathlib** が爆発的に成長。Tao Terence らの Polynomial Freiman-Ruzsa 予想証明 (2023) で著名。
- **Idris (2011-)**: Edwin Brady。実用プログラミング言語として依存型を使う設計。

### Curry-Howard とプログラミング言語設計
Hindley-Milner（4/24 学習）は単純型ラムダ計算の上に**主型推論**を築いた。Curry-Howard により、HM 型システムは**直観主義論理の含意・全称の断片**に対応する：型推論は **proof search** と同型。

**Linear Logic (Girard 1987)** は資源の使用回数を制御する論理だが、Curry-Howard 経由で **Linear Types (Rust の所有権、Linear Haskell)** に対応する。Rust の借用チェッカは **線形論理の証明検査**。

**Effects, Modal Types, Algebraic Effects** など最近の言語機能は、すべて Curry-Howard の枠組みで整理可能。

## 気づき・洞察

**Curry-Howard 同型は「数学と計算が同じものの 2 つの顔」と言っている**。Pythagoras 以来「数学は宇宙の言語」という直観があるが、Curry-Howard はそれに具体的な形を与えた：**論理は型システム、推論は計算、定理は API、証明は実装**。証明と検証が型検査と等価なら、**安全なソフトウェア = 強い型 = 厳密な命題**。

**「証明は構成である (proof is construction)」**という Brouwer-Heyting-Kolmogorov (BHK) 解釈が、Curry-Howard で本当の意味を獲得する。「P の証明」とは「P 型の値を作る手続き」。これは抽象的な真理保有ではなく、**具体的に何かを作る能力**。だから古典論理の「∃ 証明」は「**存在を主張するが構成しない**」点で、計算的に弱い。

**プログラマがよく知る現象との対応**：
- **null 値の問題**: ある型 T の値が「ないかもしれない」のに T として扱う = 偽から何でも導ける (ex falso quodlibet) を許す = 古典論理。Option/Maybe で明示するのは直観主義の選択。
- **総当たり例外**: catch-all は continuation 操作 = 古典論理の二重否定除去 = ヒルベルト的。
- **総関数 (total functions)**: 全ての入力に終わる関数 = 完全な証明。Idris/Agda は無限ループを禁止する（証明は終わらないと意味がない）。

**Stockhausen のセリエリズムとの平行性**：
- セリエリズム：12 音技法を音価・強度・音色に拡張 → トータル・セリエリズム
- 型理論：単純型を依存型・線形型・モーダル型に拡張 → トータル・依存型理論

両者とも **「公理体系の徹底」が表現力を爆発させる**例。シェーンベルクが調性を諦めて秩序を得たように、ML 言語は副作用を制限して総体的真理性を得た。

**「論理 → プログラム」だけでなく「プログラム → 論理」の方向**: 型を見れば命題が分かる。`forall a b. (a -> b) -> [a] -> [b]` という型を見ると、**自由定理 (free theorems, Wadler 1989)** により実装の選択肢が劇的に絞られる（実は map しかない）。**型がドキュメントになる**は、Curry-Howard の実用的副産物。

## 他分野との接続

- **music (シェーンベルク 12 音)**: 「公理 = ロウ、推論規則 = P/R/I/RI、証明 = 楽曲」というアナロジー。**新しい秩序を構成的に作る**点で同型。
- **tech (MLS の TreeKEM)**: Diffie-Hellman の代数的構造を**型としての KEM**に抽象化することで、PQ-MLS への拡張が可能になった。**型による抽象 = プロトコルの安全な置換**。
- **piano（暗譜の記憶階層）**: 暗譜は「楽譜」を「コンセプチュアル → モーター → アコースティック → 表情」の **4 層に変換する型変換**と見える。
- **anatomy (反射弓・小脳)**: 反射は「**前提 (sensory input) → 結論 (motor output)**」の関数型実装。脊髄反射は単純型関数、小脳の予測モデルは依存型関数。
- **philosophy (道元の正法眼蔵)**: 「修証一等」（修行 = 証明） は「proof = construction」の禅版。**プロセス自体が結果**。
- **golf (DECADE)**: 「目標選択 → 規律 → 実行」は推論ステップの連鎖。各ステップが正しい型で繋がっていればスコアは安定する。

## 次に深掘りしたいこと
- Lean 4 の mathlib 構造を実際に追ってみる
- Linear Logic と Rust 所有権の対応を厳密に追う
- Cubical Type Theory (Cohen et al. 2017) の Univalence の operational 解釈
- Game Semantics (Hyland-Ong) と Curry-Howard の関係
- 実際に簡単な命題（De Morgan）を Coq/Lean で証明してみる

## 主要参考ソース
- [Wadler, "Propositions as Types" (Communications of the ACM 2015)](https://cacm.acm.org/research/propositions-as-types/) - 包括的な解説
- [Curry-Howard correspondence - Wikipedia](https://en.wikipedia.org/wiki/Curry%E2%80%93Howard_correspondence)
- [Lectures on the Curry-Howard Isomorphism (Sørensen, Urzyczyn)](https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf) - 教科書PDF
- [Curry-Howard Isomorphism - Harvard CS152 Lecture Notes](https://groups.seas.harvard.edu/courses/cs152/2015sp/lectures/lec15-curryhoward.pdf)
- [Intuitionistic Type Theory - Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/type-theory-intuitionistic/) - 哲学的・数学的背景
