import json

from f.paiperless.shared.ollama_client import chat_json, truncate_text
from f.paiperless.shared.prompts import CLASSIFY


def main(doc_id: int, text: str, existing_document_types: list) -> dict:
    type_names = [d["name"] for d in existing_document_types]
    user = (
        f"Vorhandene Dokumenttypen: {json.dumps(type_names, ensure_ascii=False)}\n\n"
        f"Dokument-ID: {doc_id}\n\nText:\n{truncate_text(text)}"
    )
    analysis = chat_json(CLASSIFY, user)

    return {
        "doc_id": doc_id,
        "doc_nature": analysis.get("doc_nature", "Unbekanntes Dokument"),
        "selected_document_type": analysis.get("selected_document_type"),
        "new_document_type": analysis.get("new_document_type"),
        "document_type_warnings": analysis.get("document_type_warnings", []),
        "key_sections": analysis.get("key_sections", []),
        "high_importance_signals": analysis.get("high_importance_signals", []),
        "low_importance_signals": analysis.get("low_importance_signals", []),
        "has_tables": bool(analysis.get("has_tables", False)),
        "language": analysis.get("language", "de"),
    }
