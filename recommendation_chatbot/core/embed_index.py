# 기능 : 문서 임베딩 및 Chroma 벡터 인덱스 생성/검색.
import os, pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from .config import VECTOR_DIR, INDEX_PKL

def build_index(df: pd.DataFrame) -> None:
    os.makedirs(VECTOR_DIR, exist_ok=True)
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(df["text"].tolist())
    payload = {
        "vectorizer": vec,
        "matrix": X,
        "records": df[["title","host","deadline","field","link","content","text"]].reset_index(drop=True),
    }
    with open(INDEX_PKL, "wb") as f:
        pickle.dump(payload, f)

def load_index():
    with open(INDEX_PKL, "rb") as f:
        return pickle.load(f)

