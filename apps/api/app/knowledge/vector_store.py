import re
import math
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

def tokenize(text: str) -> list[str]:
    """
    纯 Python 中文分词辅助函数。对于中文字符提取单字和双字，对于英文字符按单词提取并转小写。
    """
    text = text.lower()
    tokens = []
    pattern = re.compile(r"[\u4e00-\u9fff]+|[a-z0-9]+")
    parts = pattern.findall(text)
    for part in parts:
        if re.match(r"^[\u4e00-\u9fff]+$", part):
            n = len(part)
            for i in range(n):
                tokens.append(part[i])
                if i < n - 1:
                    tokens.append(part[i:i+2])
        else:
            tokens.append(part)
    return tokens

class LocalVectorStore:
    def __init__(self, cache_path: str | Path | None = None):
        self.cache_path = Path(cache_path) if cache_path else None
        self.chunks = []            # list of dict: {id, doc_id, text, start, end}
        self.embeddings = {}        # dict: chunk_id -> list[float]
        self.bm25_index = {
            "df": {},
            "idf": {},
            "doc_lens": {},
            "avgdl": 0.0,
            "doc_tfs": {},
            "total_docs": 0
        }
        self.doc_id_to_metadata = {}

    def tokenize(self, text: str) -> list[str]:
        return tokenize(text)

    def _split_text(self, text: str, chunk_size: int = 256, overlap: int = 50) -> list[dict]:
        """
        滑动窗口分块逻辑。块大小默认 256，重叠度 50。
        """
        chunks = []
        if not text:
            return chunks
        
        step = chunk_size - overlap
        if step <= 0:
            step = chunk_size
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": min(end, len(text))
            })
            if end >= len(text):
                break
            start += step
        return chunks

    def build_bm25_index(self, docs: list[dict]):
        """
        根据传入的文档列表建立 BM25 索引。
        docs: list of dict, 每个 dict 包含 id 和 text。
        """
        self.chunks = []
        chunk_tfs = {}
        chunk_lens = {}
        total_len = 0
        df = {}
        
        for idx_doc, doc in enumerate(docs):
            doc_id = doc.get("id") or doc.get("doc_id") or f"doc_fallback_{idx_doc}"
            text = doc.get("text") or doc.get("content") or ""
            
            # 缓存全文，以便 context merge 时能还原连续文本
            self.doc_id_to_metadata[doc_id] = {"full_text": text}
            
            # 滑动窗口切分：块大小 256，重叠度 50
            chunks_data = self._split_text(text, chunk_size=256, overlap=50)
            for idx, chunk in enumerate(chunks_data):
                chunk_id = f"{doc_id}_chunk_{idx}"
                self.chunks.append({
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "text": chunk["text"],
                    "start": chunk["start"],
                    "end": chunk["end"]
                })
                
                tokens = self.tokenize(chunk["text"])
                chunk_lens[chunk_id] = len(tokens)
                total_len += len(tokens)
                
                # 计算词频
                tfs = {}
                for token in tokens:
                    tfs[token] = tfs.get(token, 0) + 1
                chunk_tfs[chunk_id] = tfs
                
                # 计算 DF (一个 token 在多少个 chunk 中出现)
                for token in tfs:
                    df[token] = df.get(token, 0) + 1
                    
        total_docs = len(self.chunks)
        avgdl = total_len / total_docs if total_docs > 0 else 0.0
        
        # 计算 IDF
        idf = {}
        for token, count in df.items():
            idf[token] = math.log((total_docs - count + 0.5) / (count + 0.5) + 1.0)
            
        self.bm25_index = {
            "df": df,
            "idf": idf,
            "doc_lens": chunk_lens,
            "avgdl": avgdl,
            "doc_tfs": chunk_tfs,
            "total_docs": total_docs
        }

    def score_bm25(self, query: str) -> dict[str, float]:
        """
        根据 BM25 索引对 query 进行打分，返回 {doc_id: max_chunk_score}。
        支持单元测试要求的返回格式。
        """
        query_tokens = self.tokenize(query)
        scores = {}
        k1 = 1.5
        b = 0.75
        
        for chunk in self.chunks:
            chunk_id = chunk["id"]
            doc_id = chunk["doc_id"]
            score = 0.0
            
            tfs = self.bm25_index["doc_tfs"].get(chunk_id, {})
            doc_len = self.bm25_index["doc_lens"].get(chunk_id, 0)
            avgdl = self.bm25_index["avgdl"]
            
            for token in query_tokens:
                if token in self.bm25_index["idf"]:
                    idf = self.bm25_index["idf"][token]
                    tf = tfs.get(token, 0)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / avgdl if avgdl > 0 else 1.0))
                    if denom > 0:
                        score += idf * (tf * (k1 + 1.0)) / denom
                        
            if score > 0:
                if doc_id not in scores or score > scores[doc_id]:
                    scores[doc_id] = score
        return scores

    def score_bm25_chunk(self, query: str) -> dict[str, float]:
        """
        对所有 chunk 打分，返回 {chunk_id: score}
        """
        query_tokens = self.tokenize(query)
        scores = {}
        k1 = 1.5
        b = 0.75
        
        for chunk in self.chunks:
            chunk_id = chunk["id"]
            score = 0.0
            tfs = self.bm25_index["doc_tfs"].get(chunk_id, {})
            doc_len = self.bm25_index["doc_lens"].get(chunk_id, 0)
            avgdl = self.bm25_index["avgdl"]
            
            for token in query_tokens:
                if token in self.bm25_index["idf"]:
                    idf = self.bm25_index["idf"][token]
                    tf = tfs.get(token, 0)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / avgdl if avgdl > 0 else 1.0))
                    if denom > 0:
                        score += idf * (tf * (k1 + 1.0)) / denom
            if score > 0:
                scores[chunk_id] = score
        return scores

    def add_embeddings(self, embeddings: dict[str, list[float]]):
        """
        添加 chunks 对应的 embedding， embeddings: {chunk_id: embedding}
        """
        self.embeddings.update(embeddings)
        
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def score_semantic_chunk(self, query_vector: list[float]) -> dict[str, float]:
        """
        计算查询向量与所有 chunk 向量的余弦相似度，返回 {chunk_id: score}
        """
        scores = {}
        if not query_vector:
            return scores
        for chunk_id, emb in self.embeddings.items():
            sim = self._cosine_similarity(query_vector, emb)
            if sim > 0:
                scores[chunk_id] = sim
        return scores

    def search_hybrid(self, query: str, query_vector: list[float] | None = None, k: int = 60, top_n: int = 5) -> list[dict]:
        """
        混合检索：使用 RRF 合并语义检索和 BM25 检索。
        若 query_vector 为 None 或 []，则退化为纯关键字（BM25）检索。
        """
        bm25_scores = self.score_bm25_chunk(query)
        # 对 bm25 结果进行排序并确定 rank 排名 (1-based)
        sorted_bm25 = sorted(bm25_scores.items(), key=lambda x: (x[1], x[0]), reverse=True)
        bm25_ranks = {chunk_id: idx + 1 for idx, (chunk_id, _) in enumerate(sorted_bm25)}
        
        semantic_ranks = {}
        if query_vector:
            semantic_scores = self.score_semantic_chunk(query_vector)
            sorted_semantic = sorted(semantic_scores.items(), key=lambda x: (x[1], x[0]), reverse=True)
            semantic_ranks = {chunk_id: idx + 1 for idx, (chunk_id, _) in enumerate(sorted_semantic)}
            
        # RRF 融合
        rrf_scores = {}
        # 找出所有候选 chunk_id
        all_chunk_ids = set(bm25_scores.keys()) | set(semantic_ranks.keys())
        
        for chunk_id in all_chunk_ids:
            score = 0.0
            if chunk_id in bm25_ranks:
                score += 1.0 / (k + bm25_ranks[chunk_id])
            if query_vector and chunk_id in semantic_ranks:
                score += 1.0 / (k + semantic_ranks[chunk_id])
            rrf_scores[chunk_id] = score
            
        # 按照 RRF 分数排序
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 组装返回结果
        results = []
        chunk_map = {chunk["id"]: chunk for chunk in self.chunks}
        for chunk_id, rrf_score in sorted_chunks:
            if chunk_id in chunk_map:
                chunk_info = chunk_map[chunk_id].copy()
                chunk_info["rrf_score"] = rrf_score
                results.append(chunk_info)
                
        # 对结果进行 Context Merge (如果可能，合并同一个 doc_id 的相邻切片)
        merged_results = self._merge_contexts(results)
        
        return merged_results[:top_n]

    def _merge_contexts(self, chunks: list[dict]) -> list[dict]:
        """
        对同个 concept 检索出的多个相邻切片块进行合并 (Context Merge)。
        """
        grouped = {}
        for idx, chunk in enumerate(chunks):
            doc_id = chunk["doc_id"]
            if doc_id not in grouped:
                grouped[doc_id] = []
            grouped[doc_id].append((idx, chunk))
            
        merged_by_doc = {}
        for doc_id, items in grouped.items():
            # 按原始拼合文本中的 start 索引排序
            items_sorted = sorted(items, key=lambda x: x[1]["start"])
            
            merged_list = []
            for original_rank_idx, chunk in items_sorted:
                if not merged_list:
                    merged_list.append({
                        "doc_id": doc_id,
                        "start": chunk["start"],
                        "end": chunk["end"],
                        "texts": [chunk["text"]],
                        "best_rrf_score": chunk["rrf_score"],
                        "best_rank_idx": original_rank_idx
                    })
                else:
                    last = merged_list[-1]
                    # 如果当前 chunk 的 start <= 上一个 chunk 的 end，则视为重叠或相邻
                    if chunk["start"] <= last["end"]:
                        last["start"] = min(last["start"], chunk["start"])
                        last["end"] = max(last["end"], chunk["end"])
                        last["best_rrf_score"] = max(last["best_rrf_score"], chunk["rrf_score"])
                        last["best_rank_idx"] = min(last["best_rank_idx"], original_rank_idx)
                        last["texts"].append(chunk["text"])
                    else:
                        merged_list.append({
                            "doc_id": doc_id,
                            "start": chunk["start"],
                            "end": chunk["end"],
                            "texts": [chunk["text"]],
                            "best_rrf_score": chunk["rrf_score"],
                            "best_rank_idx": original_rank_idx
                        })
            merged_by_doc[doc_id] = merged_list

        final_merged = []
        for doc_id, merged_intervals in merged_by_doc.items():
            full_text = self._get_doc_full_text(doc_id)
            for interval in merged_intervals:
                if full_text:
                    merged_text = full_text[interval["start"]:interval["end"]]
                else:
                    merged_text = " ... ".join(interval["texts"])
                
                final_merged.append({
                    "doc_id": doc_id,
                    "text": merged_text,
                    "start": interval["start"],
                    "end": interval["end"],
                    "rrf_score": interval["best_rrf_score"],
                    "best_rank_idx": interval["best_rank_idx"]
                })
                
        # 按照最初在召回列表中召回的先后顺序（最佳 rank 索引）升序排序
        final_merged = sorted(final_merged, key=lambda x: x["best_rank_idx"])
        return final_merged

    def _get_doc_full_text(self, doc_id: str) -> str:
        if doc_id in self.doc_id_to_metadata:
            return self.doc_id_to_metadata[doc_id].get("full_text", "")
        return ""

    def save(self):
        """
        序列化并存入 cache_path
        """
        if not self.cache_path:
            return
        data = {
            "chunks": self.chunks,
            "embeddings": self.embeddings,
            "bm25_index": self.bm25_index,
            "doc_id_to_metadata": self.doc_id_to_metadata
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self) -> bool:
        """
        从 cache_path 反序列化
        """
        if not self.cache_path or not self.cache_path.exists():
            return False
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self.chunks = data.get("chunks", [])
            self.embeddings = data.get("embeddings", {})
            self.bm25_index = data.get("bm25_index", {})
            self.doc_id_to_metadata = data.get("doc_id_to_metadata", {})
            return True
        except Exception:
            return False
