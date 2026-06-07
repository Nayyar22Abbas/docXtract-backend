from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


embedder = SentenceTransformer("all-MiniLM-L6-v2")


def build_index(chunks):
    embeddings = embedder.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, embeddings

def retrieve(query, chunks, index):
    q_emb = embedder.encode([query])
    _, ids = index.search(np.array(q_emb), k=4)
    return "\n".join([chunks[i] for i in ids[0]])