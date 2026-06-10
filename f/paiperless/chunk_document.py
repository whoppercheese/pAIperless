import json

from f.paiperless.shared.ollama_client import chat_json
from f.paiperless.shared.prompts import SUMMARY
from f.paiperless.shared.chunking import build_chunks


def main(doc_id: int, text: str, analysis: dict, correspondent_name: str | None = None, tag_names: list | None = None) -> dict:
    summary_result = chat_json(
        SUMMARY,
        f"Analyse:\n{json.dumps(analysis, ensure_ascii=False)}\n\nDokument:\n{text[:12000]}",
    )
    summary = summary_result.get("summary", "")

    chunks = build_chunks(text=text, summary=summary, analysis=analysis)
    for chunk in chunks:
        chunk["doc_id"] = doc_id
        chunk["correspondent"] = correspondent_name
        chunk["tags"] = tag_names or []
        chunk["doc_nature"] = analysis.get("doc_nature", "Unbekanntes Dokument")

    return {
        "doc_id": doc_id,
        "summary": summary,
        "chunks": chunks,
        "analysis": analysis,
        "correspondent_name": correspondent_name,
        "tag_names": tag_names or [],
    }
