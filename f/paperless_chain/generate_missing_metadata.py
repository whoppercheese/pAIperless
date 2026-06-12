from f.paperless_chain.shared.ollama_client import chat_json
from f.paperless_chain.shared.paperless_client import (
    create_or_get_correspondent,
    create_or_get_document_type,
)
from f.paperless_chain.shared.prompts import (
    build_generate_missing_prompt,
    build_generate_missing_schema,
    build_generate_missing_user_prompt,
)
from f.paperless_chain.shared.text_utils import language_name, normalize_language


def _entity_summary(entity: dict, created: bool) -> dict:
    return {"id": entity["id"], "name": entity["name"], "created": created}


def main(
    doc_id: int,
    summary: str,
    need_document_type: bool,
    need_correspondent: bool,
    document_language: str = "de",
) -> dict:
    lang_code = normalize_language(document_language)
    lang_label = language_name(lang_code)

    selected_document_type = None
    selected_correspondent = None
    created_document_type = None
    created_correspondent = None
    warnings: list[str] = []

    generated = chat_json(
        build_generate_missing_prompt(lang_label, need_document_type, need_correspondent),
        build_generate_missing_user_prompt(doc_id, summary),
        format_schema=build_generate_missing_schema(need_document_type, need_correspondent),
    )

    if need_document_type:
        generated_type = " ".join((generated.get("document_type") or "").split()).strip()
        if generated_type:
            try:
                entity, was_created = create_or_get_document_type(generated_type)
                selected_document_type = entity["name"]
                created_document_type = _entity_summary(entity, was_created)
            except Exception as exc:
                warnings.append(f"Dokumenttyp konnte nicht angelegt werden: {exc}")
        else:
            warnings.append("LLM hat keinen Dokumenttyp für Anlage geliefert")

    if need_correspondent:
        generated_corr = " ".join((generated.get("correspondent") or "").split()).strip()
        if generated_corr:
            try:
                entity, was_created = create_or_get_correspondent(generated_corr)
                selected_correspondent = entity["name"]
                created_correspondent = _entity_summary(entity, was_created)
            except Exception as exc:
                warnings.append(f"Korrespondent konnte nicht angelegt werden: {exc}")
        else:
            warnings.append("LLM hat keinen Korrespondenten für Anlage geliefert")

    return {
        "doc_id": doc_id,
        "selected_document_type": selected_document_type,
        "selected_correspondent": selected_correspondent,
        "created_document_type": created_document_type,
        "created_correspondent": created_correspondent,
        "warnings": warnings,
    }
