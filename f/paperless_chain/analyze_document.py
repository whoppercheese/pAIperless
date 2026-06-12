from f.paperless_chain.shared.ollama_client import chat_json
from f.paperless_chain.shared.prompts import (
    ANALYZE_SCHEMA,
    build_analyze_prompt,
    build_analyze_user_prompt,
)
from f.paperless_chain.shared.text_utils import (
    content_tag_names,
    is_system_tag,
    language_name,
    limit_words,
    normalize_language,
)


def _resolve_existing_name(name: str | None, name_to_canonical: dict[str, str]) -> str | None:
    if not name:
        return None
    return name_to_canonical.get(name.lower())


def main(
    doc_id: int,
    summary: str,
    existing_document_types: list,
    existing_tags: list,
    existing_correspondents: list,
    added_date: str = "",
    current_tag_names: list | None = None,
    current_correspondent_id: int | None = None,
    current_document_type_id: int | None = None,
    document_language: str = "de",
) -> dict:
    lang_code = normalize_language(document_language)
    lang_label = language_name(lang_code)
    type_name_to_canonical = {d["name"].lower(): d["name"] for d in existing_document_types}
    type_id_to_name = {d["id"]: d["name"] for d in existing_document_types}
    tag_name_to_canonical = {t["name"].lower(): t["name"] for t in existing_tags}
    corr_name_to_canonical = {c["name"].lower(): c["name"] for c in existing_correspondents}
    corr_id_to_name = {c["id"]: c["name"] for c in existing_correspondents}

    type_names = list(type_name_to_canonical.values())
    tag_names = [
        name for name in tag_name_to_canonical.values() if not is_system_tag(name)
    ]
    corr_names = list(corr_name_to_canonical.values())

    current_tags = content_tag_names(current_tag_names)

    result = chat_json(
        build_analyze_prompt(lang_label),
        build_analyze_user_prompt(
            doc_id,
            summary,
            type_names,
            tag_names,
            corr_names,
            current_tags=current_tags,
        ),
        format_schema=ANALYZE_SCHEMA,
    )

    title = limit_words((result.get("title") or "").strip())

    raw_tags = list(result.get("selected_tags") or [])
    selected_tags: list[str] = []
    for name in raw_tags:
        if is_system_tag(name):
            continue
        canonical = _resolve_existing_name(name, tag_name_to_canonical)
        if canonical and canonical not in selected_tags:
            selected_tags.append(canonical)

    raw_document_type = result.get("selected_document_type")
    selected_document_type = _resolve_existing_name(raw_document_type, type_name_to_canonical)
    if not selected_document_type and current_document_type_id:
        selected_document_type = type_id_to_name.get(current_document_type_id)

    raw_correspondent = result.get("selected_correspondent")
    selected_correspondent = _resolve_existing_name(raw_correspondent, corr_name_to_canonical)
    if not selected_correspondent and current_correspondent_id:
        selected_correspondent = corr_id_to_name.get(current_correspondent_id)

    return {
        "doc_id": doc_id,
        "title": title,
        "selected_tags": selected_tags,
        "selected_correspondent": selected_correspondent,
        "selected_document_type": selected_document_type,
    }
