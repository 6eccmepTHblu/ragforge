# A Short Overview of AI, ML and Retrieval-Augmented Generation

## Machine learning basics

Machine learning is a branch of artificial intelligence where models learn
patterns from data instead of being explicitly programmed. Supervised learning
uses labelled examples, unsupervised learning finds structure in unlabelled
data, and reinforcement learning optimises behaviour through rewards.

## Embeddings and semantic search

An embedding maps a piece of text into a dense vector such that semantically
similar texts land close together in the vector space. Semantic search encodes
a query into the same space and returns the nearest document vectors, typically
measured by cosine similarity. Vector databases such as Qdrant, Chroma, Milvus,
Pinecone and pgvector store these vectors and support fast approximate nearest
neighbour search at scale.

## Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation, or RAG, combines a retriever with a large
language model. Rather than relying only on the parameters baked into the
model, RAG first retrieves relevant chunks from an external knowledge base and
then conditions the language model on that retrieved context. This reduces
hallucinations, keeps answers grounded in source documents, and makes it easy
to update knowledge without retraining the model.

A typical RAG pipeline has four stages: ingestion (parse and chunk documents,
compute embeddings, store them), retrieval (embed the query and fetch the most
relevant chunks), augmentation (assemble the retrieved context into a prompt),
and generation (the language model produces a cited, grounded answer).

## Hybrid retrieval

Dense vector search captures meaning but can miss exact keywords such as product
codes or rare names. Sparse lexical methods like BM25 handle exact matches well
but ignore semantics. Hybrid retrieval fuses both rankings — often with
Reciprocal Rank Fusion — to get the best of both worlds.

## Evaluating RAG systems

Good RAG systems are measured, not guessed. Retrieval quality is evaluated with
metrics like hit rate and mean reciprocal rank against a labelled set. Answer
quality is often assessed with an LLM-as-judge that scores faithfulness (is the
answer supported by the retrieved context?) and answer relevancy (does it
address the question?).
