from f.paiperless.shared.paperless_client import get, paginate


def main(doc_id: int) -> dict:
    document = get(f"/api/documents/{doc_id}/")
    text = document.get("content") or ""
    tags = paginate("/api/tags/")
    correspondents = paginate("/api/correspondents/")
    document_types = paginate("/api/document_types/")

    return {
        "doc_id": doc_id,
        "text": text,
        "existing_tags": [{"id": t["id"], "name": t["name"]} for t in tags],
        "existing_correspondents": [{"id": c["id"], "name": c["name"]} for c in correspondents],
        "existing_document_types": [{"id": d["id"], "name": d["name"]} for d in document_types],
        "added_date": (document.get("added") or "")[:10],
        "current_metadata": {
            "title": document.get("title"),
            "correspondent": document.get("correspondent"),
            "tag_ids": document.get("tags", []),
            "document_type": document.get("document_type"),
        },
    }
