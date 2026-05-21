# vLLMとPagedAttentionによるLLM推論サービング
**日付**: 2026-05-04
**分野**: tech
**タグ**: #LLM #推論サービング #PagedAttention #vLLM #KVキャッシュ #システム最適化

## 学んだこと

### PagedAttentionの設計原理 — OSページングのLLMへの転用

Kwonら (SOSP 2023, "Efficient Memory Management for Large Language Model Serving with PagedAttention", arXiv:2309.06180) は、OS仮想メモリのページング機構をKVキャッシュ管理に転用するという発想で**PagedAttention**を提案した。従来のLLM推論では、各シーケンスのKVキャッシュは GPU 上で **物理的に連続な領域** に確保される必要があり、最大シーケンス長を見越したover-reservationが常態化していた。PagedAttentionはこのKVテンソルを固定長の**KV block**（典型的に 16 トークン分）に分割し、論理的に連続なシーケンスを物理的には非連続な block 群に分散させる。アテンション計算カーネル自体が `block_table[seq_id] = [phys_block_3, phys_block_17, ...]` という間接参照を経由することで、連続性の制約を取り除いた。

### KVキャッシュ・フラグメンテーションの3類型

論文によれば、従来システム (FasterTransformer, Orca等) ではKVメモリの **60-80%** が以下3種で浪費されていた:
- **内部断片化 (internal fragmentation)**: 最大長を見越した予約のうち、生成終了で未使用となる領域
- **予約過多 (reservation waste)**: まだ生成に到達していない将来分の予約
- **外部断片化 (external fragmentation)**: 異なる長さのシーケンスを連続領域に詰め込む際の隙間（バディアロケータ的な問題）

PagedAttentionでは浪費は**最後のblock末尾のみ**で発生し、実測で **4% 未満** に抑えられる。block_size=16の根拠は (a) 16トークン分でアテンションカーネルの並列度がSM占有率を飽和させる、(b) 内部断片化の上限が block_size に比例するためのトレードオフ点。論文では `b ∈ [16, 128]` で評価され、16-32が最良。

### Continuous Batching と PagedAttention の直交性

Orca が提案した iteration-level scheduling (in-flight batching) と PagedAttention は**直交**で、組み合わせで真価を発揮する。各デコードステップで完了したシーケンスを即座に取り出し、新規 prefill を空いた block に挿入できる。vLLM V1 では prefill/decode を区別せず token budget `{request_id: num_tokens}` で統一スケジュール、**chunked prefill** により長プロンプトが decode を阻害しない設計に進化した。

### プレフィックスキャッシングのMerkle連鎖

vLLM V1 では各 KV block に **SHA-256 ハッシュ** を付与し、`hash(prev_block_hash, tokens_in_block)` の Merkle 連鎖で同一プレフィックスを自動共有する。ハッシュ表で照合し、ヒット時は block table のポインタを使い回す。書き込み時のみ **Copy-on-Write** で複製。parallel sampling・beam search で **最大 55% メモリ削減・スループット 2.2x 向上**。木構造を使わず独立 block を hash table 管理するため、OSのページキャッシュと同様にLRU退避が可能になっている。

### ベンチマーク数値

元論文・公式ブログ報告:
- vs HuggingFace Transformers: **14-24x** 高スループット (単一補完)、3並列で **8.5-15x**
- vs TGI: **2.2-3.5x**
- vs FasterTransformer/Orca: **2-4x** (同等レイテンシ)
- LMSYS Chatbot Arena 実運用で **30x、GPU 数 50% 削減**

2026年時点のH100 比較 (GPT-OSS-120B, 2x H100):
- 低並列度では **TensorRT-LLM が約 8-30% 優位**（engine compile 後）
- 100並列で vLLM が **4,741 tok/s** で逆転
- SGLang は RadixAttention により共有プレフィックス時 vLLM より **+29%**
- TGI は HuggingFace 公式が maintenance mode を宣言、vLLM/SGLang を推奨

### vLLM V1 (2025-) の主要改良

- **Async scheduling**: スケジューリングと GPU 実行を pipeline 化し zero-bubble overlap、スループット最大 1.7x
- **EngineCore 分離**: tokenize/detokenize を別プロセスへ。小モデル (5ms 推論) で CPU overhead を隠蔽
- **Speculative decoding**: n-gram, EAGLE, Medusa の3方式。rejection samplingで分布等価性を保証
- **Disaggregated P/D**: prefill (compute-bound) と decode (memory-bandwidth-bound) を別インスタンスへ。中間KVを共有 KV cache service 経由で転送
- **Prefix caching デフォルト ON**: ヒット率0%でもoverheadがほぼ無い実装に

