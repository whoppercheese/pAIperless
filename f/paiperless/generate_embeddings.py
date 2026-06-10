from f.paiperless.shared.ollama_client import embed_texts


def main(chunks: list) -> dict:
    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        return {"doc_id": None, "embedded_chunks": [], "count": 0}

    vectors = embed_texts(texts)

    embedded = []
    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        embedded.append({
            "vector": vector,
            "payload": {
                "doc_id": chunk["doc_id"],
                "chunk_index": index,
                "chunk_type": chunk["chunk_type"],
                "chunk_level": chunk["chunk_level"],
                "correspondent": chunk.get("correspondent"),
                "tags": chunk.get("tags", []),
                "text": chunk["text"],
                "importance": chunk["importance"],
                "importance_reason": chunk["importance_reason"],
                "doc_nature": chunk.get("doc_nature"),
            },
        })

    return {
        "doc_id": chunks[0]["doc_id"] if chunks else None,
        "embedded_chunks": embedded,
        "count": len(embedded),
    }
