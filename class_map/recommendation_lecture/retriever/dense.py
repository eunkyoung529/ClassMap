import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class STEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        logging.info(f"입력 텍스트 {len(input)}개 임베딩 생성 시작")
        embeddings = self.model.encode(input, show_progress_bar=False, convert_to_numpy=True)
        logging.info(f"임베딩 {len(embeddings)}개 생성 완료")
        return embeddings.tolist()

def get_or_create_chroma(persist_dir: str = "./db_store"):
    logging.info(f"ChromaDB PersistentClient 생성 (저장 경로: {persist_dir})")
    return chromadb.PersistentClient(path=persist_dir)

def get_or_create_collection(client, name: str, embedding_function):
    try:
        col = client.get_collection(name=name, embedding_function=embedding_function)
    except Exception:
        col = client.create_collection(name=name, embedding_function=embedding_function)
    return col

