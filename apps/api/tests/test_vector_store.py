import pytest
from app.knowledge.vector_store import LocalVectorStore

def test_bm25_and_rrf():
    store = LocalVectorStore()
    docs = [
        {"id": "doc1", "text": "微积分基本定理描述了微分与积分的关系。"},
        {"id": "doc2", "text": "矩阵特征多项式用来求解矩阵的特征值。"}
    ]
    store.build_bm25_index(docs)
    scores = store.score_bm25("特征多项式")
    assert "doc2" in scores
    assert scores["doc2"] > 0

def test_hybrid_search():
    store = LocalVectorStore()
    docs = [
        {"id": "doc1", "text": "微积分基本定理描述了微分与积分的关系。"},
        {"id": "doc2", "text": "矩阵特征多项式用来求解矩阵的特征值。"}
    ]
    store.build_bm25_index(docs)
    
    # 模拟 chunk 的向量
    # doc1 只有 1 个 chunk: doc1_chunk_0
    # doc2 只有 1 个 chunk: doc2_chunk_0
    store.add_embeddings({
        "doc1_chunk_0": [1.0, 0.0, 0.0],
        "doc2_chunk_0": [0.0, 1.0, 0.0]
    })
    
    # 语义倾向于 doc1 向量，而 query "特征多项式" 倾向于 doc2
    results = store.search_hybrid("特征多项式", query_vector=[0.9, 0.1, 0.0], k=60, top_n=2)
    assert len(results) > 0
    # 应当召回两个，并以合适顺序排列
    doc_ids = [res["doc_id"] for res in results]
    assert "doc1" in doc_ids
    assert "doc2" in doc_ids

    # 语义空时退化为纯关键字
    results_only_bm25 = store.search_hybrid("特征多项式", query_vector=None, k=60, top_n=2)
    assert results_only_bm25[0]["doc_id"] == "doc2"

