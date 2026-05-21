# Zig言語のcomptimeとアロケーター設計哲学
**日付**: 2026-05-05
**分野**: tech
**タグ**: #Zig #comptime #アロケーター #システムプログラミング #メタプログラミング

## 学んだこと

Zigは2026年現在、Rustとは別の道を歩むシステム言語として注目されている。その設計哲学は「No Hidden Control Flow, No Hidden Memory Allocations, No Preprocessor」に集約される。Cの単純さを残しつつ、Cの致命的な問題（隠れたメモリ確保、未定義動作、貧弱な抽象化）を**明示性**で克服する。中核には2つの直交する仕組みがある — `comptime`（コンパイル時実行）と**明示的アロケーター**だ。

### comptimeの正体

`comptime`は「コンパイル時に実行される通常のZigコード」であり、マクロでもテンプレートでもない。同じ言語、同じ意味論で、ただ実行タイミングが違うだけ。これが革命的なのは、**ジェネリクス・型クラス・条件付きコンパイル・定数畳み込み・部分評価**を全て同一機構で表現できる点にある。

Zigにジェネリック構文は存在しない。代わりに「型を返す関数」を書く：

```zig
fn Matrix(comptime T: type, comptime rows: usize, comptime cols: usize) type {
    return struct {
        data: [rows][cols]T,
    };
}
```

`type`もファーストクラスの値であり、`comptime`コンテキストでのみ操作できる。`Matrix(f32, 3, 3)`は単に「コンパイル時に呼ばれる関数」であり、戻り値の型を新たに合成して返す。C++テンプレートのような独立した宣言的言語ではなく、同じZig言語そのものが型生成器として動く。

### アロケーターの明示性

Zigの標準ライブラリは「メモリ確保が必要な関数には必ず`Allocator`を引数として渡す」というルールを徹底する。`std.ArrayList(u8).init(allocator)`、`try std.json.parseFromSlice(T, allocator, input, .{})` — どこを見てもアロケーターが見える。これは単なる慣習ではなく、**ライブラリAPIの設計契約**だ。

具体的なアロケーター種別：

| アロケーター | 用途 | 特徴 |
|-------------|------|------|
| `GeneralPurposeAllocator` | 汎用 | 二重解放・リーク検出付き、デバッグ用途で強力 |
| `ArenaAllocator` | リクエスト単位の生存期間 | 個別freeを無視、`deinit()`で一括解放 |
| `FixedBufferAllocator` | 静的バッファ | スタック上の固定サイズ領域、OS呼び出しなし |
| `c_allocator` | malloc互換 | libc連携 |
| `page_allocator` | ページ粒度 | mmap直叩き、大きな割り当て |

特にArenaAllocatorは「サーバの1リクエストの間だけ生きるデータ」を効率化する。リクエスト終了で全て一括解放するため、個別の解放追跡が不要になり、リーク不可能・高速・カスタムOOM処理が容易、という三拍子が揃う。

### comptimeとアロケーターの交差点

興味深い境界として、「comptime内でアロケーターを使えるか」という問題がある。Zigには専用の `comptime allocator` 提案 (issue #5873) があり、`@alloc`/`@resize` 組み込み関数を通じて単一のグローバルcomptimeアロケーターから割り当てる構想だ。**確保失敗はコンパイルエラーになる** — 実行時にOOMで分岐するのではなく、ビルドが通らない、という設計が美しい。

これは「ビルドするマシンのメモリ量で挙動が変わる」というRustの`const fn`が抱えがちな問題への一つの解だ。コンパイル時に動かせる範囲を意図的に「予測可能で純粋」に保ちつつ、必要なら無制限のアロケーションを許す。

## 気づき・洞察

**「明示性の総量保存則」**がZigの設計を貫く。Cは何も明示しないので脆い。Rustはライフタイム・所有権・borrow checkerを明示することで安全性を得るが、構文と型システムが肥大化する。Zigは「メモリ確保」と「コンパイル時/実行時の境界」だけを徹底的に明示し、それ以外は単純に保つ。所有権はプログラマの責任、ライフタイムは慣習で管理する。

これは**「正しい部分の取捨選択」**としては大胆な賭けだ。Rustが「メモリ安全」を、Zigが「明示性とシンプリシティ」を選んだ。どちらが正しいかは用途次第だが、Zigの賭けが面白いのは、`comptime`という単一の道具が「ジェネリクス + マクロ + テンプレート + constexpr + 条件付きコンパイル」を全部置き換える、という発見にある。

もう一つの気づき：**アロケーターの引数化はテストを根本的に変える**。`FailingAllocator`を渡せば任意の地点でOOMをシミュレートでき、`testing.allocator`はリーク検知付き、`ArenaAllocator`を使えばテスト終了後の解放漏れを防げる。Cでは`malloc`をモックするのはハック的だったが、Zigでは設計の一部だ。これはCS分野で学んだ「依存性注入はテスタビリティを生む」という原理が、低レベル言語にも応用された例といえる。

## 他分野との接続

**cs分野の永続データ構造**との接続：Zigの`ArenaAllocator`は「世代ごとに一括解放」というコンセプトを持つが、これは関数型言語の永続データ構造（path copying）が「過去の状態を共有しつつ新版を作る」のと対照的な、双子のような戦略だ。一方は「使い捨ての世代」を効率化し、他方は「不変な世代を残す」を効率化する。どちらも「個別のfreeを排除する」点で共通する。

**piano分野のロシア楽派**との対比：Neuhausは「Artistic image（芸術的イメージ）が技法を規定する」と説いた。Zigも同じく「**意図（comptime値）がコード（実行時挙動）を規定する**」構造を持つ。技術駆動でも構文駆動でもなく、目的が形式を生む — 演奏とプログラミングが共鳴する。

**bread分野のオートリーズ**との接続：オートリーズは小麦粉と水を混ぜて休ませる「事前準備の段階」で、後の作業を効率化する。`comptime`もまさに「コンパイル時の事前計算」で実行時を効率化する。発酵の「時間と作業の交換」と、コンパイラの「ビルド時間と実行時間の交換」は同型だ。

## 次に深掘りしたいこと

- Zigの`build.zig`システムとMakefile/Bazelとの設計比較
- async/awaitが2026年版で再設計された経緯（`async`キーワード一時削除→stackless coroutine再設計の議論）
- Zig自身がC・C++コードをコンパイルできる`zig cc`の仕組みとcrosscompile戦略
- `comptime`の停止性問題と`@setEvalBranchQuota`による上限制御
- Roc・Odin・Janeなど他の「Cの代替候補」言語との設計トレードオフ比較

## 主要参考ソース

- [Zig Programming Language Documentation](https://ziglang.org/documentation/master/)
- [Pure Systems: Functional Programmers need to take a look at Zig](https://pure-systems.org/posts/2026-04-29-functional-programmers-need-to-take-a-look-at-zig.html)
- [openmymind: Leveraging Zig's Allocators](https://www.openmymind.net/Leveraging-Zigs-Allocators/)
- [GitHub Issue #5873: Comptime allocator builtins](https://github.com/ziglang/zig/issues/5873)
- [Java Code Geeks: Zig's Comptime - Running Code at Compile-Time](https://www.javacodegeeks.com/2026/02/zigs-comptime-running-code-at-compile-time-to-eliminate-runtime-overhead.html)
