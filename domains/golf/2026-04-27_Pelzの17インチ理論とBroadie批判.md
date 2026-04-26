# Pelzの17インチ理論とBroadie批判 — パッティングの最適速度論争
**日付**: 2026-04-27
**分野**: golf
**タグ**: #パッティング #Pelz #Broadie #strokes_gained #capture_speed #17インチ #lumpy_donut

## 学んだこと

### Dave Pelz の歴史的研究
**Dave Pelz** (1939-) は元 NASA 研究エンジニア（14年勤務、その後ゴルフ研究に転身）で、1970年代後半からパッティングの**実証研究**を行い、1989年の『**Putt Like the Pros**』、2000年の『**Putting Bible**』で集成した。ゴルフ史で初めて**統計と物理計測**を体系的に putting に持ち込んだ人物。

主要発見の一つが **"17 inches past the hole" optimum capture speed rule**——「パットがミスした場合に**ホール17インチ (約43cm) 先で止まる速度**」が、最大の入射確率を生む最適速度である。

### 物理的根拠 — "Lumpy Donut"（凸凹したドーナツ）
Pelz が観察した重要な現象は、**ホール周辺の地面が、プレー後半になるほど凹凸を生む**こと。スパイクマーク・足跡・グリーン補修跡が**ホールから半径50cm程度のリング状に蓄積**する——これが "lumpy donut"。

ボールがこの凸凹ゾーンを横断するとき:
- **遅すぎる putt**: 凸凹に方向を曲げられ、ホールに入らない（**「絶対に来ない」減速の最後でフラフラする**）
- **速すぎる putt**: ホールに到達した時点でボールが**ホール上空を「飛び越す」**現象 (lip-out)、また入っても深くまで弾けて出る
- **17インチ過ぎる速度**: 凸凹を克服する**慣性**は持つが、ホールへの "**capture diameter（捕獲直径**)" を最大化する

### Capture Diameter の物理学
ホールの実直径は **108 mm (4.25 inch)** だが、ボールが入るための**有効直径** (effective capture diameter) は速度依存で大きく変わる:

- **0 m/s でボールがホール縁に到達**: 直径ほぼ全幅 (ボール直径42.67mm を引いた約65mm)
- **1.5 m/s で接近**: 有効直径が約半分に低下、lip-out 発生
- **2.0 m/s 以上**: ボールはホール上を「跳ぶ」、ほぼ入らない

これを定量化したのが **A.R. Penner (Department of Physics, McMaster University)** の論文 *"The physics of putting"* (Canadian Journal of Physics 80, 2002)。Penner の数値モデルでは:

- ボール速度 $v$ で接近した場合、ホール中心からのオフセット $d$ がある最大値以下のときのみ捕獲される
- $v < 1.31$ m/s では $d_{max} = 53.5$ mm（ボール半径ぶん除く）
- $v = 1.63$ m/s では $d_{max} = 32$ mm
- $v > 2.0$ m/s では事実上 $d_{max} = 0$（直接ヒットでも弾き出される）

**Pelz の17インチ過ぎる速度** ≒ 接近速度 1.0-1.3 m/s に対応し、これが**完全捕獲を保証する最大速度**となる。物理的に厳密な最適値が存在する。

### Pelz の検証実験
Pelz の主張の独特な点は、**実測実験**にある:

1. **トーナメントグリーンの計測**: PGA Tour のプロパットを高速カメラで測定、入った putt と入らなかった putt の最終速度を分析
2. **6,000パットのデータベース**: 複数年にわたるツアー観測
3. **Putting Track 装置**: 自身が考案した一定速度発射装置で、ホールに対して一定速度・オフセットで人工的にパットを行い、捕獲率を測定

この実測ベースのアプローチは、当時のゴルフ指導が**逸話と感覚に依存**していたのとは画期的に異なった。

### 17インチの誤解 — "目標"ではなく"平均"
Pelz 自身が繰り返し強調するのに**しばしば誤解される**点: 17インチは**目標ではなく統計的平均**。彼の本来の文言は——

> 「最適速度でパットを送ると、外れた場合は**平均して** 17 inch past で止まる」

つまり「**全てのパットが17インチ先で止まることを目指せ**」ではなく、「**最適速度で打って外れた putts のサンプル平均が17 inchになる**」。グリーンの傾斜・スピード・芝目で大きく変動する——下り傾斜では7-8インチ、上りなら24-30インチが平均値となる。

この区別を見落とすと、**意図的に17インチオーバーするように打つ→過度に攻撃的→3-putt 増**という**逆効果**を生む。Geoff Mangum は『**The Truth About Putting**』(2007) で Pelz の17インチ rule を「**bogus science and bad advice**」と痛烈に批判したが、批判の本質は Pelz の主張ではなく**読み手の誤読**にある。

### Mark Broadie の Strokes Gained Putting
**Mark Broadie** (Columbia Business School, 1960-) は、2011年に PGA Tour と協力して **ShotLink データベース** (2003年から全ショットを GPS で記録) を分析し、**Strokes Gained Putting (SG-Putt)** を発明。これは**従来の putt per round が示せなかった「実力」を厳密に測定**する指標。

