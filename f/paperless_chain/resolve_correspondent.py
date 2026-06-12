from f.paperless_chain.shared.ollama_client import chat_json
from f.paperless_chain.shared.paperless_client import create_or_get_correspondent
from f.paperless_chain.shared.prompts import (
    CORRESPONDENT_SCHEMA,
    build_resolve_correspondent_prompt,
    build_resolve_correspondent_user_prompt,
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
    existing_correspondents: list,
    document_language: str = "de",
) -> dict:
    lang_code = normalize_language(document_language)
    lang_label = language_name(lang_code)
    corr_name_to_canonical = {c["name"].lower(): c["name"] for c in existing_correspondents}
    corr_names = list(corr_name_to_canonical.values())

    warnings: list[str] = []
    result = chat_json(
        build_resolve_correspondent_prompt(lang_label),
        build_resolve_correspondent_user_prompt(doc_id, summary, corr_names),
        format_schema=CORRESPONDENT_SCHEMA,
    )

    generated_corr = " ".join((result.get("correspondent") or "").split()).strip()
    if not generated_corr:
        warnings.append("LLM hat keinen Korrespondenten geliefert")
        return {
            "doc_id": doc_id,
            "selected_correspondent": None,
            "created_correspondent": None,
            "warnings": warnings,
        }

    existing_match = _resolve_existing_name(generated_corr, corr_name_to_canonical)
    if existing_match:
        return {
            "doc_id": doc_id,
            "selected_correspondent": existing_match,
            "created_correspondent": None,
            "warnings": warnings,
        }

    try:
        entity, was_created = create_or_get_correspondent(generated_corr)
        return {
            "doc_id": doc_id,
            "selected_correspondent": entity["name"],
            "created_correspondent": _entity_summary(entity, was_created),
            "warnings": warnings,
        }
    except Exception as exc:
        warnings.append(f"Korrespondent konnte nicht angelegt werden: {exc}")
        return {
            "doc_id": doc_id,
            "selected_correspondent": None,
            "created_correspondent": None,
            "warnings": warnings,
        }
