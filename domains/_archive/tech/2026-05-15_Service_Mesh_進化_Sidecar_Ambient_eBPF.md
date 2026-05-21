# Service Meshの進化：Sidecarから Ambient/eBPF へ
**日付**: 2026-05-15  
**分野**: tech  
**タグ**: #ServiceMesh #Istio #Cilium #eBPF #Kubernetes #Sidecar

## 学んだこと

### Sidecar モデルの本来の発想と限界

Linkerd v1 (2016) と Istio (2017) が確立した「Sidecar プロキシ」モデルは、Kubernetes Pod ごとに Envoy/Linkerd2-proxy を注入し、アプリケーションと同じネットワーク名前空間で iptables 経由でトラフィックを透過的にハイジャックする方式だった。これにより、アプリケーションコードを変更せずに mTLS・トレース・サーキットブレイカー・L7 ルーティングが導入できる。だが運用するとすぐに痛みが見えてくる：

- **リソースオーバーヘッド**: Pod ごとに 50-200MB の Envoy が起動する。1000 Pod のクラスタなら、それだけで数十 GB のメモリと数十コアの CPU が「メッシュのインフラ」に消える
- **レイテンシ**: 1 リクエストでクライアント側 sidecar → サーバ側 sidecar の 2 ホップが追加される。p99 で 1-5ms のオーバーヘッドが乗る
- **ライフサイクルの絡み**: Pod 起動時、sidecar が ready になる前にアプリが外部接続しようとすると失敗する（race condition）。Pod 終了時も sidecar が先に落ちるとアプリのドレインが詰まる
- **アップグレード地獄**: メッシュ全体の Envoy 更新は全 Pod の再起動を伴う

### Cilium Service Mesh：eBPF による sidecarless 革命

Isovalent の Cilium（2021 年に sidecar-less メッシュを発表）は、データプレーンを Linux カーネル内の eBPF プログラムとして実装する。L3/L4 のルーティング・ロードバランシング・NetworkPolicy・mTLS はすべてカーネル空間で処理され、ユーザー空間プロキシを経由しない。L7 機能（HTTP ヘッダ操作、gRPC LB）が必要な場合のみ、**ノード単位で共有される Envoy** を経由する。

これの帰結は劇的だ：
- Pod ごとの sidecar 不要 → クラスタ全体のメモリ・CPU 消費が大幅減
- カーネル内処理 → コンテキストスイッチが減り、レイテンシ削減（Cilium のベンチマークでは P99 で 50% 以上短縮の報告も）
- iptables の脱却 → 大規模クラスタでの iptables ルール爆発（N² 問題）を回避

### Istio Ambient Mesh：L4/L7 を分離する設計

Cilium に呼応して 2022 年に Istio が発表した Ambient Mesh は、データプレーンを 2 層に分割する：

1. **ztunnel（Zero Trust Tunnel）**: ノードごとに DaemonSet として動作する Rust 製の軽量プロキシ。L4 機能（mTLS, L4 認可, テレメトリ）のみを担う。Pod とは別ネットワーク名前空間で動き、HBONE (HTTP/2 CONNECT-based Overlay Network Encapsulation) でノード間トラフィックを暗号化トンネリングする
2. **Waypoint Proxy**: L7 機能（HTTP ルーティング、リトライ、L7 認可）が必要な namespace/ServiceAccount にのみデプロイされる Envoy。共有リソースとして動く

つまり「全 Pod に Envoy をつける」のではなく、「mTLS だけ全ノードで、L7 は必要な場所だけ」というオプトイン構造になった。istiod は xDS で ztunnel に L4 設定を、waypoint に L7 設定を別々に配信する。

### HBONE プロトコル：4-way ハンドシェイク削減

HBONE は HTTP/2 の CONNECT メソッドの上に mTLS を載せたトンネリングで、ztunnel 間で多重化された永続コネクションを張る。これにより、TCP ハンドシェイク + TLS ハンドシェイクのオーバーヘッドが接続初回のみに圧縮される。

### 業界の対立軸：プロキシ陣営 vs カーネル陣営

