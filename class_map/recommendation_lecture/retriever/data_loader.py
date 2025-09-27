import json
from typing import List, Dict, Any

def load_chunks(jsonl_path: str) -> List[Dict[str, Any]]:
    chunks = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks

def build_parent_map(chunks: List[Dict[str, Any]]):
    parent_by_id, parent_of = {}, {}
    for c in chunks:
        if c.get("chunk_type") == "parent":
            parent_by_id[c["chunk_id"]] = c
        elif c.get("parent_id"):
            parent_of[c["chunk_id"]] = c["parent_id"]
    return parent_by_id, parent_of
