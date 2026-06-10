import json

from f.paiperless.shared.ollama_client import chat_json, truncate_text
from f.paiperless.shared.prompts import TITLE, TAGS, CORRESPONDENT


def main(
    doc_id: int,
    text: str,
    analysis: dict,
    existing_tags: list,
    existing_correspondents: list,
    added_date: str = "",
) -> dict:
    excerpt = truncate_text(text, max_chars=10000)
    context = json.dumps(analysis, ensure_ascii=False)

    title_result = chat_json(
        TITLE,
        f"Analyse:\n{context}\n\nDokument:\n{excerpt}",
    )
    title = (title_result.get("title") or "").strip()[:60]
    document_date = title_result.get("document_date") or added_date or None

    tag_names = [t["name"] for t in existing_tags]
    tags_result = chat_json(
        TAGS,
        f"Vorhandene Tags: {json.dumps(tag_names, ensure_ascii=False)}\n\n"
        f"Analyse:\n{context}\n\nDokument:\n{excerpt}",
    )
    selected_tags = tags_result.get("selected_tags") or []
    new_tags = tags_result.get("new_tags") or []
    tag_warnings = tags_result.get("warnings") or []

    corr_names = [c["name"] for c in existing_correspondents]
    corr_result = chat_json(
        CORRESPONDENT,
        f"Vorhandene Korrespondenten: {json.dumps(corr_names, ensure_ascii=False)}\n\n"
        f"Analyse:\n{context}\n\nDokument:\n{excerpt}",
    )
    selected_correspondent = corr_result.get("selected_correspondent")
    new_correspondent = corr_result.get("new_correspondent")
    corr_warnings = corr_result.get("warnings") or []

    warnings = [*tag_warnings, *corr_warnings]
    if new_tags and not any("Tag" in w for w in warnings):
        warnings.append(f"Neue Tags vorgeschlagen: {', '.join(new_tags)}")
    if new_correspondent and not any("Korrespondent" in w for w in warnings):
        warnings.append(f"Neuer Korrespondent vorgeschlagen: {new_correspondent}")

    return {
        "doc_id": doc_id,
        "title": title,
        "document_date": document_date,
        "selected_tags": selected_tags,
        "new_tags": new_tags,
        "selected_correspondent": selected_correspondent,
        "new_correspondent": new_correspondent,
        "warnings": warnings,
        "analysis": analysis,
    }
