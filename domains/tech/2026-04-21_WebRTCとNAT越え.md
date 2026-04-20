# WebRTCの仕組みとNAT越え（ICE/STUN/TURN）
**日付**: 2026-04-21  
**分野**: tech  
**タグ**: #WebRTC #NAT #ICE #STUN #TURN #P2P #リアルタイム通信

## 学んだこと

WebRTCは単一の仕様ではなく、IETFとW3Cが協働して作り上げた**プロトコルスイート**である。RFC 8825が全体のオーバービューを定義し、ブラウザベースのリアルタイム通信のための3つのJavaScript APIを外部に露出する——`getUserMedia`（カメラ・マイクへのアクセス）、`RTCPeerConnection`（P2P接続の中核）、`RTCDataChannel`（任意バイナリデータのP2P転送）。この3つのAPIの背後では、ICE・STUN・TURN・SDP・DTLS・SRTP・SCTP・RTPといった既存のIETF標準が層状に組み合わされており、「ブラウザに実用的なリアルタイム通信を持ち込む」という一点のために十数個のRFCが束ねられている姿は、Wasm・HTTP/3・OCIと並ぶ「現代的な積層標準」の代表例である。

最も特徴的な設計判断は**シグナリングの標準化拒否**である。WebRTC仕様はピアが互いのSDPを交換する方法を一切規定しない。理由は明確で、既存アプリケーションが持つチャット・セッション・認可基盤は千差万別であり、そこに統一プロトコルを押し付けると導入障壁が高まる。結果として開発者はWebSocket・HTTP Long Polling・XMPP・Matrix・SIP over WebSocketなど任意のシグナリング手段を選べるが、裏を返せばWebRTCアプリは必ずシグナリングサーバを立てる必要があり、「純粋なP2P」ではない現実が生じる。

SDP（Session Description Protocol, RFC 8866）は**オファー/アンサーモデル**の媒体となる。発呼側が`createOffer()`でメディア形式・コーデック・ICE候補・DTLSフィンガープリントなどを記述したSDPを生成し、受信側は`setRemoteDescription()`でそれを取り込み`createAnswer()`で自分側のSDPを返す。SDPはv=/o=/s=/m=/a=といった行ベースのテキストで、1994年のmbone時代から続くレガシーフォーマットだが、WebRTCでは「BUNDLE」（複数メディアを単一トランスポートに多重化）、「rtcp-mux」（RTPとRTCPの同一ポート化）、「trickle ICE」の表明などモダンな属性が積み重ねられている。

NAT越えの核心はNATの**マッピング挙動の分類**にある。RFC 3489の古典的分類ではFull Cone・Restricted Cone・Port Restricted Cone・Symmetricの4種だが、現代のRFC 5780/4787ではEndpoint-Independent Mapping（EIM）とEndpoint-Dependent Mapping（EDM）という軸で捉え直されている。EIMなら内部→外部の宛先が変わってもパブリック側のポートが固定されるため、STUNで取得した自分のパブリックアドレスを相手に伝えればホールパンチングが成立する。ところがSymmetric NAT（典型的にはキャリアグレードNATや一部企業ファイアウォール）は宛先ごとに異なるポートを割り当てるため、STUNで観測したアドレスと実際にピアから届く時のアドレスが一致せず、直接通信は**構造的に不可能**になる。

STUN（RFC 5389、改訂版RFC 8489）は驚くほどシンプルなプロトコルで、クライアントがサーバにBindingリクエストを送り、サーバは「私にはあなたがこのIP:Portに見えます」とXOR-MAPPED-ADDRESSで返すだけ。このエコー機能だけで、NATの外側から見た自分のアドレスを知ることができる。TURN（RFC 5766、改訂版RFC 8656）はSTUNの拡張で、Symmetric NAT同士が通信できない場合の最後の砦として**中継サーバ経由**で全トラフィックをリレーする。TURNは帯域とレイテンシのコストが大きいため「可能な限り避けたい選択肢」だが、実運用では10-20%のセッションがTURNに落ちると言われる。

ICE（RFC 8445）はこれらを統合する**優先順位付き接続性チェックフレームワーク**である。各ピアはローカル候補（自ホストの全IP）、サーバリフレクティブ候補（STUNで取得したパブリックアドレス）、リレー候補（TURN割当アドレス）を収集し、相手の候補と総当たりでペアを作り、優先度順に4-wayハンドシェイク（STUN Bindingリクエスト）で連結性を確認する。優先度は式`priority = (2^24)*type + (2^8)*local + (2^0)*(256-component)`で決まり、ホスト>サーバリフレクティブ>リレーの順に高い。RFC 8838のTrickle ICEでは候補収集完了を待たずに取得し次第インクリメンタルに相手へ送れるため、セッション確立時間を数秒単位で短縮できる。

