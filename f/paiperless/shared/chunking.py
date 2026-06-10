import re
import unicodedata
from dataclasses import dataclass

TOKEN_CHARS = 4
MIN_FINE_CHARS = 300 * TOKEN_CHARS
MAX_FINE_CHARS = 500 * TOKEN_CHARS
OVERLAP_CHARS = 75 * TOKEN_CHARS

LOW_IMPORTANCE_DEFAULTS = [
    "agb", "datenschutz", "haftungsausschluss", "disclaimer",
    "rechtliche hinweise", "allgemeine geschäftsbedingungen",
    "widerrufsbelehrung", "impressum", "kleingedrucktes", "boilerplate",
]
HIGH_IMPORTANCE_DEFAULTS = [
    "rechnungsnummer", "gesamtbetrag", "summe", "total", "betrag",
    "kundennummer", "vertragsnummer", "fällig", "iban", "steuernummer",
    "header", "kopf",
]


@dataclass
class Chunk:
    text: str
    chunk_type: str
    chunk_level: str
    importance: float
    importance_reason: str


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u00ad\n", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _remove_repeated_headers_footers(text: str) -> str:
    pages = re.split(r"\f+|\n-{3,}\n", text)
    if len(pages) < 2:
        return text
    header_candidates: dict[str, int] = {}
    footer_candidates: dict[str, int] = {}
    for page in pages:
        lines = [line.strip() for line in page.split("\n") if line.strip()]
        if not lines:
            continue
        for line in lines[:2]:
            header_candidates[line] = header_candidates.get(line, 0) + 1
        for line in lines[-2:]:
            footer_candidates[line] = footer_candidates.get(line, 0) + 1
    repeated_h = {l for l, c in header_candidates.items() if c >= 2 and len(l) < 120}
    repeated_f = {l for l, c in footer_candidates.items() if c >= 2 and len(l) < 120}
    cleaned = []
    for page in pages:
        lines = [line.strip() for line in page.split("\n")]
        filtered = [l for l in lines if l and l not in repeated_h and l not in repeated_f]
        cleaned.append("\n".join(filtered))
    return "\n\n".join(p for p in cleaned if p.strip())


def _split_sections(text: str) -> list[str]:
    lines = text.split("\n")
    sections: list[str] = []
    current: list[str] = []
    heading_re = re.compile(
        r"^(?:[A-ZÄÖÜ][A-ZÄÖÜ0-9 .\-/]{2,}|[0-9]+(?:\.[0-9]+)*\s+.+|#{1,6}\s+.+)$"
    )
    for line in lines:
        if heading_re.match(line.strip()) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [s for s in sections if s]


def _is_table_block(text: str) -> bool:
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) < 2:
        return False
    table_like = sum(1 for l in lines if re.search(r"\s{2,}|\t|\|", l))
    return table_like / len(lines) >= 0.5


def _split_fine_chunks(text: str) -> list[str]:
    if len(text) // TOKEN_CHARS <= 500:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + MAX_FINE_CHARS)
        if end < len(text):
            split_at = text.rfind("\n\n", start + MIN_FINE_CHARS, end)
            if split_at == -1:
                split_at = text.rfind(". ", start + MIN_FINE_CHARS, end)
            if split_at != -1:
                end = split_at + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - OVERLAP_CHARS, start + 1)
    return chunks


def _classify_chunk_type(text: str, section_index: int) -> str:
    lowered = text.lower()
    if section_index == 0:
        return "header"
    if _is_table_block(text):
        return "table"
    if re.search(r"(gesamt|summe|total|betrag|zahlbar|iban)", lowered):
        return "totals"
    if re.search(r"(agb|datenschutz|haftung|disclaimer|widerruf)", lowered):
        return "boilerplate"
    return "section"


def _score_importance(
    text: str, chunk_type: str, high_signals: list[str], low_signals: list[str],
    section_index: int, section_count: int,
) -> tuple[float, str]:
    if chunk_type == "summary":
        return 1.0, "high:document summary"
    lowered = text.lower()
    high_terms = [s.lower() for s in high_signals] + HIGH_IMPORTANCE_DEFAULTS
    low_terms = [s.lower() for s in low_signals] + LOW_IMPORTANCE_DEFAULTS
    high_hits = [t for t in high_terms if t and t in lowered]
    low_hits = [t for t in low_terms if t and t in lowered]
    if chunk_type in {"header", "totals", "table"}:
        return 0.9, f"high:{chunk_type}"
    if high_hits:
        return min(1.0, 0.8 + 0.05 * len(high_hits)), f"high:{high_hits[0]}"
    if low_hits:
        return max(0.1, 0.3 - 0.05 * len(low_hits)), f"low:{low_hits[0]}"
    if section_index == 0 and section_count > 1:
        return 0.75, "high:first section heuristic"
    if section_index == section_count - 1 and re.search(r"unterschrift|signature|mit freundlichen", lowered):
        return 0.7, "normal:closing section"
    return 0.55, "normal:body text"


def build_chunks(text: str, summary: str, analysis: dict) -> list[dict]:
    normalized = _remove_repeated_headers_footers(_normalize_text(text))
    sections = _split_sections(normalized) or [normalized]
    high_signals = analysis.get("high_importance_signals", [])
    low_signals = analysis.get("low_importance_signals", [])
    chunks: list[Chunk] = []

    if summary.strip():
        chunks.append(Chunk(text=summary.strip(), chunk_type="summary", chunk_level="L1",
                            importance=1.0, importance_reason="high:document summary"))

    for idx, section in enumerate(sections):
        stype = _classify_chunk_type(section, idx)
        imp, reason = _score_importance(section, stype, high_signals, low_signals, idx, len(sections))
        chunks.append(Chunk(text=section, chunk_type=stype, chunk_level="L2", importance=imp, importance_reason=reason))
        if stype in {"table", "totals", "header"}:
            continue
        for fine_text in _split_fine_chunks(section):
            fimp, freason = _score_importance(fine_text, "fine", high_signals, low_signals, idx, len(sections))
            chunks.append(Chunk(text=fine_text, chunk_type="fine", chunk_level="L3", importance=fimp, importance_reason=freason))

    return [
        {"text": c.text, "chunk_type": c.chunk_type, "chunk_level": c.chunk_level,
         "importance": c.importance, "importance_reason": c.importance_reason}
        for c in chunks
    ]
