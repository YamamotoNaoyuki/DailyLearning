# WebTransport と HTTP/3 双方向通信革命
**日付**: 2026-05-02
**分野**: tech
**タグ**: #WebTransport #HTTP3 #QUIC #双方向通信 #ブラウザAPI

## 学んだこと

### WebTransport とは何か
WebTransport は HTTP/3 (QUIC) の上に構築された、ブラウザとサーバ間の低遅延双方向通信のための新しい Web API。WebSocket の現代的な置換として W3C で標準化が進み、2026 年現在 Chrome / Edge / Firefox の最新版で利用可能。WebSocket と RTCDataChannel の中間を埋める位置にある。

3 つの転送プリミティブを単一の HTTP/3 コネクション上で多重化する：
1. **Unidirectional streams**: 一方向、信頼性あり、順序保証あり
2. **Bidirectional streams**: 双方向、信頼性あり、順序保証あり (`WebTransportBidirectionalStream`)
3. **Datagrams**: UDP 風、順序保証なし、信頼性なし、低遅延

各ストリームは独立に多重化されるため、HTTP/2 のように TCP レイヤで Head-of-Line Blocking が発生しない。1 つのストリームでのパケット損失が他に影響しない (QUIC のストリーム多重化機能をそのままアプリ層に露出している)。

### 動作モデル
クライアントから `https://example.com/path` に対して `new WebTransport(url)` で接続を開く。サーバ側は HTTP/3 の `CONNECT` メソッドの拡張 (`:protocol = webtransport`) でセッションを受け入れる。これは 2018 年の RFC 8441 (Bootstrapping WebSockets with HTTP/2) と同じ「拡張 CONNECT」パターンの HTTP/3 版。

セッション確立後は `WebTransport.createBidirectionalStream()` で `ReadableStream` / `WritableStream` のペアが返ってくる。Streams API と一体化しているため、`pipeTo()` や `pipeThrough()` でバックプレッシャ込みのパイプライン処理が自然に書ける。

### WebSocket との本質的差異
WebSocket は単一の TCP コネクション上に「メッセージフレーム」が並ぶモデル。1 接続 = 1 ストリーム。アプリ層で複数チャネルを多重化したければ独自プロトコルを設計するしかない。

WebTransport は QUIC のストリーム多重化を直接利用するため、アプリは「論理的な並列ストリーム」を 0-RTT で開閉できる。1 つのコネクション内で「ファイル転送ストリーム」「テキストチャットストリーム」「ピング用 datagram」を同時に走らせ、互いを阻害しない。

さらに QUIC のコネクションマイグレーション機能により、クライアントの IP アドレスが変わってもコネクションが切れない。WiFi → 5G の切替で WebSocket は切断されるが、WebTransport は継続できる。

### Datagram の意義
信頼性なし・順序保証なしの datagram は、ゲーム・ライブストリーミング・テレプレゼンスといった「最新のフレームだけ重要、古いフレームは捨てて良い」ユースケースに最適。WebRTC の `RTCDataChannel` で似たことはできたが、SDP/ICE といった P2P 用の重い signaling が必要だった。WebTransport は通常の HTTPS リクエストと同じ origin model で datagram が使えるため、CDN などサーバ集中型のアーキテクチャに自然に組み込める。

### ストリーム制御とフロー制御
QUIC レベルで両方向の `MAX_STREAMS` / `MAX_DATA` フレームによる credit ベースのフロー制御が組み込まれている。Streams API のバックプレッシャ (writer がブロックされる) はこの credit と直接連動する。アプリ開発者は明示的なフロー制御を書かずとも、輻輳に応じて自然に送信レートが調整される。

## 気づき・洞察

WebSocket が 2011 年 (RFC 6455) に標準化されてから 15 年、Web のリアルタイム通信は「TCP 上の単一ストリーム + 独自フレーミング」という制約を負ってきた。WebTransport は **「トランスポート層の能力をそのままブラウザに露出する」** 方針への転換を示す。これは WebRTC が「メディア配信の専門知識を Web に持ち込んだ」のと類似の哲学転換。

一方で「すべてを 1 接続 + 多ストリームに集約する」設計は、HTTP/3 の根幹である QUIC のコネクション概念に強く依存する。プロキシ・ロードバランサ・WAF が QUIC を理解していないと使えない。実際、企業ネットワークでは UDP/443 がブロックされていることが多く、TCP fallback が無いため「企業内では WebSocket、コンシューマ向けでは WebTransport」という棲み分けが当面続きそう。

WebTransport の存在は、HTTP/3 が単なる「HTTP/2 の高速化」ではなく **「アプリ層プロトコルの基盤」** へと進化したことを示す。HTTP/3 上で SSE, WebSocket, WebTransport, 通常の REST が並走する世界観。

## 他分野との接続

- **cs (TCP輻輳制御 2026-03-21, MVCC 2026-04-27)**: QUIC は TCP の congestion control (CUBIC, BBR) を user space で実装し直したもの。アプリ層に近い場所で輻輳制御を持つことで、Linux kernel の更新を待たずに新しいアルゴリズムをデプロイできる。MVCC が「複数の論理タイムラインを並走させる」発想と同じく、WebTransport も「複数の論理ストリームを並走させる」設計。
- **tech (Apache Iceberg 2026-04-29, MLS 2026-05-01)**: MLS や CRDT のような分散プロトコルでは、複数のメッセージタイプ (handshake, application, key update) を独立に送りたい。WebTransport の多ストリームはこれらを物理的に分離できる輸送基盤として理想的。
- **anatomy (前庭系 2026-03-21)**: 人間の感覚統合は「視覚・前庭・固有受容覚」を独立チャネルで受信して脳で統合する。WebTransport の多ストリーム多重化と、感覚チャネルの独立性 + 中枢統合という構造は同型。

## 次に深掘りしたいこと

- WebTransport over WebTransport (relaying) の議論。CDN を介した中継時のセキュリティモデル。
- MoQ (Media over QUIC) — WebTransport を基盤としたライブストリーミング新世代プロトコル。HLS/DASH より低遅延を狙う。
- QUIC の 0-RTT 再開と replay attack 対策 (idempotent request 限定)。
- ブラウザの QUIC 実装の中身 (Chromium quiche)。

## 主要な参考ソース
- [W3C WebTransport Specification](https://www.w3.org/TR/webtransport/)
- [draft-ietf-webtrans-http3 (IETF)](https://datatracker.ietf.org/doc/draft-ietf-webtrans-http3/)
- [MDN WebTransport API](https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API)
- [Chrome Developers: How to use WebTransport](https://developer.chrome.com/docs/capabilities/web-apis/webtransport)
