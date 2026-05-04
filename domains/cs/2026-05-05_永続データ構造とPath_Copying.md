# 永続データ構造とPath Copying
**日付**: 2026-05-05
**分野**: cs
**タグ**: #永続データ構造 #path_copying #fat_node #HAMT #Okasaki #構造共有

## 学んだこと

**永続データ構造（persistent data structure）**とは、変更操作を行っても**過去の版を保持し続ける**データ構造である。値を書き換えるのではなく、新しい版を返す。Driscoll, Sarnak, Sleator, Tarjanの1986年論文《Making Data Structures Persistent》で体系化された概念で、現代のClojureのコレクション、Haskellの全データ型、Reactの不変ステート管理、Gitのコミットツリーなど広範な実装の基礎となっている。

### 永続性の階層

| 種類 | 旧版アクセス | 旧版変更 | 例 |
|------|-------------|----------|------|
| **Ephemeral（揮発的）** | × | × | 通常のC配列、JS Array.push |
| **Partially Persistent（部分永続）** | ○ | × | バージョン履歴 |
| **Fully Persistent（完全永続）** | ○ | ○ | Clojureコレクション |
| **Confluently Persistent（合流永続）** | ○ | ○+merge | Git |

「完全永続」は、過去のどの版に対しても変更操作が可能で、版同士が分岐できる。「合流永続」はさらに進んで、複数の版を**合流（merge）**できる——Gitの`git merge`はまさにこれだ。

### 素朴実装：完全コピー

最も単純な永続化は、変更のたびにデータ構造全体をコピーすることだ。これは**O(n)時間・O(n)空間**を要し、明らかに非効率。だが、関数型言語の意味論的なモデルとしては正しい。

### Fat Node Method（肥大ノード法）

各ノードを**「複数の版の値を保持できる肥大ノード」**に変える。各値にバージョン番号を付与し、検索時はそのバージョン以前で最新のものを取り出す。

- 時間複雑度：O(log m)（mは変更回数）— 二分探索で版を特定
- 空間複雑度：変更ごとに+O(1)（既存ノードに値を追加するのみ）

問題点：版を辿る方向性。「あるノードがどの版で誰の親だったか」を追跡する逆ポインタが必要で、実装が極めて複雑になる。

### Path Copying（経路コピー法）

最も広く使われる手法。**変更されたノードからルートまでの経路上のノードのみをコピー**し、それ以外は古い版と共有する。

二分木に新しい葉を追加する場合：
```
古い版:        新しい版:
    A              A'
   / \            / \
  B   C          B'  C        ← Cは共有
 / \            / \
D   E          D   E'         ← E'は新ノード
```

経路上のA→B→Eの3ノードだけが新しく作られ、CとDは旧版と共有される。**O(log n)時間・O(log n)空間**（バランス木の場合）。

### Driscoll-Sarnak-Sleator-Tarjan ハイブリッド法

論文の真の貢献は、Fat NodeとPath Copyingを組み合わせた**Node Copying**手法だ。各ノードに**少数の追加スロット**（典型的にはp個、pは入次数）を持たせ、それが埋まったときだけ新ノードを作る。

これにより**O(1)償却時間・O(1)償却空間**を達成。Fat Nodeの空間効率と、Path Copyingの時間効率の良いとこ取りだ。論文の白眉である。

### Okasaki赤黒木 — Functional Pearl

Chris Okasakiの1999年論文《Red-Black Trees in a Functional Setting》は、永続赤黒木の挿入を**約30行のHaskell**で書き切った傑作である。手続き型でぐちゃぐちゃに見えた赤黒木が、関数型の代数的データ型とパターンマッチングで驚くほど美しく書ける：

```haskell
data Color = R | B
data Tree a = E | T Color (Tree a) a (Tree a)

insert :: Ord a => a -> Tree a -> Tree a
insert x s = makeBlack (ins s)
  where ins E = T R E x E
        ins (T color a y b)
          | x < y = balance color (ins a) y b
          | x > y = balance color a y (ins b)
          | otherwise = T color a y b
        makeBlack (T _ a y b) = T B a y b

balance B (T R (T R a x b) y c) z d = T R (T B a x b) y (T B c z d)
balance B (T R a x (T R b y c)) z d = T R (T B a x b) y (T B c z d)
balance B a x (T R (T R b y c) z d) = T R (T B a x b) y (T B c z d)
balance B a x (T R b y (T R c z d)) = T R (T B a x b) y (T B c z d)
balance color a x b = T color a x b
```

`balance`関数が4つの「平衡が崩れたパターン」を統一的に扱い、結果は赤黒木の不変条件を回復する。**path copyingが暗黙に行われる**——再帰呼び出しが新しいノードを構築し、変更されない部分木は元のポインタが共有されるため、自動的に永続性が保たれる。

これは関数型プログラミングの「**immutabilityが永続性を無料で生む**」という根源的な美しさを示している。手続き型で永続化するには明示的な努力が必要だが、関数型では何もしなくても永続的だ。

### HAMT（Hash Array Mapped Trie）

ClojureのHashMapが採用するデータ構造。Phil Bagwellの2001年論文《Ideal Hash Trees》で提案され、Rich Hickeyが永続化したもの。

仕組み：
1. キーをハッシュ化して32bit整数を得る
2. ハッシュを**5bit ずつのセグメント**に分割（2^5=32）
3. 各セグメントを**32要素のスパース配列**のインデックスとして使用
4. 木の深さは32/5 ≈ 7程度（最大）→ **実質的にO(1)**アクセス

