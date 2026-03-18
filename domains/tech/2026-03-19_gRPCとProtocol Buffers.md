# gRPCとProtocol Buffers——IDLから始まるサービス間通信の設計哲学
**日付**: 2026-03-19
**分野**: テクノロジー
**タグ**: #gRPC #ProtocolBuffers #HTTP2 #マイクロサービス #API設計 #サービスメッシュ #Connect

## 学んだこと

### Protocol Buffers——バイナリシリアライゼーションとIDLの統一

Protocol Buffers（Protobuf）はGoogleが2008年にオープンソース化したIDL（Interface Definition Language）兼バイナリシリアライゼーションフォーマットである。その設計の核心は、「スキーマを先に定義し、そこからコードを生成する」というスキーマファースト思想にある。JSONやXMLが「データを先に作り、後からスキーマを当てる」のと真逆のアプローチだ。

バイナリワイヤフォーマットはフィールド番号とワイヤタイプのペアでエンコードされる。フィールド名はワイヤ上に一切現れない。これがJSONと比較して最大10倍のメッセージサイズ削減を実現する理由だ。フィールド番号がIDとして機能するため、フィールド名の変更はワイヤ互換性を壊さない。この設計判断が、スキーマ進化（schema evolution）の柔軟性の根幹となっている。

スキーマ進化のルールは厳格かつ実用的だ。フィールド番号は絶対に再利用しない（`reserved`で明示的に封印する）。新しいフィールドの追加は常に安全——古いバイナリは未知フィールドを保持して透過的に転送する。`required`フィールドは有害とされ、proto3で完全に廃止された。なぜなら、一度`required`と宣言すると、そのフィールドを削除する安全な方法が存在しなくなるからだ。

#### proto2からproto3へ、そしてEditionsへ

proto2とproto3の最大の違いはフィールドプレゼンス（存在性）のセマンティクスにある。proto2はすべてのフィールドが明示的プレゼンスを持つ——フィールドが設定されたかどうかを区別できる。proto3はデフォルトで暗黙的プレゼンスに変更した。つまり、フィールドがデフォルト値（整数の0、文字列の空文字）に設定されている場合と、まったく設定されていない場合を区別できない。後にproto3に`optional`キーワードが追加され、明示的プレゼンスを選択可能になったが、これは設計上の揺り戻しとも言える。

もうひとつの重要な違いは、proto3がrepeatedフィールドのpackedエンコーディングをデフォルト有効にしたことだ。これにより、整数の配列などが大幅にコンパクトになる。

2024年から導入が始まった**Protobuf Editions**は、proto2/proto3という二項対立を解消する試みだ。`syntax = "proto3"`の代わりに`edition = "2024"`と記述し、フィールドプレゼンスやpackedエンコーディングといった個々の振る舞いを「フィーチャー」として細粒度で制御する。初版のEdition 2023はproto2とproto3の振る舞いを完全に再現でき、ワイヤフォーマットは一切変わらない。年次リリースが計画されており、Edition 2024は2025年Q3にリリース予定とされている。

### gRPC——HTTP/2の上に構築されたRPCフレームワーク

gRPCの設計を理解するには、まずHTTP/2の特性を理解する必要がある。HTTP/1.1では1つのTCPコネクション上で1つのリクエスト・レスポンスしか同時に処理できない（パイプラインは実質機能しなかった）。HTTP/2はフレームとストリームの概念を導入し、単一TCPコネクション上で複数のリクエスト・レスポンスを多重化（multiplexing）する。

gRPCはこのHTTP/2のプリミティブの上に3層の階層構造を構築する。

**チャネル（Channel）** は論理的な接続を表す。1つのチャネルは複数のHTTP/2コネクションを束ね、名前解決（Resolver）とロードバランシングを統合する。DNSリゾルバがホスト名を13個のIPアドレスに解決すれば、RoundRobinバランサがそれぞれにコネクションを作成する。

**RPC** は個々のHTTP/2ストリームに対応する。1つのコネクション上で数百のRPCが同時に走れる。これがgRPCの高い並行性の源泉だ。

**メッセージ** はHTTP/2データフレームの上にマッピングされる。デフォルトのフレームサイズは16KBで、それより大きなメッセージは複数フレームにまたがり、小さなメッセージは1フレームに複数収まる。

