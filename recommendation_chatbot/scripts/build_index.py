from ..core.store import load_contests
from ..core.embed_index import build_index

def main():
    print("[build_index] loading contests ...")
    df = load_contests()
    print(f"[build_index] records: {len(df)}")
    print("[build_index] building index ...")
    build_index(df)
    print("[build_index] done.")

if __name__ == "__main__":
    main()
