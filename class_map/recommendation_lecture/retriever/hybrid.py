from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder

META_FIELDS = [
    "course_id", "course_code", "title", "chunk_type", "week",
    "department", "course_type", "schedule", "credits", "hours",
    "target", "instructor", "email", "language", "skills", "tags"
]

def extract_metadata(c: Dict[str, Any]) -> Dict[str, Any]:
    """Chunk에서 주요 메타데이터만 추출 (None 방지)"""
    meta = {}
    for k in META_FIELDS:
        if k in c:
            val = c.get(k)
            if val is None:
                val = ""   
            meta[k] = str(val)  
    return meta

def apply_filters(c: Dict[str, Any], flt: Dict[str, Any]) -> bool:
    """단순한 AND 필터링 (string equality)"""
    if not flt:
        return True
    for k, v in flt.items():
        if v is None:
            continue
        if str(v) not in str(c.get(k, "")):
            return False

    return True


def hybrid_search(
    chunks: List[Dict[str, Any]],
    collection,          
    bm25, tokenized_corpus,
    query: str,
    cross_encoder: CrossEncoder,    
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    batch_size: int = 32,
    weights: Dict[str, float] = None 
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval (Dense + BM25) → Candidate 생성 → CrossEncoder rerank
    BM25 + Dense + Rerank 가중합으로 최종 정렬
    """
    if weights is None:
        weights = {"bm25": 0.2, "dense": 0.3, "rerank": 0.5}

    # Dense 검색
    dense = collection.query(query_texts=[query], n_results=max(top_k*3, 20))
    dense_ids = dense["ids"][0]
    dense_scores = dense.get("distances", [[]])[0]
    dense_scores = [1 - d for d in dense_scores] if dense_scores else [0.0] * len(dense_ids)

    # BM25 검색
    from ..retriever.bm25 import bm25_search
    bm25_res = bm25_search(bm25, tokenized_corpus, query, top_k=max(top_k*3, 50))
    bm25_dict = {i: s for i, s in bm25_res}

 
    id_to_idx, idx_to_id = {}, {}
    for idx, c in enumerate(chunks):
        cid = c.get("chunk_id", str(idx))
        id_to_idx[cid] = idx
        idx_to_id[idx] = cid


    candidates = set()
    candidates.update([cid for cid in dense_ids if cid in id_to_idx])
    candidates.update([idx_to_id[i] for i, _ in bm25_res if i in idx_to_id])

    candidate_docs = []
    for cid in candidates:
        idx = id_to_idx.get(cid)
        if idx is None:
            continue
        c = chunks[idx]
        if not apply_filters(c, filters or {}):
            continue
        candidate_docs.append(c)


    candidate_docs = sorted(candidate_docs, key=lambda x: 0 if x.get("chunk_type")=="parent" else 1)


    pairs = [(query, c["text"]) for c in candidate_docs]
    rerank_scores = cross_encoder.predict(pairs, batch_size=batch_size, show_progress_bar=False)

    results = []
    for c, rerank_s in zip(candidate_docs, rerank_scores):
        cid = c.get("chunk_id")

        bm25_s = bm25_dict.get(id_to_idx.get(cid, -1), 0.0)
        dense_s = 0.0
        if cid in dense_ids:
            i = dense_ids.index(cid)
            dense_s = dense_scores[i]

        final_score = (
            weights["bm25"] * bm25_s +
            weights["dense"] * dense_s +
            weights["rerank"] * float(rerank_s)
        )

        c["_bm25_score"] = bm25_s
        c["_dense_score"] = dense_s
        c["_rerank_score"] = float(rerank_s)
        c["_final_score"] = final_score
        results.append(c)

    reranked = sorted(results, key=lambda x: x["_final_score"], reverse=True)
    return reranked[:top_k]
