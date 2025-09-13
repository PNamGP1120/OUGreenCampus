import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from OUGreenApp.models import News

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
index = None
texts = []

def build_index():
    global index, texts
    texts = []

    news_items = News.objects.filter(status="published").order_by("-created_at")
    for n in news_items:
        if n.content:
            texts.append(f"{n.title}\n{n.content}")

    if not texts:
        index = None   # quan trọng: set None nếu không có dữ liệu
        return None

    embeddings = model.encode(texts, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index


def search_news(query, top_k=3):
    global index, texts

    if index is None or not texts:
        build_index()

    if index is None or not texts:  # nếu vẫn chưa có dữ liệu
        return []

    q_emb = model.encode([query], convert_to_numpy=True)
    # FAISS sẽ trả về kết quả rỗng nếu index trống
    if index.ntotal == 0:
        return []

    D, I = index.search(q_emb, min(top_k, index.ntotal))
    return [texts[i] for i in I[0] if i < len(texts)]
