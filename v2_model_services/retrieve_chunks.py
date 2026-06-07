from v2_model_services.embeddding_faiss_index import embedder
import numpy as np

def retrieve(query, chunks, index):
    q_emb = embedder.encode([query])
    _, ids = index.search(np.array(q_emb), k=4)
    return "\n".join([chunks[i] for i in ids[0]])