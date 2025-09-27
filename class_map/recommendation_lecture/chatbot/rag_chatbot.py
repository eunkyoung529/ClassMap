import argparse
import json
import os
from dotenv import load_dotenv
from retriever.data_loader import load_chunks, build_parent_map
from retriever.bm25 import build_bm25_index
from retriever.dense import STEmbeddingFunction, get_or_create_collection
from retriever.hybrid import hybrid_search
from chatbot.gpt_client import create_azure_client
from chatbot.generator import generate_answer

import chromadb
from sentence_transformers import CrossEncoder

def get_or_create_chroma(persist_dir):
    return chromadb.PersistentClient(path=persist_dir)


def build_dense_index(chunks, persist_dir, model_name):
    client = get_or_create_chroma(persist_dir)
    ef = STEmbeddingFunction(model_name=model_name)
    col = get_or_create_collection(client, "syllabus_chunks", embedding_function=ef)

    if col.count() == 0:
        ids, docs, metadatas = [], [], []
        from retriever.hybrid import extract_metadata
        for idx, c in enumerate(chunks):
            cid = c.get("chunk_id", str(idx))
            ids.append(cid)
            text = c.get("text", "")
            if c.get("chunk_type") == "parent":
                week_plan = "\n".join(c.get("weekly_plan", [])) if isinstance(c.get("weekly_plan"), list) else ""
                text += "\n[주차별 계획 요약]\n" + week_plan
            docs.append(text)
            metadatas.append(extract_metadata(c))
        col.add(ids=ids, documents=docs, metadatas=metadatas)
        print(f"[Chroma] Added {len(ids)} chunks.")
        print(f"[Chroma] Persisted to {persist_dir}")
    else:
        print(f"[Chroma] Collection already has {col.count()} chunks.")
    return col


def main():
    load_dotenv()

    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default="./syllabus_chunks.jsonl", help="Path to syllabus_chunks.jsonl")
    ap.add_argument("--persist", default="./chroma_db", help="Chroma persist directory")
    ap.add_argument("--embed_model", default="BAAI/bge-m3")
    ap.add_argument("--query", default=None, help="Query text")
    ap.add_argument("--filters", default=None, help='JSON string for metadata filters')
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument("--chat", action="store_true", help="Use Azure GPT to generate final answer")
    ap.add_argument("--rerank_model", default="Dongjin-kr/ko-reranker", help="CrossEncoder model for reranking")
    args = ap.parse_args()

 
    chunks = load_chunks(args.chunks)
    parent_by_id, _ = build_parent_map(chunks)


    col = build_dense_index(chunks, args.persist, args.embed_model)
    bm25, tokenized = build_bm25_index(chunks)

    cross_encoder = CrossEncoder(args.rerank_model)

    if args.query:
        filters = json.loads(args.filters) if args.filters else {}

        query_text = args.query
        auto_filters = {}
        for year in ["1학년", "2학년", "3학년", "4학년"]:
            if year in query_text:
                auto_filters["target"] = year

        if "전공" in query_text:
            auto_filters["course_type"] = "전공"
        elif "교양" in query_text:
            auto_filters["course_type"] = "교양"

        filters.update(auto_filters)

        hits = hybrid_search(
            chunks, col, bm25, tokenized,
            query=args.query,
            cross_encoder=cross_encoder,
            top_k=args.top_k,
            filters=filters,
            weights={"bm25": 0.3, "dense": 0.2, "rerank": 0.5},  
        )

        parent_hits = [h for h in hits if h.get("chunk_type") == "parent"]

        if args.chat:
            client = create_azure_client()
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
            answer = generate_answer(args.query, parent_hits, deployment, client)
            print("챗봇 답변:\n", answer)
        else:
            print(json.dumps(hits, ensure_ascii=False, indent=2))

    else:
        print("Indexes built. Use --query to search or --chat for chatbot.")


if __name__ == "__main__":
    main()