#### 4つのサービスメソッドパターン

gRPCは4種類のRPCパターンを定義する。

**Unary RPC** は最もシンプルな1リクエスト・1レスポンスのパターンだ。通常のHTTPリクエストと同等だが、型安全性とProtobufの効率性が加わる。

**Server Streaming RPC** はクライアントが1リクエストを送り、サーバーがメッセージのストリームを返す。リアルタイムのフィード購読やログストリーミングに適する。メッセージの順序はgRPCが保証する。

**Client Streaming RPC** はクライアントがメッセージのストリームを送り、サーバーが1レスポンスを返す。ファイルアップロードやセンサーデータの一括送信に使われる。サーバーは「典型的にはすべてのメッセージを受信した後に」レスポンスするが、途中で返すことも許容される。

**Bidirectional Streaming RPC** は双方が独立にメッセージを送受信する。2つのストリームは完全に独立しており、ピンポン的なやりとりも、双方が好きなタイミングで書き込む自由形式も可能だ。チャットアプリケーションやリアルタイムコラボレーションの基盤となる。

#### デッドライン伝播とメタデータ

gRPCのデッドライン伝播は分散システムにおけるタイムアウト管理の優れた解法だ。クライアントが「この呼び出しは200ms以内に完了すべき」と宣言すると、そのデッドラインはサービスチェーン全体を伝播する。ただし、デッドラインは「絶対時刻」として表現されるため、サーバー間のクロック同期問題が生じる。gRPCはこれをタイムアウト（残り時間）に変換し、すでに経過した時間を差し引いて伝播することで解決する。

メタデータはHTTPヘッダーに相当するキーバリューペアで、認証トークンやトレーシング情報を運ぶ。キーは大文字小文字を区別せず、`grpc-`プレフィックスは予約されている。バイナリ値を含むキーには`-bin`サフィックスが必要で、base64エンコードされる。

#### インターセプタ

インターセプタはgRPCのミドルウェアパターンだ。クライアント側とサーバー側の両方に設定でき、すべてのRPCの前後に処理を挿入する。認証検証、ロギング、メトリクス収集、トレーシング（OpenTelemetryとの統合）などの横断的関心事を、ビジネスロジックから分離する。チェーン可能で、実行順序は登録順に従う。

#### コネクション管理とKeep-Alive

gRPCはHTTP/2のPINGフレームをKeep-Aliveメカニズムとして活用する。PINGはフロー制御をバイパスするため、データストリームに影響を与えずに接続の生存確認ができる。PINGへの応答がなければコネクションを破棄して再接続する。これはクラウド環境で特に重要だ——GCPのロードバランサは10分、AWS ELBは60秒でアイドルコネクションを切断するため、適切なKeep-Alive設定なしではコネクションが無言で切れる。

### 設計トレードオフ——gRPC vs REST vs GraphQL

この3つのAPI技術は競合ではなく、それぞれ異なる問題空間に最適化されている。

**gRPCが輝く場面**: マイクロサービス間の内部通信。型安全性、高性能（バイナリ+HTTP/2多重化）、双方向ストリーミング、コード生成による開発効率が求められるとき。レイテンシが数ミリ秒でも問題になるサービスチェーンの内部に最適。

**RESTが適する場面**: 外部公開API。ブラウザからの直接アクセス、キャッシュ活用（CDN、HTTPキャッシュ）、広範なツールエコシステム、学習コストの低さが重要なとき。Web API全体のデファクトスタンダードであり続けている。

**GraphQLが活きる場面**: フロントエンド駆動の開発。モバイルアプリのように帯域幅が制限され、クライアントごとに必要なデータが異なり、オーバーフェッチ/アンダーフェッチを避けたいとき。「クライアントが必要なデータだけを正確に指定する」という哲学。

実務では組み合わせが一般的だ。外部向けにREST/GraphQLのBFF（Backend for Frontend）を置き、内部のマイクロサービス間はgRPCで通信する。Google Cloud自身がこのパターンを推奨している。

### gRPCとマイクロサービス——サービスメッシュとロードバランシング

#### L4 vs L7ロードバランシング問題