### 競合との階層別棲み分け

| ライブラリ | 設計思想 | 強み |
|---|---|---|
| **TGI** (HF) | Rust router + Python worker | エコシステム統合（maintenance mode 2025） |
| **TensorRT-LLM** | NVIDIA 専用 AOT engine | 低並列で最速、kernel fusion 徹底（GPU lock-in） |
| **SGLang** | RadixAttention（基数木 prefix 共有） | プログラム的プロンプト・共有 prefix 時 vLLM 超え |
| **llm-d** | Kubernetes-native, vLLM を pod として束ねる | KV cache aware routing、TTFT 3x 改善、scale-to-zero |

vLLM の差別化は **OS 風汎用ページング + プラガブル attention backend + 広いHW対応**。SGLangは「アプリ層プレフィックス共有」、TensorRT-LLMは「コンパイラ最適化」、llm-dは「クラスタ層ルーティング」と各々別の階層を最適化しており、実運用ではこれらをスタックすることが現代的アーキテクチャになりつつある。

## 気づき・洞察

PagedAttentionの本質は「**メモリ管理の連続性仮定をハードウェアアーキテクチャ層から切り離した**」こと。これはOSがプロセスごとに連続な仮想アドレス空間を見せながら物理ページを断片化させて自由に管理する話と同型である。GPU上のテンソル演算は「連続メモリ前提の並列カーネル」が支配的だったが、attention のような **間接参照可能な計算** ではこの仮定を崩せると示した。同じ発想は今後 KV 以外（activation, gradient, optimizer state）にも展開されうる。

V1で導入された **disaggregated prefill/decode** は、計算性質が真逆（prefill: compute-bound, decode: memory-BW-bound）の処理を別ハードウェアに分離するという設計で、CPU の P-core/E-core 異種コアアーキテクチャとも通底する。「同じプロセッサでやらず、得意なものに分ける」という古典的設計原理がLLM推論に降りてきた格好である。

## 他分野との接続

- **CS**: 仮想メモリのページング、Bloom filter的なハッシュ照合、Merkle木によるコンテンツアドレス指定。OS基礎が直接応用された珍しい事例。
- **CRDT/分散システム**: prefix caching のハッシュチェーンは、過去エントリの「Merkle DAGによる内容アドレス指定」（Apache Iceberg, Git）と同じ設計パターン。
- **Lamport論理時計**: シーケンスIDによる順序づけと、disaggregated構成での KV transfer プロトコルの一貫性管理に通ずる。
- **piano/golf のメンタルプラクティス**: 「同じ前提を毎回最初から構築するのではなく、共有可能な部分を再利用する」という発想は、運動学習でのメンタルリハーサルにおける「動作プリフィックス」の再利用と類比的。

## 次に深掘りしたいこと

- vLLM の attention backend (FlashAttention v3, FlashInfer, xFormers) の選択ロジックとblock_sizeの相互作用
- Speculative decoding の rejection sampling 数学的基礎と分布等価性の証明
- llm-d / Dynamo の KV cache offloading（GPU→CPU→NVMe階層）の実装
- TensorRT-LLM engine の AOT compile が破壊するワークロードの種類

## 参考ソース
- Kwon et al., "Efficient Memory Management for LLM Serving with PagedAttention", SOSP 2023 (arXiv:2309.06180): https://arxiv.org/abs/2309.06180
- vLLM Blog (2023): https://blog.vllm.ai/2023/06/20/vllm.html
- vLLM Docs - Paged Attention design: https://docs.vllm.ai/en/latest/design/paged_attention/
- vLLM Docs - Automatic Prefix Caching: https://docs.vllm.ai/en/stable/design/prefix_caching/
- vLLM Blog - Anatomy of a High-Throughput LLM Inference System (2025): https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html
- Red Hat Developer - vLLM V1 Alpha (2025): https://developers.redhat.com/articles/2025/01/28/vllm-v1-a-major-upgrade-vllms-core-architecture
- llm-d Blog: https://llm-d.ai/blog/kvcache-wins-you-can-see
- Clarifai - SGLang vs vLLM vs TensorRT-LLM: https://www.clarifai.com/blog/comparing-sglang-vllm-and-tensorrt-llm-with-gpt-oss-120b
