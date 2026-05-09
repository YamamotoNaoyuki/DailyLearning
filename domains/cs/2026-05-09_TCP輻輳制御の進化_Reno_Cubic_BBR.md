# TCP輻輳制御の進化（Reno, CUBIC, BBR）
**日付**: 2026-05-09
**分野**: cs
**タグ**: #TCP #輻輳制御 #BBR #CUBIC #ネットワーク #BDP

## 学んだこと

TCP輻輳制御（Congestion Control）は、**「ネットワークが詰まる前に、送信側が自主的に速度を落とす」仕組み**である。1986年のインターネット輻輳崩壊事件（Stanford-LBL間のスループットが32 kbpsから40 bpsに激減）を契機に、Van Jacobsonが1988年に「TCP Congestion Avoidance and Control」論文を発表し、現在まで続くTCP輻輳制御の枠組みを確立した。

### 3つの世代：Reno → CUBIC → BBR

#### Reno（1990年代）：AIMDの古典

TCP Renoは**AIMD（Additive Increase, Multiplicative Decrease）**を採用：
- ACKを受け取るたび、輻輳ウィンドウ（cwnd）を**1セグメント加算**（線形増加）
- 重複ACK（パケットロス）を検知すると、cwndを**半分**（50%減）

Renoは「**ロスベース**」アルゴリズム：パケットロスを輻輳の唯一の信号として使う。スロースタート、輻輳回避、高速再送、高速回復の4状態モデル。

問題：高速ネットワーク（Gbps級）では、AIMDの線形増加が遅すぎる。1Gbps、RTT 100msの回線でロスから回復するのに、Renoでは数十分かかる。

#### CUBIC（2008年〜現在のLinuxデフォルト）

韓国・KAISTのSangtae HaとInjong Rheeが開発。Renoの線形増加を**3次関数（cubic function）**に置き換えた：

```
W(t) = C * (t - K)³ + W_max
```

- W_max: 前回ロス時のcwnd
- K: W_maxまでの回復時間
- C: 攻撃性パラメータ（標準0.4）

特徴：
- 前回のW_max付近では**ゆっくり**動く（プラトー領域）
- W_maxを超えると**急速に**増加（プローブ領域）
- ロス時の減少は**30%**（Renoの50%より穏やか）
- **RTT非依存**：高RTTでも公平な帯域取得

CUBICはLinux 2.6.18（2006年）からデフォルトになり、現在のインターネットの多数派トラフィック。Windows 10以降もCUBICがデフォルト。

#### BBR（2016年、Google）：ロスに依存しないモデルベース

Neal Cardwell, Yuchung Cheng らGoogle社のチームが開発した**BBR（Bottleneck Bandwidth and Round-trip propagation time）**は、根本的にパラダイムを変えた。

BBRは**ロスを輻輳信号として使わない**。代わりに：
- **BtlBw（Bottleneck Bandwidth）**：ボトルネックリンクの帯域幅を継続的に推定
- **RTprop（Round-trip Propagation time）**：物理的な最小RTTを推定（キュー待ち時間を除く）
- 送信レート = BtlBw、in-flightデータ量 = BtlBw × RTprop = **BDP（Bandwidth-Delay Product）**

BBRの目標は、**「キューに詰めずにリンクを満たす」**こと。これにより：
- バッファブロート（巨大バッファによる遅延）を回避
- 高RTT・ランダムロスのある経路（衛星、無線）で劇的に高速
- YouTube、Spotifyのストリーミングで採用後、平均スループットが14%向上、リバッファリング3%削減（Googleレポート）

### 「ランダムロス」が分けるロスベースとモデルベースの宿命

ロスベース（Reno, CUBIC）の根本問題：**パケットロスは「輻輳」と「ランダム障害」を区別できない**。長距離ファイバ、無線リンクではロス率0.1〜1%が常時発生する。CUBICはこれを輻輳と誤認し、cwndを30%減らし続ける。結果、利用可能帯域の数%しか使えなくなる。

BBRはこの問題を完全に回避する。1%のランダムロスでも送信レートを下げない。これが「100ms以上のRTTでBBRがCUBICの数倍のスループットを出す」現象の正体。

### BBRの初期問題と BBRv2

BBRv1（2016）には**公平性問題**があった：
- 同じボトルネックでBBRとCUBICが競合すると、**BBRが帯域の80-90%を取り、CUBICが10-20%に押し込まれる**
- ボトルネックがshallow buffer（浅いバッファ）だと、BBRが大量のロスを引き起こす（自分はロスを無視するから）