gRPCのロードバランシングは、HTTP/1.1とは根本的に異なる課題を抱える。HTTP/1.1ではリクエストごとにコネクションを張る（または短時間で再利用する）ため、L4（トランスポート層）のロードバランサでコネクション単位に分散すれば十分だった。しかしgRPCはHTTP/2の長寿命コネクション上に多数のRPCを多重化する。L4ロードバランサはTCPコネクション単位でしか分散できないため、あるクライアントが毎分1リクエスト、別のクライアントが毎秒50リクエストを送る場合、バックエンドの負荷は3000倍の偏りが生じる。

L7（アプリケーション層）ロードバランシングはHTTP/2プロトコルをパースし、個々のストリーム（=RPC）単位で分散する。これによりコネクションを超えた均等分散が可能になるが、プロトコルの解析コストが加わる。

#### サービスメッシュの解法

EnvoyプロキシとIstioサービスメッシュは、このL7ロードバランシング問題を透過的に解決する。Envoyはサイドカープロキシとしてすべてのトラフィックを仲介し、HTTP/2とgRPCをファーストクラスでサポートする。デフォルトではleast-requestモデル（プールからランダムに2ホストを選び、アクティブリクエストが少ない方にルーティング）を採用する。

IstioはEnvoyの上にポリシーレイヤを構築し、ポートとHostヘッダーに基づく個別リクエスト単位のルーティングを実現する。長寿命コネクションでもリクエストレベルの負荷分散が効く。さらに自動リトライ、サーキットブレーカー、レートリミッティング、リクエストシャドウイング、ゾーンローカルロードバランシングといった高度な機能が標準で利用できる。

もうひとつの選択肢として**クライアントサイドロードバランシング**がある。gRPC自体がネイティブにサポートしており、リゾルバ+バランサの組み合わせでプロキシなしの直接通信を実現する。レイテンシの面では有利だが、すべての言語実装でバランシングロジックを維持する必要がある。

**Look-aside（外部参照型）ロードバランシング**は、専用のLBサーバーに負荷情報を集約し、クライアントが最適なバックエンドアドレスを問い合わせた上で直接通信するハイブリッドモデルだ。クライアントの判断と実際のサーバー状態の一貫性をどう保つかが技術的課題となる。

### gRPC-Webとブラウザの制約

ブラウザからgRPCを直接使うことは、2026年現在も不可能だ。ブラウザのHTTP APIはHTTP/2のフレームレベルの制御を提供しない——HTTP/2の使用を強制できず、生のHTTP/2フレームにもアクセスできない。

**gRPC-Web** はこの制約を回避するプロトコルで、ブラウザが利用できるXHR/Fetch APIの範囲内でgRPCのセマンティクスを再現する。ただしClient StreamingとBidirectional Streamingは使えない（Server Streamingのみ対応）。また、gRPC-WebサーバーまたはEnvoyのようなプロキシがgRPC-WebフレームとネイティブgRPCフレーム間の変換を担う必要がある。

### Connectプロトコル——gRPCの哲学をHTTPネイティブに

Buf社が開発したConnectプロトコルは、gRPCの設計思想を維持しながらHTTPインフラとの互換性を大幅に改善する。最大の設計判断は**HTTPトレーラの廃止**だ。gRPCはHTTP/2トレーラに依存するが、多くのプロキシやCDNがトレーラを正しく処理できない。Connectはこれを排除し、エラー情報をJSON形式でレスポンスボディに埋め込む。

Unary RPCでは、生のProtobufメッセージ（またはJSON）がHTTPボディとしてそのまま送られる。`curl`でデバッグでき、ブラウザのネットワークインスペクタで中身を確認できる。これは「REST的なシンプルさ」とProtobufの型安全性の両立だ。

ストリーミングでは、1バイトのフラグ+4バイトのビッグエンディアン長さプレフィックスという最小限のフレーミングを使う。最後のメッセージに`EndStreamResponse`というJSONオブジェクトを付加し、エラーとトレーリングメタデータを運ぶ。

Connectは**HTTP/1.1、HTTP/2、HTTP/3のすべてで動作する**。仕様はHTTPバージョン固有のフレーミング詳細に依存しない設計だ。さらに副作用のないRPCにはHTTP GETを使えるため、ブラウザキャッシュとCDNキャッシュが活用できる。

