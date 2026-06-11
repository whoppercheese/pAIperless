from f.paiperless.shared.paperless_client import patch
from f.paiperless.shared.text_utils import limit_words


def main(
    doc_id: int,
    title: str,
    selected_tags: list,
    selected_correspondent: str | None,
    existing_tags: list,
    existing_correspondents: list,
    existing_document_types: list,
    current_tag_ids: list | None = None,
    selected_document_type: str | None = None,
    document_date: str | None = None,
    warnings: list | None = None,
) -> dict:
    tag_name_to_id = {t["name"].lower(): t["id"] for t in existing_tags}
    corr_name_to_id = {c["name"].lower(): c["id"] for c in existing_correspondents}
    dtype_name_to_id = {d["name"].lower(): d["id"] for d in existing_document_types}
    collected_warnings = list(warnings or [])

    tag_ids: list[int] = list(current_tag_ids or [])
    known_tag_ids = set(tag_ids)
    applied_tag_names: list[str] = []
    for name in selected_tags:
        key = name.lower()
        if key in tag_name_to_id:
            tag_id = tag_name_to_id[key]
            applied_tag_names.append(name)
            if tag_id not in known_tag_ids:
                tag_ids.append(tag_id)
                known_tag_ids.add(tag_id)

    correspondent_id = None
    correspondent_name = selected_correspondent
    if correspondent_name:
        key = correspondent_name.lower()
        if key in corr_name_to_id:
            correspondent_id = corr_name_to_id[key]
        else:
            correspondent_name = None

    document_type_id = None
    document_type_name = selected_document_type
    if document_type_name:
        key = document_type_name.lower()
        if key in dtype_name_to_id:
            document_type_id = dtype_name_to_id[key]
        else:
            document_type_name = None

    update_payload: dict = {}
    cleaned_title = limit_words(title.strip())
    if cleaned_title:
        update_payload["title"] = cleaned_title
    if tag_ids:
        update_payload["tags"] = list(dict.fromkeys(tag_ids))
    if correspondent_id is not None:
        update_payload["correspondent"] = correspondent_id
    if document_type_id is not None:
        update_payload["document_type"] = document_type_id
    if document_date:
        update_payload["created_date"] = document_date

    if not update_payload:
        collected_warnings.append("Keine Metadaten-Änderungen, Paperless-Update übersprungen")
        print("=== pAIperless Paperless Update (skipped) ===")
        print(f"doc_id: {doc_id}")
        print("reason: Keine Metadaten-Änderungen")
        return {
            "doc_id": doc_id,
            "title": cleaned_title,
            "tag_names": applied_tag_names,
            "correspondent_name": correspondent_name,
            "document_type_name": document_type_name,
            "warnings": collected_warnings,
            "paperless_document": None,
            "skipped": True,
        }

    updated = patch(f"/api/documents/{doc_id}/", update_payload)

    return {
        "doc_id": doc_id,
        "title": title,
        "tag_names": applied_tag_names,
        "correspondent_name": correspondent_name,
        "document_type_name": document_type_name,
        "warnings": collected_warnings,
        "paperless_document": updated,
    }
