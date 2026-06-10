from f.paiperless.shared.notify_client import notify


def _format_message(
    title: str,
    tag_names: list,
    correspondent_name: str | None,
    document_type_name: str | None,
    warnings: list,
) -> str:
    lines = [
        "pAIperless: Dokument verarbeitet",
        f"Titel: {title}",
        f"Tags: {', '.join(tag_names) if tag_names else '–'}",
        f"Korrespondent: {correspondent_name or '–'}",
        f"Dokumenttyp: {document_type_name or '–'}",
    ]
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {w}" for w in warnings)
    return "\n".join(lines)


def main(
    doc_id: int,
    title: str,
    tag_names: list | None = None,
    correspondent_name: str | None = None,
    document_type_name: str | None = None,
    warnings: list | None = None,
) -> dict:
    message = _format_message(
        title,
        tag_names or [],
        correspondent_name,
        document_type_name,
        warnings or [],
    )
    mode = notify(message, doc_id=doc_id)

    return {
        "doc_id": doc_id,
        "notified": mode != "log",
        "mode": mode,
        "message": message,
        "warnings": warnings or [],
    }