ConnectはgRPC互換でもある——同じProtobuf定義から、Connectプロトコル、gRPCプロトコル、gRPC-Webプロトコルのすべてをサポートするサーバーを構築できる。

### 最新動向

#### Google MCPへのgRPCトランスポート提案（2026年2月）

GoogleがMCP（Model Context Protocol）のトランスポート層としてgRPCを追加する提案をInfoQが報じている。MCPは現在JSON-RPC over HTTPをトランスポートとして使用しているが、企業内でgRPCを広く採用している組織にとっては、既存のgRPCインフラをそのまま活用できることが大きな利点となる。プラガブルトランスポートインターフェースのPython SDK PRが進行中であり、JSONをProtobufに置き換えることで帯域幅とCPUオーバーヘッドの大幅削減が見込まれる。

A2A（Agent-to-Agent）プロトコルもv0.3でgRPCサポートを追加しており、エージェント間通信の高性能化が進んでいる。IDLによるインターフェース定義→コード生成というgRPC/Protobufのパラダイムが、AI時代のプロトコル設計にも浸透しつつある。

#### eBPFによるgRPCオブザーバビリティ

Grafana Beyla（OpenTelemetry eBPF Instrumentation, OBIとして寄贈予定）は、eBPFを使ってHTTP/gRPCサービスのトレースとメトリクスをコード変更なしで自動収集する。カーネルレベルでプロトコルを解析するため、言語を問わず、Rust/Go/Java問わずgRPCのレイテンシとエラー率を透過的に観測できる。

IsovalentのTetragonはさらに深い層で、syscallレベルでgRPC通信を監視し、ポリシーベースのセキュリティエンフォースメントを実現する。これらのツールは、gRPCのバイナリプロトコルという「人間に不透明」な特性を、カーネルレベルの計装で補完する重要な役割を果たす。

## 気づき・洞察

### 「意図的な制約」の設計哲学が繰り返し現れる

Protobufのスキーマ進化ルール——フィールド番号を絶対に再利用しない、`required`を廃止する——は、eBPFの検証器がチューリング不完全性を意図的に選択したのと同じ設計哲学だ。「できないことを明確にする」ことで、システム全体の安全性を確保する。proto3が`required`を廃止した判断は、「将来の自分たちの手を縛らない」という長期的視点に基づいている。

### L4/L7ロードバランシング問題はHTTP/2の「成功の代償」

HTTP/2の多重化はパフォーマンスの大幅な改善だが、ロードバランシングにおいては新たな課題を生んだ。これは技術進化における典型的なパターンだ——ある問題を解決する革新が、別のレイヤに新たな問題を押し出す。gRPCのL4 LB問題は、サービスメッシュという新たな抽象化レイヤの必要性を生み出した。

### ConnectプロトコルはgRPCの「デバッガビリティ債務」の返済

gRPCのバイナリプロトコルとHTTP/2トレーラへの依存は、性能と引き換えにデバッガビリティを犠牲にした。Connectはこの「技術的債務」を返済する試みであり、JSONエラー、HTTPネイティブセマンティクス、`curl`互換性を回復する。性能とデバッガビリティのトレードオフ曲線上で、gRPCとRESTの中間的な最適点を見つけた設計だ。

### IDLファースト思想がAIプロトコル時代に復活

MCPやA2AがJSON-RPCで始まり、後からgRPC/Protobufへの対応を追加する動きは、「まずシンプルに始めて、スケール時に型安全性を追加する」という自然な進化だ。しかしProtobufのEditions移行が示すように、IDLの設計判断は長期にわたって影響を及ぼす。AIエージェント間通信がProtobufのIDLを採用するなら、Agent CardとProtobufサービス定義の関係性の設計が、今後のエコシステムの拡張性を左右するだろう。

## 他分野との接続

**音楽（楽譜とIDL）**: 楽譜は演奏のIDLと言える。作曲家がスキーマ（楽譜）を定義し、演奏者がそこからコード（演奏）を生成する。Protobufのスキーマ進化——後方互換性を保ちつつフィールドを追加する——は、交響曲の改訂版が原曲の聴衆を疎外しないことに似ている。ショスタコーヴィチが後期に交響曲の編成を変えつつも構造的一貫性を保ったように。