- **プロキシ陣営（Istio, Linkerd, Envoy）**: 「カーネルは複雑すぎる、ユーザー空間プロキシで柔軟性を保つべき」
- **カーネル陣営（Cilium, Isovalent）**: 「sidecar はオーバーキル、eBPF で十分」

Istio Ambient はある意味でこの両方を取り入れた折衷案：データプレーンの境界を「Pod の中」から「ノードレベル」に引き上げ、必要なときだけ L7 プロキシを差し込む。Cilium と Istio は Service Mesh Interface (SMI) と Gateway API という共通インターフェースで部分的に互換性を確保しつつある。

## 気づき・洞察

**「インフラ機能はどこに置くべきか」という古典問題の再演**。アプリ内ライブラリ（Hystrix 等）→ Sidecar → カーネル拡張 → 共有プロキシと、メッシュの境界は徐々に「アプリから離れて、より下のレイヤへ」移動してきた。これは Unix 哲学における「機能をどのレイヤに置くか」の古典的議論の再演で、各レイヤにはトレードオフがある：
- アプリ内：性能◎・運用×（言語別実装が必要）
- Sidecar：透過性◎・リソース×
- カーネル/共有プロキシ：効率◎・柔軟性×（eBPF verifier の制約、ロード時の権限問題）

**「全部の Pod に同じ機能をコピーする」非効率**への気づきが、ここ数年の革命の本質。同じノードで動く 30 個の Pod に同じ Envoy のコピーを 30 個用意するのは無駄、というシンプルな観察から Ambient/Cilium が生まれた。

**Rust が「カーネルじゃないが性能とメモリ安全性が必要な領域」を埋めている**。ztunnel が Rust なのは偶然ではなく、cloud-native の中で C++ Envoy の置き換えとして Rust が選ばれる流れの一つ。Cloudflare の Pingora、Linkerd2-proxy、Discord の rustls 採用などと同根。

## 他分野との接続

- **cs / 分散システム**: Service Mesh は分散システムの「コントロールプレーン / データプレーン分離」の典型例。Raft/Paxos の合意は istiod の設定配信に、CAP 定理は xDS の eventual consistency に現れる
- **anatomy / 神経系**: sidecar は「全シナプスに個別のミエリン鞘」、Ambient/Cilium は「ノードごとに集約された Schwann 細胞」のアナロジー。資源効率と機能局所性のトレードオフは生体システムでも同じ
- **bread / 発酵管理**: ノード単位の共有プロキシは、パン工房の「中央キッチンで温度管理し、各ベンチ（Pod）には軽い装備だけ置く」設計に近い
- **music / 対位法**: 各 Pod が独立して動く（sidecar）vs 全声部を中央でまとめる（Ambient）は、フーガでの「ホモフォニー的整理」と「真の独立声部」の対比に似ている

## 次に深掘りしたいこと

- HBONE プロトコルの実装詳細と、QUIC ベース版（HTTP/3 CONNECT）への移行可能性
- Cilium Tetragon によるランタイム脅威検知と eBPF の可観測性
- Linkerd の microproxy アプローチ（Rust 製の極小 sidecar）が Ambient/Cilium に対してどう生き残るか
- Service Mesh と Gateway API の共存戦略（L7 ルーティングがどちらの責任か）

## 主要参考ソース
- [Istio Ambient Overview](https://istio.io/latest/docs/ambient/overview/)
- [istio/istio: ztunnel architecture](https://github.com/istio/istio/blob/master/architecture/ambient/ztunnel.md)
- [Solo.io: Traffic in ambient mesh — ztunnel, eBPF, waypoint](https://www.solo.io/blog/traffic-ambient-mesh-ztunnel-ebpf-waypoint)
- [Codecentric: From sidecars to sidecarless](https://www.codecentric.de/en/knowledge-hub/blog/sidecars-sidecarless-evolution-service-mesh-technologies-istio-cilium)
- [Cilium docs: Service Mesh](https://docs.cilium.io/en/stable/network/servicemesh/)
