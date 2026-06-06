import re
import copy
import asyncio
from pathlib import Path
from app.config import get_settings
from app.knowledge.loader import load_knowledge
from app.knowledge.schema import KnowledgeHit, KnowledgeItem
from app.knowledge.vector_store import LocalVectorStore
from app.llm.openai_compatible import OpenAICompatibleClient

SUBJECT_HINTS = {
    "calculus": ["高数", "微积分", "导数", "积分", "极限", "洛必达", "函数"],
    "linear_algebra": ["线代", "矩阵", "行列式", "特征值", "特征向量", "线性方程组", "秩"],
    "probability": ["概率", "随机", "分布", "期望", "方差", "条件概率", "独立", "互斥"],
}


def detect_subject(query: str, explicit_subject: str | None = None) -> str | None:
    if explicit_subject and explicit_subject != "auto":
        return explicit_subject
    for subject, hints in SUBJECT_HINTS.items():
        if any(hint in query for hint in hints):
            return subject
    if "∫" in query or "\\int" in query or "lim" in query or "导数" in query:
        return "calculus"
    return None


def _tokens(query: str) -> list[str]:
    parts = re.findall(r"[\w\u4e00-\u9fff]+", query.lower())
    tokens = [part for part in parts if len(part) > 1]
    if "幂函数积分" in query or ("∫" in query and "x" in query):
        tokens.extend(["积分", "不定积分", "原函数", "幂函数"])
    if "条件概率" in query:
        tokens.extend(["条件概率", "乘法定理"])
    if "二阶行列式" in query:
        tokens.extend(["二阶行列式", "行列式"])
    return list(dict.fromkeys(tokens))


_vector_store = None
_vector_store_lock = asyncio.Lock()


def is_cache_valid(store: LocalVectorStore, current_items: tuple[KnowledgeItem, ...]) -> bool:
    """
    检查缓存的文档 ID 和文本内容是否与当前 load_knowledge() 完全一致。
    支持修改、删除和新增的检测。
    """
    if not hasattr(store, "doc_id_to_metadata") or not store.doc_id_to_metadata:
        return False

    # 检查 embeddings and chunks 是否为空，以及数量是否匹配
    if not store.chunks or not store.embeddings or len(store.embeddings) != len(store.chunks):
        return False
        
    current_docs = {}
    for item in current_items:
        current_docs[item.id] = _get_item_full_text(item)
        
    # 数量不匹配说明有新增或删除
    if len(current_docs) != len(store.doc_id_to_metadata):
        return False
        
    # 检查内容是否改变，或者是否有 ID 不匹配
    for doc_id, current_text in current_docs.items():
        if doc_id not in store.doc_id_to_metadata:
            return False
        cached_text = store.doc_id_to_metadata[doc_id].get("full_text", "")
        if cached_text != current_text:
            return False
            
    return True


async def get_vector_store(api_key: str | None = None) -> LocalVectorStore:
    global _vector_store
    if _vector_store is not None:
        return _vector_store
        
    async with _vector_store_lock:
        if _vector_store is not None:
            return _vector_store

        settings = get_settings()
        cache_path = settings.knowledge_root / "embeddings.json"
        
        store = LocalVectorStore(cache_path=cache_path)
        items = load_knowledge()
        
        # 校验缓存是否有效
        if store.load() and is_cache_valid(store, items):
            _vector_store = store
            return _vector_store
        
    docs = []
    for item in items:
        full_text = _get_item_full_text(item)
        docs.append({
            "id": item.id,
            "text": full_text
        })
        
    store.build_bm25_index(docs)
    
    # 使用 asyncio.gather 和 asyncio.Semaphore(5) 并发获取 embeddings
    client = OpenAICompatibleClient(settings)
    sem = asyncio.Semaphore(5)
    
    async def fetch_with_semaphore(chunk_text: str):
        async with sem:
            return await client.create_embedding(chunk_text, api_key=api_key)
            
    tasks = []
    chunk_ids = []
    for chunk in store.chunks:
        chunk_ids.append(chunk["id"])
        tasks.append(fetch_with_semaphore(chunk["text"]))
        
    results = await asyncio.gather(*tasks)
    
    chunk_embeddings = {}
    all_success = True
    for chunk_id, emb in zip(chunk_ids, results):
        if emb and len(emb) > 0:
            chunk_embeddings[chunk_id] = emb
        else:
            all_success = False
            
    store.add_embeddings(chunk_embeddings)
    
    # 只有当所有的 chunk 都成功生成了有效向量时才写盘
    if all_success and len(store.chunks) > 0:
        store.save()
        
    _vector_store = store
    return _vector_store



def _get_item_full_text(item: KnowledgeItem) -> str:
    parts = []
    if item.concept_zh:
        parts.append(f"概念：{item.concept_zh}")
    if item.prerequisite:
        parts.append(f"先修知识：{' '.join(item.prerequisite)}")
    if item.description:
        parts.append(f"描述：{item.description}")
    if item.intuitive_explanation:
        parts.append(f"直观解释：{item.intuitive_explanation}")
    if item.solution:
        parts.append(f"解题方法：{item.solution}")
    return "\n".join(parts)


async def search_knowledge(
    query: str, subject: str | None = None, limit: int = 5, api_key: str | None = None
) -> list[KnowledgeHit]:
    detected_subject = detect_subject(query, subject)
    
    store = await get_vector_store(api_key=api_key)
    
    settings = get_settings()
    client = OpenAICompatibleClient(settings)
    
    try:
        query_vector = await client.create_embedding(query)
        # 混合检索
        results = store.search_hybrid(query, query_vector=query_vector, top_n=limit * 2)
    except Exception as e:
        # Fallback if embedding fails
        results = store.search_hybrid(query, query_vector=[], top_n=limit * 2)
    
    items = {item.id: item for item in load_knowledge()}
    
    hits: list[KnowledgeHit] = []
    for res in results:
        doc_id = res["doc_id"]
        if doc_id not in items:
            continue
        orig_item = items[doc_id]
        
        item = copy.copy(orig_item)
        item.description = res["text"]
        item.intuitive_explanation = ""
        
        score = int(res["rrf_score"] * 100000)
        if detected_subject and item.subject == detected_subject:
            score += 20000
            
        hits.append(KnowledgeHit(item=item, score=score))
        
    hits.sort(key=lambda hit: (hit.score, hit.item.concept_zh), reverse=True)
    return hits[:limit]

