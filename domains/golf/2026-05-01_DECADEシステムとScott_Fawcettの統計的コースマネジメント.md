# DECADE システムと Scott Fawcett の統計的コースマネジメント
**日付**: 2026-05-01
**分野**: golf
**タグ**: #DECADE #ScottFawcett #コースマネジメント #ストロークスゲインド #分散

## 学んだこと

### Scott Fawcett と DECADE の起源
Scott Fawcett は 1990 年代にテキサス A&M でカレッジゴルフをし、1999 年 US Open に出場、Web.com（現コーン・フェリー）と Hooters Tour でプロ生活を送った後、3 つの量的学位（数学・経済・統計関連）を活かしてゴルフ統計のコースマネジメントへ移行した珍しい経歴の持ち主。MIT Sloan Sports Analytics Conference でも発表している。

DECADE は **D**istance, **E**xpectation, **C**orrect target, **A**nalyze, **D**iscipline, **E**xecute の頭文字。彼は 2014 年頃から PGA Tour ShotLink データ（後の Strokes Gained 基盤）と自身のショットパターン研究を統合した有料カリキュラムを提供し、Will Zalatoris、Sam Burns、Scottie Scheffler コーチ陣など多数のツアープロが採用している。

### 核心概念 1：ショットパターン（Shot Pattern / Dispersion）
**ある程度の経験を持つゴルファーは、左右の散布幅が距離の約 5–8% で固定**される。これは Fawcett が ShotLink と自身のレッスンデータから導いた最重要発見。

- **PGA Tour プロ**: ドライバーで約 70 yards 幅（最も左から最も右まで）。ファウラー級でも 60 yards、平均でも 70 yards。
- **ハンディキャップ 10 のアマチュア（200 yard ドライバー）**: 同じ 70 yards 幅。**プロより角度（degrees）は大きいが、距離が短いので絶対値の幅は同程度**。
- **ハンディキャップ 0 (スクラッチ)**: 約 60 yards。

### 核心概念 2：標準偏差で考える
ショットパターンは正規分布で近似でき、**全体幅の約 1/4 = 1σ** と扱える。ピンを狙ったときに片側に半分（35 yards）外れる確率は約 16%（1σ）、片側に 70 yards 外れる確率は約 2.5%（2σ）。**ピンに直接狙うと、平均的に 35 yards 外れる**。

これが「**ピンを狙うな、グリーンの中央＋αを狙え**」の数学的根拠。バンカーや OB の境界から **1σ 離れたところを狙えば、進入リスクは 16%**。これを 2σ 離せば 2.5% に下がる。

### 核心概念 3：The 70/30 Ratio (フェアサイドルール)
グリーン中央を狙うのではなく、**70% のショットがピンの太い側（fat side）に着地するように狙え**、というのが DECADE の象徴的ルール。例：ピンが左奥でバンカーが左手前にある時、ピンより右目（右奥またはグリーン中央右）を狙うと、散布の 70% は右側（つまり安全側）に分布する。

これは「**期待値ではなく分布の歪みを最適化する**」発想。Pelz 17 インチ理論（4/27）が「期待値計算で攻めろ」と言ったのに対し、DECADE は「**分散と非対称ペナルティを考慮して保守的に攻めろ**」と言う。両者は矛盾しない：パッティング（軽いペナルティ）では Pelz が正しく、アプローチ（バンカー・OB の重いペナルティ）では DECADE が正しい。

### 核心概念 4：Strokes Gained で意思決定
Mark Broadie の Strokes Gained (4/18 で学習) は「あるショットが平均からどれだけ得点を稼いだか」を距離別の期待打数 (Expected Strokes) から計算する。Fawcett はこの **Expected Strokes Curve** を全ホールでメンタルに参照させる。

例：パー 5 で 250 yard 残り。
- 直接グリーンを狙う：成功すれば EX = 2.8（イーグル圏）、失敗（バンカー）すれば EX = 3.2。期待値 ≈ 0.5 × 2.8 + 0.5 × 3.2 = 3.0 打。
- 100 yard を残してレイアップ：EX(100yd フェアウェイ) ≈ 2.85 打。
- → **レイアップの方が期待打数が低い**。多くのアマチュアは「2 オン狙い」が誤りと知らない。

### 核心概念 5：The Discipline Problem
DECADE は分析より**規律 (Discipline)** を最重視する。「正しい目標を選ぶ」ことの 8 割は理論ですぐ理解できるが、「**毎ショット規律を保つ**」のは至難。Fawcett の経験則では、上級アマチュアの 6 割以上が、ホールごとに「自分の今日の調子」「過去の経験」「直感」で目標を変え、結果としてショットパターンと地形のミスマッチでスコアを落とす。

DECADE が要求する規律：
1. ティーショットでは**フェアウェイの最も広い部分のセンター**を打点ではなく**着弾点**として狙う
2. アプローチでは**距離の 5% を 1σ として、ピンから 1–2σ 離れた目標**を選ぶ
3. **不調の日は目標を保守側にもう 1σ ずらす**（散布幅は大きくなる前提）
4. **「ヒーローショットを打たない」**——傾斜・木越え・230 yards 越えのキャリーを要する状況では、躊躇せずにレイアップ

