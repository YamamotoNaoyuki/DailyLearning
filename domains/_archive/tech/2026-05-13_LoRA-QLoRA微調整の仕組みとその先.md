# LoRA / QLoRA と PEFT ファミリーの設計哲学
**日付**: 2026-05-13
**分野**: テクノロジー
**タグ**: #LoRA #QLoRA #PEFT #ファインチューニング #LLM #低ランク近似 #量子化

## 学んだこと

### なぜ「低ランク更新」で十分なのか——理論的根拠

LoRA（Low-Rank Adaptation、arXiv:2106.09685、Hu et al. 2021 / Microsoft）の鍵は一つの仮説に尽きる。**「事前学習済みモデルの重みのタスク適応に必要な変化量は、本質的に低ランクの部分空間に収まる」**。

この仮説の土台は Aghajanyan et al. 2021（arXiv:2012.13255）の「固有次元仮説（Intrinsic Dimensionality）」である。事前学習済み RoBERTa のパラメータ空間をランダム射影で圧縮し、たった **〜200 次元のサブスペース**だけを最適化しても、フルファインチューニングの 90% 以上の性能が得られることを示した。つまり大規模モデルが獲得した汎化は本質的に低次元の構造を持つ。LoRA はこれを「前向き（weight update を低ランク行列の積で表現）」に活用したものだ。

数式で表すと、事前学習済みの重み行列 W₀ ∈ ℝ^(d×k) に対して更新を凍結し、代わりに：

```
ΔW = B · A,  B ∈ ℝ^(d×r),  A ∈ ℝ^(r×k),  r ≪ min(d, k)
```

を訓練する。forward pass では `h = W₀x + (α/r)·BAx` と計算され、推論時は単に `W₀ + (α/r)·BA` に重みをマージすることで**推論オーバーヘッドがゼロ**になる（ここが Adapter Tuning との決定的な違い）。GPT-3 175B 換算で訓練可能パラメータが 10,000 倍削減、GPU メモリが 3 倍削減。

スケーリング係数 `α/r` のデフォルトは `α = r`（実質的に 1.0 倍）だが、これは重大な落とし穴を含んでいた。

### rsLoRA——スケーリング係数の数学的修正

標準 LoRA の `α/r` スケーリングは **rank が大きくなると学習が不安定化・低速化する**という問題を持つ。Kalajdzievski（2023、arXiv:2312.03732）はその原因を理論的に証明し、正しいスケーリング係数は `α/√r` であるべきと示した。これが **rsLoRA（Rank-Stabilized LoRA）**。

直感的には、LoRA の更新 `BA` の各成分は O(1/r) のノルムを持つが、これを r 個足し合わせると合計ノルムは O(1) になるはずが `α/r` スケーリングでは O(1/r) に萎んでしまう。`α/√r` にすると合計ノルムがランクによらず安定する。実用上の意味は大きい：高ランク（r=64, 128）でも学習が収束しやすくなり、「高ランク = 高品質」というトレードオフを活かせる。Hugging Face PEFT に標準実装済み。

### QLoRA——4-bit NF4 + 二重量子化 + ページドオプティマイザ

QLoRA（Dettmers et al. 2023、arXiv:2305.14314、NeurIPS 2023）は LoRA の「どこを削るか」という着眼点をさらに急進させた。**凍結した基盤モデル本体を 4-bit で保持したまま LoRA アダプタのみ bf16 で学習する**という発想だ。3 つのコア技術が組み合わさっている：

**（1）NF4（4-bit NormalFloat）データ型**：事前学習済み LLM の重みは平均 0 の正規分布に従うことが実験的に確認されており、これを情報理論的に最適な 4-bit 離散化で表現したのが NF4 だ。uniform 量子化や INT4 より正規分布への適合が高く、QLoRA 実験での品質損失を最小化する。storage は 4-bit だが forward/backward pass では都度 bf16 にデクアンタイズして演算する（「compute dtype と storage dtype を分ける」設計）。

**（2）Double Quantization（二重量子化）**：量子化定数（スケール因子 C）自体をさらに量子化する。これだけで平均 **0.37 bits/parameter** の節約が得られる。絶対値は地味だが 65B モデルではギガバイト級の節約になる。

**（3）Paged Optimizers（ページドオプティマイザ）**：長シーケンスの gradient checkpointing 時にオプティマイザ状態（AdamW の 1st/2nd moment）が GPU メモリスパイクを起こす問題を、NVIDIA Unified Memory API を用いて CPU RAM へ退避することで吸収。「持っていない分は貸し出す」というページングそのものだ。

