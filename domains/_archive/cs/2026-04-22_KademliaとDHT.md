# KademliaとDHT(分散ハッシュテーブル)
**日付**: 2026-04-22
**分野**: cs
**タグ**: #DHT #Kademlia #P2P #XOR距離 #BitTorrent #IPFS

## 学んだこと

### DHTが解く問題
分散ハッシュテーブル(DHT)は「中央サーバなしで、数百万のノードに分散した `key → value` を高速に引ける」データ構造。問題の本質は次の3点：
1. **ノードの出入りが頻繁(churn)** でも動き続けること
2. **ルックアップの計算量を O(log N)** に抑えること
3. **どのノードも特別でないこと**(単一障害点を作らない)

伝統的な集中型(例: DNSの権威サーバ)はスケーラブルだが、ノードの自律性と耐障害性が不足。DHTは「**全ノードが対等な参加者**」という制約を維持したまま、同規模のルックアップ効率を達成する。

### DHTの歴史的系譜
- **Chord(2001, MIT)**: 円形IDリングにノードを配置、フィンガーテーブルで指数的にジャンプ。O(log N)を初めて達成した古典。
- **Pastry(2001, Microsoft Research)**: プレフィックスルーティング。
- **Tapestry(2001, Berkeley)**: Pastryと類似。
- **Kademlia(2002, NYU/Maymounkov & Mazières)**: XORメトリックという独創的な発想。後に BitTorrent DHT, eD2k, Ethereum, IPFS, Tor hidden services の基盤になった。**事実上の業界標準**。

### Kademliaの核: XOR距離
Kademliaでは各ノードに 160 bit(SHA-1由来)の NodeID を振る。2ノードの距離を次で定義：
```
distance(a, b) = a XOR b   (整数として解釈)
```
このXOR距離は数学的に「メトリック(距離空間)」の公理を満たす：
- `d(x, x) = 0`
- `d(x, y) > 0` (x ≠ y)
- `d(x, y) = d(y, x)` (対称)
- **Unidirectional**: 任意の点xと距離Dに対し、`d(x, y) = D` を満たすyは唯一(他のメトリックにはない性質)
- 三角不等式: `d(x, z) ≤ d(x, y) XOR d(y, z)`

XOR距離の美しさは**計算が1サイクルで済む**こと。Chordのような「モジュロ計算 + 方向性」が不要。また**abelian group**(可換群)を成すため、数学的分析が閉じる。

### k-buckets: ルーティングテーブル
各ノードは 160 個の「k-bucket」を持つ：
- i 番目のバケットには「自分から距離が `2^i` 以上 `2^(i+1)` 未満のノード情報」を最大 k 個(通常 k=20)保持。
- 距離の近い範囲(小さいi)は実質的にピアが少ないためバケットは疎、遠い範囲は密。
- バケットは **LRU(least recently used)ポリシー**で、新ノードは古くて通信に応答しないノードを置き換える。これがアンチスパム/anti-Sybil耐性の鍵。**古くから接続しているノードほど優先される**ため、攻撃者は長期滞在しないとテーブルに侵入できない。

### ルックアップアルゴリズム
key `K` に対する value を取得する手順：
1. 自分のk-bucketsから K に**最も近い α 個(通常 α=3)**のノードを選ぶ。
2. それらに並列で `FIND_NODE(K)` を送る。
3. 各応答は「自分が知っている中で K に最も近いノード k 個」を返す。
4. 新しく知ったノードのうち、さらに K に近いものに再度 `FIND_NODE`。
5. これ以上近いノードが見つからなくなるまで繰り返す。収束したノード集合に `FIND_VALUE(K)` を送る。

**各イテレーションで「K との最長一致プレフィックスが少なくとも1ビット伸びる」**ため、ネットワークサイズ N に対し **O(log₂ N)** ホップで到達。**α 並列化**により、遅いノード1つが全体をブロックしない。

### 4つのRPCだけで全て成り立つ
Kademliaが設計として美しいのは、プロトコルが以下の4つのメッセージで完結する点：
- `PING`: ノードが生きているか確認
- `STORE(key, value)`: 値を保存させる
- `FIND_NODE(id)`: id に近いk個のノードを返す
- `FIND_VALUE(key)`: key を持っていれば値を返す、なければ FIND_NODE と同じ応答

キー保存は「keyに最も近いk個のノード」に冗長コピー。ノード退出時は k の冗長性で救われる。1時間ごとに re-publish される(レプリカ更新)。24時間キャッシュの有効期限(expire)。

