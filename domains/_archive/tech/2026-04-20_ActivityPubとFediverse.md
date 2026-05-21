# ActivityPubとFediverse——分散SNSの設計哲学
**日付**: 2026-04-20  
**分野**: tech  
**タグ**: #ActivityPub #Fediverse #Federation #Mastodon #ATProtocol #Nostr #分散システム

## 学んだこと

### ActivityPubの技術仕様 (W3C Recommendation, 2018-01-23)
ActivityPubはW3C Social Web WGが標準化したクライアント-サーバー/サーバー-サーバー両対応のプロトコル。中核は **Actor Model**——各ユーザー（Person/Service/Group/Application/Organization）は独立したactorで、固有URIを持ち、4つのcollection endpointを公開する：`inbox`（受信）、`outbox`（送信履歴）、`followers`、`following`。actorオブジェクトはJSON-LD（Activity Streams 2.0 + ActivityPub context）でserializeされる。

通信モデルは **POST to inbox / GET from outbox**。AがBをフォローすると、AのサーバーはBのinboxに`Follow` activityをHTTP POSTし、Bのサーバーが`Accept` activityをAのinboxへ返す。以降、Bの投稿（`Create(Note)`）はBのサーバーが全followerのinbox（または`sharedInbox`）にfan-outする。`Like`, `Announce`（boost）, `Undo`, `Delete`, `Update`も全てactivityとして統一的に扱われる——これは**「動詞をデータ化する」**Activity Streamsの哲学で、ObjectとVerbを分離することで新しい挙動をvocabulary拡張だけで追加できる。

### Federation実装メカニズム
**WebFinger**（RFC 7033）でactor discoveryを行う：`@alice@mastodon.social`というacct: URIから`https://mastodon.social/.well-known/webfinger?resource=acct:alice@mastodon.social`を引き、`self` linkでactor URI（JSON-LD）を取得する。

**HTTP Signatures**（Cavage draft、IETF httpbis WGで標準化進行中）は認証のデファクト。送信サーバーは`Host`, `Date`, `Digest`, `(request-target)`等をRSA-SHA256で署名し、受信サーバーがactorの`publicKey`を引いて検証。TLSは経路を守るが、**メッセージ単位の出所保証**はHTTP Signaturesが担う——W3C仕様が authentication/authorization を意図的に省いた（"out of scope"）結果、FEP (Fediverse Enhancement Proposals) が実装規範として結晶化した。

### 主要実装の設計差分
- **Mastodon**（Ruby/Rails, Sidekiq）：Twitter型マイクロブログ、500字制限、linear timeline
- **Misskey/Firefish/Sharkey**（Node.js/TS）：絵文字リアクション、MFM記法、AS2.0独自拡張
- **Pleroma/Akkoma**（Elixir）：軽量、BEAM VMのプロセスモデルがfan-outと好相性
- **Lemmy**（Rust）：Reddit型forum。`Group` actorをcommunityとして使い、`Page`/`Note`+`inReplyTo` chainでネストコメント表現
- **PeerTube（動画）/ Mobilizon（イベント）/ BookWyrm（読書）**：同一プロトコルで異種サービスが連合

### Threads (Meta) の連合対応
2024年3月ベータ→2025年に欧州含む拡大。Threads公式アカウント（`@username@threads.net`）をMastodon等からフォロー可能。ただし**非対称**：DM非対応、フォロワーカウント相互不整合、検索非連合、外部フォロー限定的。**数億MAU抱えるMeta参入**はモデレーションasymmetry（小規模サーバーのブロックは効かない、逆は致命）、サーバー負荷（Meta側fan-inがDDoS相当）、Embrace-Extend-Extinguishへの警戒を生む。

### スケーリングと分散の限界
- **Fan-out爆発**：フォロワー10万人の1投稿=10万HTTP POST（sharedInboxで同一サーバー内は集約）。Mastodon大規模インスタンスはSidekiq滞留が常態化
- **モデレーション**：共通のspam/abuse DBなし、#fediblockハッシュタグ等ad-hoc協調
- **DoS耐性**：inbox POSTは署名検証にcompute要、rate limitingは各実装任せ