暗号化は**DTLS-SRTP**の二段構え（RFC 5764）で強制される。平文メディアは仕様上許されず、ブラウザは例外なく拒否する。まずDTLS（UDP版TLS）ハンドシェイクで鍵交換を行い、そこから派生した鍵でSRTPが各RTPパケットをAES-128で暗号化する。DTLSのフィンガープリントはSDP経由で交換されるため、シグナリング経路が信頼できれば中間者攻撃を防げる——つまりシグナリングのセキュリティ（通常TLS上のWebSocket+アプリ層認証）がE2E保証の土台になる。

最後に、**Google Congestion Control（GCC）** がネットワーク輻輳への応答を担う。UDP上で動作するWebRTCは自前で輻輳制御を持つ必要があり、GCCは受信側のパケット到着間隔変動（遅延勾配）と送信側のパケットロス率の二つを並列に観測して送信レートを動的に調整する。単なるロスベースではなく**遅延ベースの早期検知**を組み合わせる点が特徴で、バッファブロート下でもロスが発生する前にビットレートを落とせる。加えてProbing（通常トラフィックに上乗せした探査パケット）で使える帯域の上限を能動的に探る。

## 気づき・洞察

WebRTCの設計で最も考えさせられるのは、**「何を標準化し、何を意図的に標準化しないか」** という線引きの鋭さである。メディア層（コーデック・RTP・SRTP・DTLS）は完全に標準化する一方で、シグナリング層は完全にアプリケーション任せ。一見矛盾しているこの判断は、「ブラウザ間の相互運用に必須な部分」と「アプリケーション固有の要件が強い部分」を分離する哲学的選択である。結果としてWebRTCは既存のあらゆる通信アプリに「後付け」で埋め込めるようになり、Discord・Slack・Zoom・Google MeetからシステムがP2Pで動くのに、どのSDKを使っているかで中身が全く違うという豊かな多様性が生まれた。標準化の濫用は相互運用性を一見高めるが、採用コストを押し上げて結局「最大公約数の機能しか使われない」事態を招く——MCPがトランスポートを宣言的にした一方でAgent Cardの内部構造を固定していないのと同じ設計パターンである。

P2Pという言葉の**幻想と現実**も重要だ。WebRTCはP2Pの代表選手として語られるが、実際には（1）必須のシグナリングサーバ、（2）必須のSTUNサーバ、（3）高い確率で必要になるTURNサーバ、（4）大規模会議では避けられないSFU/MCU——と中央集権要素が層状に積み重なっている。完全な端末間直接通信が成立するのは、両ピアがEIM型NATか公開IPを持ち、かつファイアウォールが寛容なケースに限られ、実運用データでは30-50%程度でしかない。これはActivityPubのFederationとは対照的で、ActivityPubは「サーバ間のpush配送」という前提のためNAT越えの問題をほぼ意識しない。P2Pが真に成立するには**端末の常時到達可能性**が前提であり、モバイル・スリープ・NATという三重苦の現代ネットワークでは構造的に困難である。

「インターネットの端点原理（end-to-end principle）」が1981年のSaltzer・Reedの論文で提唱されて以降、IPv4アドレス枯渇によるNATの蔓延はこの原理への最大の裏切りだった。WebRTCとICEは**その裏切りを前提として受け入れ、迂回路を規約として整備する**という実践的な諦めの産物である。IPv6がもたらすはずだった「全端末が公開IPを持つ世界」は2026年現在も実現しておらず、ICEは当面不要にならない。この「理論的に美しい解（IPv6）が普及しきれないから、泥臭い迂回（NAT越え）をプロトコル化する」というパターンは、HTTP/2がTCPのHead-of-Line Blockingを完全には解けずQUICを生んだのと似ている。インターネットの進化は、破綻した前提を置き換えるのではなく、その上に層を重ねていく。

## 他分野との接続

