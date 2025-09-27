from rank_bm25 import BM25Okapi
from konlpy.tag import Okt
tokenizer = Okt()

def build_bm25_index(chunks):
    corpus = [c.get("text", "") for c in chunks]
    tokenized = [tokenizer.morphs(doc) for doc in corpus]  
    bm25 = BM25Okapi(tokenized)
    return bm25, tokenized


def bm25_search(bm25, tokenized_corpus, query: str, top_k: int = 10):
    tokenized_query = tokenizer.morphs(query)
    scores = bm25.get_scores(tokenized_query)
    idx_scores = list(enumerate(scores))
    idx_scores.sort(key=lambda x: x[1], reverse=True)
    return idx_scores[:top_k]