### Nostr/AT Protocol/Nomadic Identityとの比較
ActivityPubの弱点は**account portability**：`@alice@server.A`がserver.Aに依存、移行時にfollower再構築必要（Mastodonの`Move` activityは部分解決）。

- **Nostr**：secp256k1公開鍵=identity、relayは単なる中継、複数relayへ同じ署名済みeventを投げる（"multi-homing"）。鍵紛失=完全消失
- **AT Protocol (Bluesky)**：DID + Personal Data Server (PDS) + Relay (firehose) + AppViewの4層分離。PDSを乗り換えてもDIDが不変なのでfollowers保持、labelerでモデレーション分離
- **Nomadic identity (Zot/Streams)**：同一identityを複数サーバーに同時クローン、FEP-ef61でActivityPubに後付け提案中

**本質的トレードオフ**：ActivityPub=server-centric（sysadmin権威）、Nostr=key-centric（鍵管理責任）、AT Protocol=DID-centric（PDS分離の複雑性）。

### E2EE非対応
ActivityPubの"private" messageは**宛先指定（`to`/`cc`）による配信範囲制御**に過ぎず、サーバー管理者は平文を読める。E2EEは仕様に**存在しない**。FEP-5bf0（Tox-like）、FEP-0ea0（PGP）等が草案段階。Signal/Matrix由来のOlm/Megolm移植が議論されるが、multi-device鍵管理とforward secrecyをfederated環境で実装する複雑性が障害。

## 気づき・洞察

ActivityPubの actor-based design は **分散オブジェクト指向 + emailのstore-and-forward**——Alan Kayの本来のOO定義（"messaging, local retention and protection and hiding of state"）に近い。**stateの局所性**が鍵で、誰もglobal viewを持たず、各サーバーが知る範囲のみ一貫性を保証する（CAP的にはAP優先、eventually consistent）。

中央集権SNS（Twitter/X）は**single-writer, single-source-of-truth**、ユーザーは"tenant"に過ぎない。ActivityPubが提供するのは **exit の権利**——気に入らなければ別サーバーへ、あるいは自分で立てる。中央集権SNSの"voice"しかない状況に対し、Fediverseはexitを技術的に保障する。ただしportability限界でexit costは未だ非ゼロ——ここがAT Protocol/Nomadic identityが攻める設計空間。

ActivityPubは**「完璧な分散」ではなく「email以来最も成功した連合」**を目指した実用主義の産物。email (SMTP) がspam/spoofingに苦しみつつ50年動いている事実こそ、この設計の長期生存可能性を示唆する。

## 他分野との接続

- **cs/分散システム**：CAP定理でAP優先、eventually consistent。CRDTやevent sourcingと同じ哲学——誰も中央制御していないのに局所相互作用から大域安定状態が創発する
- **bread/サワードウ微生物生態系**：各菌が自律的相互作用で安定ecosystem形成→各サーバーが自律的actor相互作用で連合ecosystem形成。pH勾配=各サーバーのmoderation policy勾配
- **music/ムソルグスキー**：西欧アカデミズム中央集権への対抗としての民族主義＝中央集権SNSへの対抗としてのFediverse。「公認されない」自律性の価値

## 次に深掘りしたいこと

- FEP-ef61（nomadic identity on ActivityPub）の実装詳細
- AT Protocolのlabeler composable moderation設計
- Nostrのzapとbitcoin経済的incentiveによるspam抑制
- Threads連合の長期的影響——Metaのembrace戦略がFediverseを歪める可能性

## 参考ソース

- [W3C ActivityPub Recommendation (2018)](https://www.w3.org/TR/activitypub/)
- [W3C Activity Streams 2.0 Core](https://www.w3.org/TR/activitystreams-core/)
- [Fediverse Enhancement Proposals (FEP)](https://codeberg.org/fediverse/fep)
- [AT Protocol Specification](https://atproto.com/specs/atp)
- [Mastodon Documentation — Federation & ActivityPub](https://docs.joinmastodon.org/spec/activitypub/)