結果として、65B パラメータモデルを **単一 48GB GPU（RTX A6000 相当）** でファインチューニング可能にした。代償は訓練時間の 39% 増（量子化/デクアンタイズのオーバーヘッド）。

### DoRA——大きさと方向を分けて学ぶ

DoRA（Weight-Decomposed Low-Rank Adaptation、Liu et al. 2024、ICML 2024 Oral、arXiv:2402.09353、NVIDIA）はより根本的な問いを立てた。「LoRA とフルファインチューニングは何が違うのか？」

Weight Normalization の観点から重み行列を **magnitude（スカラー列ベクトル m）と direction（単位列ベクトル行列 V）に分解**すると：
- フルファインチューニング：magnitude と direction を**独立して**調整し、その変化に負の相関がある（大きくなった方向のベクトルは magnitude を下げる傾向）
- LoRA：magnitude と direction の変化が**相関してしまい**、フルファインチューニングとは定性的に異なるパラメータ軌跡を辿る

DoRA の解決策は magnitude だけフルパラメータ更新し、direction の更新には LoRA を使うことで、フルファインチューニングに近い学習パターンを少ないパラメータで実現すること。LLaMA-7B/13B でのコモンセンス推論が LoRA 比 **+3.4 / +1.0 ポイント**、LLaVA での視覚指示チューニングで **+0.6 ポイント**。推論時は LoRA と同様にマージできるため推論コストゼロ。

### "Illusion of Equivalence"——LoRA の一般化の落とし穴

arXiv:2410.21228（NeurIPS 2025 採択）は「LoRA = フルファインチューニングの軽量代替」という認識に疑問を呈した。重み行列の SVD を解析すると、LoRA でファインチューニングした行列には **"intruder dimensions"（侵入次元）** と呼ばれる高ランクの特異ベクトルが発生する。フルファインチューニングにはこれがない。

実用的な意味：intruder dimensions を持つモデルは事前学習データ分布への適合が劣化し、**逐次的なマルチタスクファインチューニングでの破滅的忘却が悪化する**。解決策は高ランク + rsLoRA の組み合わせ（intruder dimensions が消える）だが、これはパラメータ数の増加を意味する。「LoRA は同じタスク分布での評価では等価に見えるが、分布外では異なる」——これはベンチマークで気づきにくい落とし穴だ。

### AdaLoRA——ランクを動的に割り当てる

標準 LoRA はすべての対象層に同じランク r を割り当てるが、層ごとに「学習すべき情報量」は異なる。AdaLoRA（Zhang et al. 2023）は SVD 形式 `W = P·Λ·Q`（P, Q は直交行列、Λ は対角）で重み更新を表現し、重要度が低い特異値を訓練中に刈り込む。結果として総パラメータ予算を固定したまま重要な層に自動的にランクを集中させる。

### GaLore——LoRA の「外」：勾配空間の低ランク射影

GaLore（Gradient Low-Rank Projection、Zhao et al. 2024、arXiv:2403.03507）は発想が根本から違う。LoRA はパラメータ空間を低ランクに制限するが、GaLore は**すべての重みをフルランクで学習しつつ、勾配空間だけを低ランクに投影してオプティマイザ状態を圧縮する**。

仕組み：各重み行列の勾配 G ∈ ℝ^(m×n) に対して SVD で rank-r の部分空間 R を求め、その部分空間内でのみ AdamW の 1st/2nd moment を保持する。数 T ステップごとに部分空間 R を更新する。オプティマイザ状態は O(mn) → O((m+n)r) に削減。

LoRA との決定的な差は「フルランク学習ができる」こと：LoRA は重みの変化を rank-r サブスペースに永続的に閉じ込めるが、GaLore は任意の方向に動けてオプティマイザの状態だけ削る。これにより **事前学習**（LoRA が苦手なフェーズ）にも適用可能。7B モデルを RTX 4090（24GB）単一 GPU でゼロから事前学習できることを初めて実証した。GaLore 2（arXiv:2504.20437、2025/04）では Randomized SVD（15x 高速化）と FSDP 統合を追加し、500B トークン・256×H100 での Llama 7B 事前学習を実証した。

### 実装上の知見——ハイパーパラメータ選択