### 核心概念 6：パットのドロー&フェード（パッティング戦略）
DECADE はパッティングでも **「カップの太い側（high side / pro side）を通せ**」を強調する。傾斜のあるグリーンで low side（amatuer side）に外すと、戻しのパットも傾斜下りで難しい。プロ側に外すと、戻しは上り傾斜で易しい。これも「分布の歪みの最適化」の応用。

### Brandel Chamblee の批判と反論
Golf Channel のアナリスト Chamblee は「**Tiger も Jack も DECADE のような『安全プレー』をしなかった**」と批判する。Fawcett の反論：「彼らは ShotLink 以前に **直感的に DECADE を実践していた**。Tiger が 2000 Pebble US Open で記録的勝利したとき、彼は 12 の Par4 でグリーン中央しか狙わなかった」。MIT Sloan の発表で Fawcett は実際の Tiger のショット軌跡を ShotLink で解析し、「Tiger の戦略は DECADE と 95% 一致」と示した。

## 気づき・洞察

**DECADE の本質は「期待値最適化ではなく、分散認識下の意思決定」**。経済学の **Kelly Criterion** に近い：勝率と配当が分かっていても、過剰投入は破産する。ゴルフでは「ピンを直接狙う」のは過剰投入。**16% の確率で 35 yards 外れる**ことを引き受ける覚悟があるか、という問題。

**70/30 ルールは「リスク非対称性」の応用**。グリーン中央 = 期待値最大の地点ではなく、**ペナルティが急に増える境界から最も遠い点**が最適目標。これは金融の Conditional Value at Risk (CVaR) と同型。期待値より tail risk を見る。

**Pelz の 17 インチ理論との和解**: 4/27 で学んだ Pelz は「短いパットを攻めろ」と言い、Broadie は「データはそれに反対」と言った。DECADE はこの両者を統合する：**ペナルティが軽い領域（パッティング）では攻め、重い領域（バンカー越え）では守る**。これは「risk management is context-dependent」という当たり前のことを、ゴルフの言語で精緻化した。

**規律問題は心理学のメタ認知問題**: アマチュアが DECADE を知っていても実行できないのは、「**自分の散布幅を客観視できない**」から。今日 1 球目が良く飛んだから、自分はプロのような散布幅だと錯覚する。これは小脳の運動学習（4/24 で学習）の前向性アップデートが「直近の成功」に過剰に依存する性質と整合する。**良いコースマネジメントは、自分のロングタームの分布を信じる訓練**。

## 他分野との接続

- **golf (4/29 Choking)**: プレッシャー下で目標を狭めるのは Choking と同じ機構。DECADE が「**広い目標を信じる**」と教えるのは、Choking 防止の認知デザインでもある。
- **CS (Bloom Filter, 4/28)**: 「false positive を許して計算量を圧縮する」発想と、「16% の外れを許して期待値を最適化する」DECADE は構造的に同じ。**確実性を諦めることで効率を得る**。
- **anatomy (小脳, 4/24; 基底核, 4/25)**: ゴルフスイングは基底核に依存する手続き記憶。DECADE は意思決定（前頭葉）と実行（基底核）を分離させる：「**目標を決めたら考えるな**」。
- **piano (メンタルプラクティス 4/30)**: メンタルプラクティスでスイングを「視覚化」するのは DECADE の "Expectation" フェーズと同型。
- **music（リーマンのアゴーギク）**: 「期待値からの逸脱を表現にする」音楽家と、「期待値からの逸脱を回避する」ゴルファーは表裏の関係。
- **tech (MLS の確率的セキュリティ)**: 「攻撃者が成功する確率を log N に閉じ込める」のは「ピンに直接乗る確率を諦めて期待値を最大化する」と同じ tail risk 思考。

## 次に深掘りしたいこと
- DECADE の Strokes Gained Approach 計算式の細部
- アマチュア向けのショットパターン測定法（Arccos, Garmin）
- DECADE と Lou Stagner（PGA Tour Insider）の戦略比較
- ベイズ更新で「今日の調子」を散布幅に反映するアプローチ
- DECADE Fundamentals コースの教材構造

## 主要参考ソース
- [Decade Golf - 公式](https://decade.golf/about/) - Scott Fawcett の DECADE システム公式
- [Course-management expert Scott Fawcett knows how we can all play smarter golf - Golf Digest](https://www.golfdigest.com/story/course-management-expert-scott-fawcett-tips-smarter-golf)
- [Cracking the Course Management Code with DECADE - MyGolfSpy](https://mygolfspy.com/news-opinion/cracking-the-course-management-code-with-decade/)
- [MIT Sloan Sports Analytics Conference - Scott Fawcett](https://www.sloansportsconference.com/people/scott-fawcett) - 学術的発表
- [This data-first approach to course strategy is changing how pros play - GOLF.com](https://golf.com/news/decade-stats-course-strategy-changing-how-pros-play/)