スパース配列の実装には**ビットマップ**を使う：32要素のうち実際に存在する要素のビットだけを立て、対応する値を密に詰めて保存する。これにより典型的な空ノードのオーバーヘッドを削減する。

更新時はpath copyingが自動的に働く：変更されたノードからルートまでの最大7ノードだけが新しくコピーされる。**残りの32^6≈10億ノードは旧版と共有**される。これがClojureの「不変だが効率的」という奇跡を生んでいる。

### 構造共有（Structural Sharing）の実用的影響

JavaScriptのImmutable.js、ImmerHookのstate管理、Reduxのselector最適化、Redux Toolkitなど、**JS/TS界隈の不変ライブラリは全てpath copyingを採用**している。

なぜ重要か：Reactの再レンダリング判定は`prev !== next`の参照等価性で行う（`React.memo`、`useMemo`の依存配列）。**永続データ構造は変更箇所以外のサブツリーが同じ参照を保つ**ため、変更されていないコンポーネントの再レンダリングを自動的にスキップできる。

ImmerはProxyで**疑似的な変更可能インターフェイス**を提供しつつ、内部でpath copyingを行う。プログラマは`draft.users[0].name = "Alice"`のように書け、内部的には新しいUserオブジェクト＋新しいUsers配列＋新しいRootオブジェクトが作られる。

## 気づき・洞察

**「不変性は時間旅行を可能にする」**——これが永続データ構造の本質だ。Reduxの「タイムトラベルデバッガ」、Gitの`git checkout HEAD~5`、Reactの「レンダー履歴」——すべて永続データ構造があるから可能になる。**過去が消えない**ことで、現在の状態は過去のすべての状態の**累積関数**として定義できる。

これはHaskell/Erlang/Clojureなど関数型言語が「並行プログラミングに強い」理由でもある。複数のスレッドが同じデータを読むとき、**そのデータが変更不可能であれば、ロックは不要**だ。Goのチャネル、JavaScriptのstructured cloneなどの「メッセージパッシング型並行性」も、永続性が支える設計だ。

もう一つの気づき：**「O(log n)はO(1)の実用的な近似」**。HAMTの「最大深さ7」は、log32(40億)≈7という事実から来る。コンピューターの実用的なメモリ容量を考えると、log_32 nは事実上定数だ。これはB-treeのfanoutを大きく取る理由（DBインデックスでの実用化）と同じ思想。**理論的なlog vs 定数の境界は、実装の定数倍を考慮するとぼやける**。

そして「**immutabilityのコストは思ったより小さい**」。素朴に考えると、不変オブジェクトは「毎回コピーするから遅い」と思われがちだ。だがpath copyingで実際にコピーされるのはO(log n)個のノードだけ——多くの場合、CPU L1キャッシュに収まる程度の量である。**メモリ帯域幅が支配する現代では、参照の共有がキャッシュ効率を上げる効果**もある。

## 他分野との接続

**tech分野のZigアロケーター**との深い対比：Zigの`ArenaAllocator`は「**世代単位で一括解放**」——すなわち「過去の版は破棄する」設計。永続データ構造は逆に「過去を残す」。両者とも個別freeを排除する点で共通だが、**過去をどう扱うか**で正反対の道を選んだ。**システム言語と関数型言語の哲学的差異の一断面**だ。

**music分野のベルク《ヴォツェック》**との接続：第3幕D短調間奏曲は「**無調の現在の中に、調性的な過去が永続的に保存されている**」ことを露わにする。新しい言語が古い言語を破壊するのではなく、過去の版が共有されている——音楽の永続データ構造である。

**anatomy分野の海馬リプレイ**との接続：海馬のSharp-wave ripples中の「過去の発火列の再生」は、**永続的に保存された経験の再アクセス**だ。神経系も「過去を消さずに保存する」戦略を取っている。記憶とは生物学的な永続データ構造である。

**bread分野**との対比：パンの香りは「500の化合物が重層的に共存する」が、**過去には戻れない**（焦がしたら取り消せない）。化学反応は本質的に揮発的だ。一方、関数型データ構造は「**書き込みも参照透明**」——副作用がない。生命と数学の本質的な差異がここに見える。

## 次に深掘りしたいこと

- 永続スプレー木・永続フィボナッチヒープなど、複雑なバランス木の永続化技法
- Differential Dataflow（Frank McSherry）における時間付き永続データ構造
- Git内部のオブジェクトストアと永続Merkle木の最適化
- 永続型Bツリーを使ったLMDB・LightningDBのストレージ設計
- 量子計算における「永続性」の対応概念（unitarityと可逆性）

## 主要参考ソース

- [Wikipedia: Persistent data structure](https://en.wikipedia.org/wiki/Persistent_data_structure)
- [Driscoll, Sarnak, Sleator, Tarjan: Making Data Structures Persistent (PDF)](http://www.cs.cmu.edu/~sleator/papers/another-persistence.pdf)
- [MIT 6.854 Lecture Notes: Persistent Data Structures](https://courses.csail.mit.edu/6.854/16/Notes/n2-persistent.html)
- [Chris Okasaki: Red-Black Trees in a Functional Setting (PDF)](https://www.cs.tufts.edu/~nr/cs257/archive/chris-okasaki/redblack99.pdf)
- [Worace Williams: Hash Array Mapped Tries](https://worace.works/2016/05/24/hash-array-mapped-tries/)
- [Clojure Reference: Data Structures](https://clojure.org/reference/data_structures)
- [Andrey Listopadov: Clojure on Fennel - Persistent Data Structures](https://andreyor.st/posts/2026-04-07-clojure-on-fennel-part-one-persistent-data-structures/)