BBRv2（2019）はこれを改善：
- ECN（Explicit Congestion Notification）信号を反応に取り入れ
- ロス率の閾値（2%）を超えたら一時的に減速
- inflight cap（送信中データ上限）を追加

BBRv3（2023）はさらにフェアネスを改善し、現在Google内部で全面展開中。

### 現代インターネットの実態（2025-2026）

CDNプロバイダ（Cloudflare, Fastly）、ハイパースケーラー（Google, Meta）はBBRを大規模採用。Linux 4.9以降でBBRが標準カーネルに含まれ、`net.ipv4.tcp_congestion_control = bbr`で有効化できる。

しかし全インターネットの大多数はまだCUBIC。**BBRとCUBICの共存が当面続く**。学術的にもBBRをデフォルトにすべきかの議論は続いており（2025年arXiv論文「Should BBR be the default」）、フェアネス問題は完全には解決していない。

## 気づき・洞察

TCP輻輳制御の歴史は、**「観測可能なシグナルから不可視の状態を推定する」推論問題**として再解釈できる。送信側はネットワーク全体の状態を直接観測できず、「ACK」「重複ACK」「タイムアウト」という間接信号から状態を推定する。Reno/CUBICは「ロス → 輻輳」という単純なベイズ推論。BBRは「**送信レートの変化に対する応答曲線**」から帯域とRTTを別個に推定するより精巧なベイズ推論。

特に深いのは、**「BBRがロスを無視する」という思想転換**。半世紀近く「ロス = 輻輳」という暗黙の前提があったのを、Googleは「**それは1980年代の地上有線ネットワークでの事実であって、現代の無線・衛星・グローバル光網では成立しない**」と看破した。**ドメインの基本前提を疑う**ことが、革新的な進歩の源泉。

ロスベース vs モデルベースの対立は、機械学習の「経験的リスク最小化 vs 構造的リスク最小化」の対立に似ている。前者はデータから直接最適化、後者はモデルを仮定して推論する。BBRは「ネットワークは BDP に従って動く」というモデルを置くことで、ノイジーな観測（ランダムロス）に頑健になった。

「フェアネス vs 効率性」のトレードオフも興味深い。BBRはCUBICより効率的だが不公平。CUBICはRTT-fair（同じボトルネックの全フローが公平に帯域を分け合う）が、効率性に欠ける。**「全員に最適」と「全体の最適化」が両立しないのは、分散システム設計の普遍的問題**。

## 他分野との接続

- **CS（Paxos/Raft、合意アルゴリズム）**: 輻輳制御も「分散合意」の一形態。各送信側が独立に判断するが、ネットワーク全体としての安定状態を維持する。
- **CS（Lamport論理時計、HLC）**: BBRの RTprop推定は時間の精密測定を要求。ネットワーク機器のクロック誤差に脆弱。
- **golf（AimPoint）**: AimPointが「視覚を信用せず物理に従う」ように、BBRは「ロス信号を信用せずモデルに従う」。**観測可能信号が真の状態を歪めて反映する場合、モデルの方が正確**。
- **anatomy（小脳のフォワードモデル）**: BBRのネットワークモデルは、小脳の運動内部モデルと同型。**システムの応答を予測することで、フィードバック遅延を補正する**。
- **bread（クロワッサンの温度管理）**: 「観測（バターの硬さ）から状態（結晶比率）を推定」する点で、輻輳推論と同じ構造。

## 次に深掘りしたいこと

- QUIC上のBBR実装：HTTP/3におけるTCP代替
- DataCenter TCP（DCTCP）とECN：データセンタ専用の輻輳制御
- Active Queue Management（CoDel, FQ-CoDel, PIE）：ルータ側からのバッファブロート対策
- SwiftやProtective Loadなど次世代輻輳制御アルゴリズム

## 主要参考ソース

- [TCP congestion control - Wikipedia](https://en.wikipedia.org/wiki/TCP_congestion_control)
- [BBR's Sharing Behavior with CUBIC and Reno - arXiv](https://arxiv.org/html/2505.07741v1)
- [Should BBR be the default TCP Congestion Control Protocol? - arXiv](https://arxiv.org/html/2510.22461v1)
- [Exploring the BBRv2 Congestion Control Algorithm - Internet2 (PDF)](https://internet2.edu/wp-content/uploads/2022/12/techex22-AdvancedNetworking-ExploringtheBBRv2CongestionControlAlgorithm-Tierney.pdf)
- [Path Quality: Is BBR the Future of Congestion Avoidance? - ThousandEyes](https://www.thousandeyes.com/blog/path-quality-brr-future-congestion-avoidance)