**ゴルフ（コースマネジメントとAPI設計）**: gRPC/REST/GraphQLの使い分けは、ゴルフのクラブ選択に通じる。ドライバー（gRPC）は飛距離だが正確性が求められ、アイアン（REST）は汎用的で安定し、ウェッジ（GraphQL）は精密なアプローチに使う。すべてのショットをドライバーで打たないように、すべてのAPIをgRPCにする必要はない。

**解剖学（デッドライン伝播と神経系）**: gRPCのデッドライン伝播は、痛覚信号が末梢から中枢に伝わりながら「経過時間を差し引いて」反応閾値を調整するメカニズムに類似する。分散システムの「タイムアウト」と生体の「反応時間」は、どちらもカスケード障害を防ぐためのフィードバック制御だ。

**哲学（プラトンのイデア論とスキーマファースト）**: Protobufの.protoファイルは、プラトンのイデア（理想形）に相当する。実際のメッセージは.protoという「イデア」の現世での表現（影）であり、.protoが変わらない限り、どの言語で実装しても本質は同じだ。前回学んだプラトンの洞窟の比喩——影と実体の関係——がそのまま当てはまる。

## 次に深掘りしたいこと

- **gRPCリフレクションとサービスディスクリプタ**: Protobuf記述子を使ったランタイムでのサービス定義取得。grpcurlやPostmanの仕組み
- **Protobuf Editions実践**: Edition 2024の具体的なフィーチャーフラグ設定と、proto3からの移行手順
- **Connect + Next.js/Remix統合**: Connectプロトコルを使ったフルスタックTypeScriptアプリケーションの実装パターン
- **gRPCとKubernetesのヘルスチェック**: gRPC Health Checking Protocolとk8sのgrpc readiness/livenessプローブの統合
- **HTTP/3（QUIC）上のgRPC**: UDPベースのQUICがgRPCのHead-of-Line Blocking問題を解決する可能性
- **Buf Schema Registry**: Protobufスキーマのバージョン管理・互換性チェック・コード生成のマネージドサービス

Sources:
- [gRPC Core Concepts](https://grpc.io/docs/what-is-grpc/core-concepts/)
- [gRPC on HTTP/2](https://grpc.io/blog/grpc-on-http2/)
- [gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)
- [gRPC Load Balancing](https://grpc.io/blog/grpc-load-balancing/)
- [Protocol Buffers Overview](https://protobuf.dev/overview/)
- [Proto3 Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [Protobuf Editions Overview](https://protobuf.dev/editions/overview/)
- [Protobuf Editions are here - Buf Blog](https://buf.build/blog/protobuf-editions-are-here)
- [Connect Protocol Reference](https://connectrpc.com/docs/protocol/)
- [Connect Introduction](https://connectrpc.com/docs/introduction/)
- [Connect-Web - Buf Blog](https://buf.build/blog/connect-web-protobuf-grpc-in-the-browser)
- [The State of gRPC-Web](https://grpc.io/blog/state-of-grpc-web/)
- [Google Pushes for gRPC Support in MCP - InfoQ](https://www.infoq.com/news/2026/02/google-grpc-mcp-transport/)
- [gRPC as a Custom Transport for MCP - Google Cloud Blog](https://cloud.google.com/blog/products/networking/grpc-as-a-native-transport-for-mcp)
- [gRPC vs REST - Google Cloud Blog](https://cloud.google.com/blog/products/api-management/understanding-grpc-openapi-and-rest-and-when-to-use-them)
- [API Showdown: REST vs GraphQL vs gRPC - InfoQ](https://www.infoq.com/presentations/rest-graphql-grpc/)
- [Istio gRPC Proxyless Service Mesh](https://istio.io/latest/blog/2021/proxyless-grpc/)
- [How eBPF Is Powering Observability - The New Stack](https://thenewstack.io/how-ebpf-is-powering-the-next-generation-of-observability/)
- [Learning eBPF for Better Observability - InfoQ](https://www.infoq.com/articles/learning-ebpf-observability/)