定義:
$$SG_{putt} = \text{ベンチマーク打数 (距離別の Tour 平均)} - \text{実際の打数}$$

例: 8 ft からの平均 putt 数が 1.46 (Tour 平均)、あなたが 1 putt で入れた → SG = 0.46。

### Broadie の putting 戦略への含意
Broadie の『*Every Shot Counts*』(2014) Chapter 7 は putting 戦略を統計的に解析:

- **長距離 putt (20 ft 以上) でアマチュアは過度に消極的**——3-putt を恐れて「**die-it-in**」（死んでホールに到達するスピード）を狙うが、**実際には die-it-in より少し強めの方が in 確率が高い**
- 距離別 in 確率:
  - 3 ft: Tour 約 96%, アマチュア 約 84%
  - 8 ft: Tour 約 50%, アマチュア 約 30%
  - 15 ft: Tour 約 22%, アマチュア 約 13%
  - 20 ft: Tour 約 15%, アマチュア 約 8%

- **Lag putting** (長距離) では 3-putt を避けるための速度コントロールが SG を最も改善する
- **8 ft 以下** では Pelz の capture speed 理論が実用的——「**hole の back center を狙え**」

### Pelz vs Broadie の補完関係
両者は時に対立的に語られるが、**実は問題領域が異なる**:

- **Pelz**: 個別 putt の**物理学的最適化** (capture speed, line)
- **Broadie**: 統計的な**戦略最適化** (どの位置からどう攻めるか)

Broadie は Pelz の物理学を否定せず、「**Pelz の研究はサンプル数が少ない場合があり、Tour 全体への一般化に注意が必要**」と注意を促すに留まる。両者は補完的。

Tour プロでは **Tiger Woods** が「**8-12 inches past, dead center**」を信条としたとされ、**Jordan Spieth** は「**good speed, good line**」を口癖に Pelz/Broadie 折衷を実践。**Adam Scott** (long putter 時代後) は AimPoint と Pelz speed を組み合わせ、2026 年現在の Tour SG-Putt 上位はほぼ全員が**統計分析と物理理論の両方**を取り入れている。

### Dr. Paul Hurrion の研究
イギリスの sport biomechanist **Dr. Paul Hurrion** (Quintic Consultancy 創設) は、Pelz と独立に capture speed を計測:

- ホール入射時の最適速度: **1.4-1.6 m/s** がボール捕獲の物理学的最大効率
- 17インチ rule は、平均的な Tour green speed (Stimpmeter 11) で**約 1.5 m/s に対応**——Pelz と物理学的に整合
- グリーン速度が変わると最適 over-distance も変わる: Stimp 8 では 13-14 inch、Stimp 13 では 22-25 inch

### 3-foot circle と短距離 putt の重要性
Pelz の**もう一つの重要な統計**: PGA Tour の score の **約 43%** は**短距離 putt (3 ft 以内)** で決まる。すなわち:

> 「**3 フィート圏内のパットが入るかどうかが、スコアの最大の決定要因**」

これは「**3-foot circle drill**」（ホールの周り3フィートに18箇所のボールを置き、全て入れるまで終わらない練習）の根拠となった。Bruce Crampton, Tom Watson, Jordan Spieth が信奉者として知られる。

## 気づき・洞察

### "Lumpy Donut" は古典物理学の精緻な観察
Pelz の最大の貢献は、**「ホール周辺の地面が均一でない」という当たり前の事実に注目した**こと。1970年代までゴルフの putting 理論は「**ボールとホールの幾何学的関係**」のみを論じ、**地面の状態という時間変動的な変数**を無視していた。Pelz の "lumpy donut" は、ニュートン力学的な putting 観に**生態学的・時間的な変数**を持ち込んだ画期的な観察。**当たり前の事実を厳密に定式化することの威力**。

### 「平均値の罠」— Pelz 誤読の構造
Pelz の17インチが「目標」と誤読されるのは、**人間が統計値を行動指針に変換するときの典型的失敗**。「**平均すれば17インチ過ぎる速度**」は**確率分布の重心**であり、それを**一つ一つの putt の目標値**に変換してはいけない。これは多くの**Bayesian 思考の応用** (確率的最適化を決定論的目標に翻訳する誤り) と同型。Geoff Mangum の批判は **Pelz の主張の誤読**を批判しているのであって、Pelz そのものではない。**統計的助言の運用には情報識字が必要**。

### 物理学が直感を救う
Penner の物理モデルが示すのは「**速すぎても遅すぎてもダメ、固有の最適速度がある**」。これはアマチュア直感「**入れたいなら強めに打て**」を**数学的に否定**する重要な結果。Penner の捕獲半径式 $d_{max}(v)$ は、速度が増すと急激に減少する非線形性を持ち、**人間の感覚的予測を超える**。**ゴルフの実証科学化**は、こうした直感反例の発見の積み重ね。