- **ランク r**：r=4〜8 はシンプルなタスク（分類・スタイル変換）、r=16〜32 は複雑な命令チューニング、r=64+ は最高品質が必要な場合。rsLoRA 使用を前提にすると高ランクのペナルティが減る
- **対象層**：元論文では Q/V のみ対象にしたが、最近の研究（GRPO での層別勾配分析）では MLP の up_proj が最もリウォード感度が高い（21.4%）。K/V/Q と MLP を全部対象にするのが 2025 年の実践的デフォルト
- **α（スケーリング）**：rsLoRA なら α=16 固定で r を変化させるのがシンプルな戦略
- **QLoRA でのバッチサイズ**：Paged Optimizers は OOM 防止だが、長シーケンスではバッチ 1 でも逼迫する。gradient checkpointing との組み合わせが必須

## 気づき・洞察

LoRA ファミリーに通底しているのは「**計算・メモリの制約を消すのではなく、制約を扱いやすい場所に移動させる**」という設計原理だ。

- LoRA：モデル更新のランク（複雑さ）を制限する代わりに推論コストをゼロにする
- QLoRA：基盤モデルの storage を 4-bit に圧縮する代わりに前向きパスでデクアンタイズのコストを払う
- GaLore：フルランク更新を許す代わりにオプティマイザ状態のみ低ランクに圧縮する

rsLoRA の `α/√r` 修正は小さな変更に見えて「高ランク LoRA は本質的に使いにくかった」という実践的制約を取り除いた。理論の正確さが実用性を直接変える好例だ。

"Illusion of Equivalence" の知見は特に重要だ。同一ベンチマークで同点でも**モデルの「形状」が違う**——これはスペックシートで比較できない差異で、LLM の評価手法自体への疑問提起でもある。

## 他分野との接続

- **CS（線形代数・SVD）**：LoRA は行列の低ランク近似（Schmidt–Eckart–Young 定理：Frobenius ノルム最小の rank-r 近似は上位 r 個の特異値を使う行列）の直接応用。SVD はAdaLoRA・DoRA・GaLore でも核心に使われ続けている
- **CS（情報圧縮）**：QLoRA の NF4 は情報理論最適符号化の応用。Huffman 符号や算術符号と同じく、分布の形を利用して情報量を最小化する
- **解剖学・スポーツ**：「筋肉のどこを鍛えるか」という問いに似ている——全体をくまなく使うよりも「この動作に最も効くモーターパターン」だけを重点的に使うことが効率化の核心
- **音楽**：ピアノの速度練習で「指全体を動かすのではなく最小限の動きで打鍵する」という局所化の原則は LoRA の「必要な自由度だけ更新する」哲学と同型

## 次に深掘りしたいこと

- **LoRA のマージ技術**：TIES-Merging・DARE・SLERP など複数の LoRA/モデルを重みスペースで合成する手法。マルチタスク適応の実用的解になりつつある
- **継続的学習と LoRA**：intruder dimensions 問題が最も顕在化するのが逐次タスク学習。EWC（Elastic Weight Consolidation）と LoRA の組み合わせで破滅的忘却を防ぐ研究
- **RoPE・コンテキスト長と LoRA**：LLaMA の 4K → 128K コンテキスト拡張で使われた LongLoRA（sparse attention + LoRA）の仕組み

## 参考ソース

- [LoRA: Low-Rank Adaptation of Large Language Models（arXiv:2106.09685）](https://arxiv.org/abs/2106.09685)
- [QLoRA: Efficient Finetuning of Quantized LLMs（arXiv:2305.14314）](https://arxiv.org/abs/2305.14314)
- [DoRA: Weight-Decomposed Low-Rank Adaptation（arXiv:2402.09353）](https://arxiv.org/abs/2402.09353) — ICML 2024 Oral
- [A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA / rsLoRA（arXiv:2312.03732）](https://arxiv.org/abs/2312.03732)
- [LoRA vs Full Fine-tuning: An Illusion of Equivalence（arXiv:2410.21228）](https://arxiv.org/abs/2410.21228) — NeurIPS 2025
- [GaLore: Memory-Efficient LLM Training by Gradient Low-Rank Projection（arXiv:2403.03507）](https://arxiv.org/abs/2403.03507)
- [GaLore 2: Large-Scale LLM Pre-Training by Gradient Low-Rank Projection（arXiv:2504.20437）](https://arxiv.org/abs/2504.20437)
- [Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning（arXiv:2012.13255）](https://arxiv.org/abs/2012.13255)
- [Hugging Face PEFT LoRA ドキュメント](https://huggingface.co/learn/llm-course/en/chapter11/4)
- [NVlabs/DoRA GitHub](https://github.com/NVlabs/DoRA)
