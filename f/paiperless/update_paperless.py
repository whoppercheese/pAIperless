from f.paiperless.shared.paperless_client import post, patch


def main(
    doc_id: int,
    title: str,
    selected_tags: list,
    new_tags: list,
    selected_correspondent: str | None,
    new_correspondent: str | None,
    existing_tags: list,
    existing_correspondents: list,
    existing_document_types: list,
    selected_document_type: str | None = None,
    new_document_type: str | None = None,
    document_date: str | None = None,
    document_type_warnings: list | None = None,
    warnings: list | None = None,
    analysis: dict | None = None,
) -> dict:
    tag_name_to_id = {t["name"].lower(): t["id"] for t in existing_tags}
    corr_name_to_id = {c["name"].lower(): c["id"] for c in existing_correspondents}
    dtype_name_to_id = {d["name"].lower(): d["id"] for d in existing_document_types}
    collected_warnings = list(warnings or []) + list(document_type_warnings or [])

    tag_ids: list[int] = []
    for name in selected_tags:
        key = name.lower()
        if key in tag_name_to_id:
            tag_ids.append(tag_name_to_id[key])

    for name in new_tags:
        key = name.lower()
        if key in tag_name_to_id:
            tag_ids.append(tag_name_to_id[key])
            continue
        created = post("/api/tags/", {"name": name, "matching_algorithm": 0})
        tag_name_to_id[key] = created["id"]
        tag_ids.append(created["id"])
        collected_warnings.append(f"Neuer Tag in Paperless angelegt: {name}")

    correspondent_id = None
    correspondent_name = selected_correspondent or new_correspondent
    if correspondent_name:
        key = correspondent_name.lower()
        if key in corr_name_to_id:
            correspondent_id = corr_name_to_id[key]
        else:
            created = post("/api/correspondents/", {"name": correspondent_name, "matching_algorithm": 0})
            correspondent_id = created["id"]
            if new_correspondent:
                collected_warnings.append(f"Neuer Korrespondent in Paperless angelegt: {correspondent_name}")

    document_type_id = None
    document_type_name = selected_document_type or new_document_type
    if document_type_name:
        key = document_type_name.lower()
        if key in dtype_name_to_id:
            document_type_id = dtype_name_to_id[key]
        else:
            created = post("/api/document_types/", {"name": document_type_name, "matching_algorithm": 0})
            document_type_id = created["id"]
            collected_warnings.append(f"Neuer Dokumenttyp in Paperless angelegt: {document_type_name}")

    update_payload: dict = {"title": title, "tags": list(dict.fromkeys(tag_ids))}
    if correspondent_id is not None:
        update_payload["correspondent"] = correspondent_id
    if document_type_id is not None:
        update_payload["document_type"] = document_type_id
    if document_date:
        update_payload["created_date"] = document_date

    updated = patch(f"/api/documents/{doc_id}/", update_payload)

    return {
        "doc_id": doc_id,
        "title": title,
        "tag_names": selected_tags + new_tags,
        "correspondent_name": correspondent_name,
        "document_type_name": document_type_name,
        "warnings": collected_warnings,
        "analysis": analysis or {},
        "paperless_document": updated,
    }