### Strokes Gained は「真の能力」を測る装置
Broadie の SG が画期的だった理由は、従来の **putt-per-round** では「**短い距離からの putt が多いラウンド**」と「**長い距離からの putt が多いラウンド**」を区別できなかった点。SG は**距離別に Tour 平均を引く**ことで、**「あなたの putting 能力そのもの」を統計的に取り出す**。これは**異なる難度の試行を共通単位に正規化する**という、Bayesian 統計や項目反応理論 (IRT) と同じ思想。**ゴルフ統計学の革命**。

### 「失敗時の許容」を最適化する戦略
Pelz の17インチも、Chaffin の暗譜PCも、**「失敗時の復帰可能性をパラメータ化する」**点で同型。**完璧を目指すのでなく、失敗の代償を計算に入れる**——これは保険数理 (actuarial science) の思想であり、トレーディングの **stop-loss**、エンジニアリングの **fail-safe design** とも繋がる。**スポーツ・芸術・工学に共通する「リスク調整最適化」のパターン**。

### Tour プロは無意識的に物理学者である
Tiger Woods の "8-12 inches past, dead center" は Pelz の 17 inch とほぼ整合。Spieth の "good speed" は SG 思想の言語化。**プロは理論を意識せず実践しているが、研究者が後付けで言語化すると整合する**——これは**実践知と科学知の収斂**の典型例。**身体経由の知識は、後から科学が追認する**形で正統化される。

## 他分野との接続

- **piano (Chaffin の performance cues)**: 「失敗時の復帰経路を多重化」する設計思想が共通。完璧を目指さず、復帰可能性を増やす——音楽暗譜と putt 戦略の同型性
- **anatomy (基底核と手続き記憶)**: Pelz の "3-foot circle drill" は**短距離 putt を基底核回路に焼き付ける**運動学習。プレッシャー下で皮質判断が落ちても、基底核に保存された運動が拾う
- **golf (ランダム vs ブロック練習)**: Pelz の drill は伝統的な block practice、Broadie の **random-distance putting** は random practice——両者の使い分けがコンテクスト干渉効果の最適化
- **cs (NP 完全性)**: putting の最適化は組合せ的に困難だが、capture speed という**近似最適**が存在する点が、NP 困難問題の**多項式時間近似アルゴリズム**と同型
- **bread (Detmolder Verfahren の段階管理)**: 異なるパラメータ (温度・湿度・時間) が交差する最適化として、Pelz の (speed, line, lumpy donut) と同じ多変数最適化問題
- **other (考古学的年代測定)**: 複数の独立的測定法 (放射性炭素・年輪・地層) を組み合わせて精度を上げるのと、Pelz (物理) + Broadie (統計) + AimPoint (傾斜) の**多源情報統合**が同型

## 次に深掘りしたいこと
- **A.R. Penner** の論文 "*The physics of putting*" (Canadian J. Physics 80, 2002) を直接読む
- **Dave Pelz** *Putting Bible* の章別アーカイブ (特に 4-7章の green reading 理論)
- **Mark Broadie** *Every Shot Counts* Chapter 7 の Lag putting 統計詳細
- **Dr. Paul Hurrion** の Quintic 解析動画 (capture speed visualization)
- **Geoff Mangum** *The Truth About Putting* の Pelz 批判の論理構造
- **AimPoint Express** (Mark Sweeney) と Pelz/Broadie の融合戦略
- **Phil Mickelson** の lag putting メソッド——「**3-putt をしない**」哲学の実装
- **GPro** (Tour 用のグリーンリーディングソフトウェア) が putting データから戦略を計算する仕組み

## 参考ソース
- Penner, A. R. (2002), "The physics of putting", *Canadian Journal of Physics* 80(2): https://cdnsciencepub.com/doi/10.1139/p01-137
- Pelz, D. *Dave Pelz's Putting Bible: The Complete Guide to Mastering the Green* (Doubleday, 2000)
- Pelz, D. *Putt Like the Pros* (Harper, 1989)
- Broadie, M. *Every Shot Counts: Using the Revolutionary Strokes Gained Approach to Improve Your Golf Performance and Strategy* (Gotham, 2014)
- Broadie, M. (2008), "Assessing Golfer Performance on the PGA TOUR", *Interfaces*: https://www.columbia.edu/~mnb2/broadie/Assets/strokes_gained_pga_broadie_20110408.pdf
- Hurrion, P. "Golf Ball Speed at Hole Entry": https://www.paulhurrion.com/tuition/an-investigation-into-golf-ball-speed-at-hole-entry/
- Mangum, G. *The Truth About Putting* (2007)
- Holmes, B. W. (1991), "Putting: How a Golf Ball and Hole Interact", *American Journal of Physics* 59(2)
- The Sand Trap Forum (2010-), "Putting Capture Speed" 議論集成: https://thesandtrap.com/forums/topic/46450-putting-capture-speed/
- The Recreational Golfer (2013), "Putt 17 inches past the hole – fact or fiction?": https://therecreationalgolfer.com/blog/2013/08/putt-17-inches-past-the-hole-fact-or-fiction/