tech分野のActivityPubとWebRTCは**対極の分散通信モデル**として並べると興味深い。ActivityPubはサーバ間のstore-and-forward型連合で、各サーバが公開IPを持つ前提のためNAT越えは問題にならないが、大規模フォロワーへのfan-out爆発に悩む。WebRTCは端末間直結を目指すがNATと戦い続ける。CRDTとの接続も濃厚で、WebRTC DataChannelはYjs・Automergeなどのローカルファースト同期プロトコルの主要な転送手段となっている——SignalServerだけを中央に置いて、あとは端末間でCRDT更新を直接配送するアーキテクチャが実現できる。

CS分野の観点では、WebRTCがUDP上に**TCPもどきの輻輳制御とセッション管理**を再発明している姿が示唆的だ。GCCはTCP CUBICとは異なる遅延勾配検知ベースで、低遅延要件のために「ロスを待つ」TCPの常識を捨てている。DTLSはTLSをパケットロスに耐えるよう変形した版で、TLSが前提とする順序保証と信頼性転送をすべて外している。これらは「TCPスタックをそのまま使えば楽なのに、あえてUDP上で再構築する」というトレードオフの具体例であり、CS授業で習う「TCP vs UDP」の二項対立が実務では「UDP+カスタム制御層」という第三の道を生んでいることを示す。

音楽・ピアノ分野との意外な接続として、**リモートアンサンブル演奏**の技術的困難がある。WebRTCの一般的なエンドツーエンド遅延は100-300msで、通常の会話では問題ないが、アンサンブル演奏では20-30ms以下が必要（音速で7-10m離れた奏者の距離相当）。JackTrip・JamKazam・SonobusなどはWebRTCではなく独自の極低遅延UDPプロトコルを採用し、FEC（前方誤り訂正）で再送を不要にしパケットロスは音声ミュートで受け入れる、という「品質より遅延」の哲学で割り切っている。これはWebRTCが会話用途のために行った設計判断（多少の遅延を許容してパケット順序再構築する）と真逆で、リアルタイムメディアの「リアルタイム」は目的によって桁が違う要件になる好例だ。

## 次に深掘りしたいこと

- **Media over QUIC（MoQ）**——IETF moqワーキンググループが進める次世代プロトコル。WebTransport+WebCodecsで配信を分離し、WebRTCがカバーしきれないライブ配信とインタラクティブ通信の中間領域を狙う
- **SFUの内部実装**——LiveKit・Janus・mediasoup・Pion SFUのアーキテクチャ比較。シミュルキャスト・SVC（Scalable Video Coding）による適応的レイヤー選択の仕組み
- **E2EE for group calls**——Insertable Streams APIでSFU通過後もメディアを暗号化する仕組み。Signal・Whatsapp・Zoomの実装差
- **WHIP/WHEP**——WebRTC-HTTP Ingestion/Egress Protocol。RTMPを置き換えるWebRTCベースの配信プロトコル。OBS Studio対応
- **WebCodecs + WebTransport + WebAssembly**——「ブラウザで独自の低遅延通信を組む」という新しい潮流。Zoomが2023年から実用化

## 参考ソース

- [RFC 8445 - Interactive Connectivity Establishment (ICE): A Protocol for NAT Traversal](https://datatracker.ietf.org/doc/html/rfc8445)
- [RFC 8825 - Overview: Real-Time Protocols for Browser-Based Applications](https://datatracker.ietf.org/doc/html/rfc8825)
- [RFC 8838 - Trickle ICE](https://datatracker.ietf.org/doc/rfc8838/)
- [RFC 8489 - Session Traversal Utilities for NAT (STUN)](https://datatracker.ietf.org/doc/html/rfc8489)
- [RFC 8656 - Traversal Using Relays around NAT (TURN)](https://datatracker.ietf.org/doc/html/rfc8656)
- [RFC 5764 - DTLS-SRTP](https://datatracker.ietf.org/doc/html/rfc5764)
- [MDN Web Docs - Introduction to WebRTC protocols](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Protocols)
- [MDN Web Docs - WebRTC connectivity](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Connectivity)
- [WebRTC for the Curious (webrtcforthecurious.com)](https://webrtcforthecurious.com/)
- [draft-ietf-rmcat-gcc-02 - Google Congestion Control](https://datatracker.ietf.org/doc/html/draft-ietf-rmcat-gcc-02)
- [Kurento Docs - NAT Types and NAT Traversal](https://doc-kurento.readthedocs.io/en/stable/knowledge/nat.html)
- [BlogGeek.me - WebRTC SFU Explained (Tsahi Levent-Levi)](https://bloggeek.me/webrtcglossary/sfu/)
