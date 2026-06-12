from f.paperless_chain.shared.ollama_client import chat_json
from f.paperless_chain.shared.paperless_client import create_or_get_document_type
from f.paperless_chain.shared.prompts import (
    DOCUMENT_TYPE_SCHEMA,
    build_resolve_document_type_prompt,
    build_resolve_document_type_user_prompt,
)
from f.paperless_chain.shared.text_utils import language_name, normalize_language


def _entity_summary(entity: dict, created: bool) -> dict:
    return {"id": entity["id"], "name": entity["name"], "created": created}


def _resolve_existing_name(name: str | None, name_to_canonical: dict[str, str]) -> str | None:
    if not name:
        return None
    return name_to_canonical.get(name.lower())


def main(
    doc_id: int,
    summary: str,
    existing_document_types: list,
    document_language: str = "de",
) -> dict:
    lang_code = normalize_language(document_language)
    lang_label = language_name(lang_code)
    type_name_to_canonical = {d["name"].lower(): d["name"] for d in existing_document_types}
    type_names = list(type_name_to_canonical.values())

    warnings: list[str] = []
    result = chat_json(
        build_resolve_document_type_prompt(lang_label),
        build_resolve_document_type_user_prompt(doc_id, summary, type_names),
        format_schema=DOCUMENT_TYPE_SCHEMA,
    )

    generated_type = " ".join((result.get("document_type") or "").split()).strip()
    if not generated_type:
        warnings.append("LLM hat keinen Dokumenttyp geliefert")
        return {
            "doc_id": doc_id,
            "selected_document_type": None,
            "created_document_type": None,
            "warnings": warnings,
        }

    existing_match = _resolve_existing_name(generated_type, type_name_to_canonical)
    if existing_match:
        return {
            "doc_id": doc_id,
            "selected_document_type": existing_match,
            "created_document_type": None,
            "warnings": warnings,
        }

    try:
        entity, was_created = create_or_get_document_type(generated_type)
        return {
            "doc_id": doc_id,
            "selected_document_type": entity["name"],
            "created_document_type": _entity_summary(entity, was_created),
            "warnings": warnings,
        }
    except Exception as exc:
        warnings.append(f"Dokumenttyp konnte nicht angelegt werden: {exc}")
        return {
            "doc_id": doc_id,
            "selected_document_type": None,
            "created_document_type": None,
            "warnings": warnings,
        }