### 実世界での実装
- **BitTorrent DHT(Mainline)**: BitTorrentのトラッカーレス化。世界で数百万ノードが日常的に参加する最大のDHT。
- **IPFS/libp2p**: 分散ストレージ。 keyはCID(Content Identifier)。
- **Ethereum Node Discovery v5**: EthereumノードのピアディスカバリもKademlia派生。
- **Tor hidden services(v3)**: オニオンアドレスのディレクトリもDHT。

## 気づき・洞察

**「距離の定義を変えるだけで世界が変わる」**。Chordは「リング上の時計回り距離」、Pastryは「プレフィックス一致長」、Kademliaは「XOR」。同じ問題に対し、距離空間の選び方だけでアルゴリズムの美しさが一変する。XORの**対称性**により、「AはBから見て近いのに、BはAから見て遠い」という非対称な関係がなくなる。これがルーティングテーブルの**対称的学習**(AがBを学べば、BもAを学ぶ)を可能にし、ネットワーク全体の**自己修復性**につながる。

**「LRUが攻撃耐性になる」**。最も素朴なキャッシュポリシーであるLRUが、Sybil攻撃(偽ノードを大量生成する攻撃)への耐性の中核。なぜなら、攻撃者はk-bucketに食い込むために**古くから応答し続けるノードを置き換える必要があり、それには長時間の正常な振る舞いが必要**だから。悪意のコスト=滞在時間、という自然な価格付け。暗号でも認証でもなく、**時間を通貨にしてSybilを防ぐ**思想。これはブロックチェーンのPoW以前に、既にP2Pの世界で「コストを時間に置き換える」解が存在したことを意味する。

**「分散システムの3要素」**。DHT設計が示すのは「ノードの出入り耐性(churn)」「効率(log N)」「対称性(peer-to-peer)」の同時達成が可能ということ。これは中央集権を前提とした従来DBの設計思想の対極にある。クライアント-サーバが「役割の固定」で設計を単純化したのに対し、DHTは「役割の流動」をプロトコルに内包する。

## 他分野との接続

- **tech(WebGPU)**: WebGPUのコマンドバッファも「各コマンドは独立・順序の最小化」という非同期分散的設計。Kademliaの α 並列 FIND_NODE と思想が響く。
- **music(プロコフィエフのサイドスリップ)**: XOR距離は「隣接ビットの違いで距離が大きく跳ねる」特性を持つ。`0b10000000` と `0b01111111` は隣接値なのにXOR距離最大。プロコフィエフの和声も「見た目は似ているのに和声的距離は遠い」ことがある。**距離の見た目と実質の乖離**という点で類似。
- **anatomy(SI関節の楔構造)**: どちらも「強い単独要素を持たず、全体の構造的制約で安定する」。SI関節は専用筋なしで楔と靭帯で、KademliaはリーダーなしでXOR距離とk-bucketsで。
- **golf(プレショットルーティン)**: DHTルックアップの α 並列クエリは「複数の選択肢を並行評価してから収束する」。ゴルフのプレショットでクラブ候補2-3本を念頭に置き、風向き・ライを並行評価して収束する過程と構造的に同じ。
- **bread(事前発酵)**: re-publish周期は「腐敗する前に刷新する」仕組み。サワードウスターターを継続維持する「リフレッシュ」と、Kademliaの "keys expire in 24h, re-published every hour" は同じ思想。

## 次に深掘りしたいこと

- ChordとKademliaの定量的比較(同じ churn 条件での ルックアップ成功率/レイテンシ)
- S/Kademlia: Sybil耐性を強化した変種、IPFSで採用
- BitTorrent DHTの実際のNodeIDの分布(本当に一様か、地域的バイアスがあるか)
- libp2p/Ethereum Discovery v5 での Kademlia のカスタマイズ点
- Content-addressed storage(CID)と Kademlia の組み合わせが生む遅延特性

## 参考ソース
- [Kademlia: A Peer-to-Peer Information System Based on the XOR Metric (Maymounkov & Mazières, 2002) - Springer](https://link.springer.com/chapter/10.1007/3-540-45748-8_5) - 原論文 (Tier 1)
- [Distributed Hash Tables with Kademlia - Stanford Code the Change](https://codethechange.stanford.edu/guides/guide_kademlia.html) - 大学公開資料
- [Kademlia - Wikipedia](https://en.wikipedia.org/wiki/Kademlia)
- [Formal Specification of the Kademlia and the Kad Routing Tables in Maude - SpringerLink](https://link.springer.com/chapter/10.1007/978-3-642-37635-1_14) - 形式仕様の学術論文
- [Kademlia - a Distributed Hash Table implementation for BitTorrent](https://arpit.substack.com/p/kademlia-a-distributed-hash-table)
