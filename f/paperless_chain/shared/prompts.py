import json


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "document_date": {"type": ["string", "null"]},
    },
    "required": ["summary"],
}

ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "selected_document_type": {"type": ["string", "null"]},
        "selected_correspondent": {"type": ["string", "null"]},
        "selected_tags": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "title",
        "selected_tags",
        "warnings",
    ],
}

CHUNK_SCHEMA = {
    "type": "object",
    "properties": {
        "chunks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["text", "label"],
            },
        },
    },
    "required": ["chunks"],
}


def _json_schema_instruction(schema: dict) -> str:
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
    return f"""\
JSON-SCHEMA (PFLICHT — exakt dieses Format einhalten):
{schema_json}

- Alle required-Felder müssen vorhanden sein
- Keine zusätzlichen Top-Level-Felder
- Feldtypen und verschachtelte Struktur exakt wie im Schema
- Antworte ausschließlich als JSON gemäß Schema. Keine Erklärungen außerhalb des JSON."""


def build_summary_prompt(document_language: str) -> str:
    lang = document_language
    return f"""\
Du erstellst eine Zusammenfassung eines Dokuments für eine Dokumentenverwaltung (Paperless-ngx).
Die Dokumentsprache laut Paperless ist: {lang}.
Antworte als JSON.

SPRACHE (PFLICHT):
- summary MUSS vollständig in der Dokumentsprache ({lang}) verfasst sein.
- NIEMALS in einer anderen Sprache antworten — auch nicht teilweise.
- Eigennamen, Firmennamen und Beträge unverändert übernehmen.

INHALT:
Lies den gesamten Text und fasse ihn zusammen.
- summary: ausführliche Zusammenfassung auf {lang}, typischerweise 6-12 Sätze
- Enthalte zwingend: Zweck, Absender/Absendername, Dokumentart, alle genannten Daten (Rechnungs-, Brief-, Vertragsdatum etc.), Beträge, Fristen, Vertragsparteien, wichtige Konditionen
- Keine Floskeln, keine Einleitung wie "Dieses Dokument..."
- Die Summary muss alle Fakten enthalten, die später für Titel, Dokumenttyp, Korrespondent und Tags benötigt werden

DATUM:
Extrahiere das relevante Dokumentdatum direkt aus dem Volltext (nicht aus heutigem Datum raten).
- document_date: YYYY-MM-DD oder null
- Priorität: Rechnungsdatum > Briefdatum > Vertragsdatum > Auszugsdatum > andere im Dokument genannte Daten
- Nur setzen wenn ein konkretes Datum im Text steht; bei mehreren Kandidaten das relevanteste nach Priorität wählen

{_json_schema_instruction(SUMMARY_SCHEMA)}"""


def build_analyze_prompt(document_language: str) -> str:
    lang = document_language
    return f"""\
Du extrahierst Metadaten aus einer Dokumenten-Zusammenfassung für Paperless-ngx.
Die Dokumentsprache laut Paperless ist: {lang}.
Im User-Prompt erhältst du die Auswahllisten und die Summary — nicht den Volltext.
Arbeite die folgenden Schritte der Reihe nach ab und antworte als ein einziges JSON-Objekt.

SPRACHE (PFLICHT):
- title MUSS vollständig in der Dokumentsprache ({lang}) verfasst sein.
- NIEMALS in einer anderen Sprache antworten — auch nicht teilweise.
- Eigennamen, Firmennamen und Beträge unverändert übernehmen.

AUSWAHL-LISTEN (im User-Prompt):
- VORHANDENE DOKUMENTTYPEN, VORHANDENE KORRESPONDENTEN, VORHANDENE TAGS
- optional AKTUELLE TAGS (bereits am Dokument)
- NUR exakte Namen aus diesen Listen verwenden, NIEMALS neue Namen erfinden

SCHRITT 1: TITEL
Leite aus der Summary einen Titel ab.
- title: kurzer Titel auf {lang}, 3-12 Wörter (Wortgrenzen einhalten, niemals mitten im Wort abbrechen).
  Enthalte Absender (Kurzname), Dokumentart und Datum/Zeitraum.
  Keine Rechnungsnummern, vollständigen Firmennamen oder Adressen.

SCHRITT 2: DOKUMENTTYP
Bestimme die Dokumentart aus der Summary und ordne sie einem Typ aus VORHANDENE DOKUMENTTYPEN zu.
- selected_document_type: exakter Name aus VORHANDENE DOKUMENTTYPEN, oder null nur wenn kein passender Typ existiert
Regeln:
- NUR Namen aus VORHANDENE DOKUMENTTYPEN verwenden, NIEMALS neue Typen erfinden oder vorschlagen
- Wenn die Summary die Dokumentart nennt (z.B. Rechnung, Vertrag, Kontoauszug, Brief) und ein passender Typ in VORHANDENE DOKUMENTTYPEN existiert: diesen Typ zuweisen — nicht null
- Synonyme und Abkürzungen berücksichtigen (z.B. Invoice → Rechnung, KTO-Auszug → Kontoauszug)
- Groß-/Kleinschreibung und Umlaute sind beim Vergleich irrelevant
- null nur wenn die Summary keine erkennbare Dokumentart enthält oder kein ähnlicher Eintrag in VORHANDENE DOKUMENTTYPEN existiert

SCHRITT 3: KORRESPONDENT
Bestimme den Absender aus VORHANDENE KORRESPONDENTEN.
- selected_correspondent: exakter Name aus VORHANDENE KORRESPONDENTEN, oder null wenn keiner passt
Regeln:
- NUR Namen aus VORHANDENE KORRESPONDENTEN verwenden, NIEMALS neue Korrespondenten erfinden oder vorschlagen
- Rechtsformen (GmbH, AG etc.), Titel (Dr., Prof.), Groß-/Kleinschreibung und Umlaute sind beim Vergleich irrelevant

SCHRITT 4: TAGS
Lege die finale Tag-Liste für das Dokument fest.
- selected_tags: Liste, NUR exakte Namen aus VORHANDENE TAGS — das ist die vollständige Ziel-Liste
Regeln:
- NUR Namen aus VORHANDENE TAGS verwenden, NIEMALS neue Tags erfinden oder vorschlagen
- Wenn AKTUELLE TAGS existieren: jeden einzeln prüfen; unpassende Tags weglassen, passende behalten
- Entferne Tags die thematisch nicht zum Dokument passen (z.B. falscher Absender, falsches Thema, veraltete Zuordnung)
- Ergänze bei Bedarf weitere passende Tags aus VORHANDENE TAGS (typisch 1-5)
- Ohne AKTUELLE TAGS: 1-5 passende Tags wählen; leere Liste nur wenn wirklich kein vorhandener Tag passt
- NIEMALS System-Tags vergeben oder in selected_tags aufnehmen: AI-Warning, AI-Error, AI-Processed
- Keine redundanten Tags (nicht mehrere für dasselbe Konzept)
- Vorhandene Personen-Tags wählen wenn Person im Dokument vorkommt
- Keine zu generischen ("Dokument") oder zu spezifischen ("Rechnung-2024-März") Tags

SCHRITT 5: WARNINGS
- warnings: immer eine leere Liste [] zurückgeben (Warnings werden serverseitig gesetzt)

JSON-AUSGABEFORMAT - verwende exakt diese Top-Level-Feldnamen (keine verschachtelten Schritte):
title, selected_document_type, selected_correspondent, selected_tags, warnings

{_json_schema_instruction(ANALYZE_SCHEMA)}"""


def build_generate_missing_schema(need_document_type: bool, need_correspondent: bool) -> dict:
    properties: dict = {}
    required: list[str] = []
    if need_document_type:
        properties["document_type"] = {"type": "string"}
        required.append("document_type")
    if need_correspondent:
        properties["correspondent"] = {"type": "string"}
        required.append("correspondent")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def build_generate_missing_prompt(
    document_language: str,
    need_document_type: bool,
    need_correspondent: bool,
) -> str:
    lang = document_language
    sections: list[str] = [
        f"""\
Du erzeugst fehlende Metadaten für ein Dokument in Paperless-ngx.
Die Dokumentsprache laut Paperless ist: {lang}.
Im User-Prompt erhältst du nur die Summary — nicht den Volltext.
Kein passender Eintrag existiert in den vorhandenen Paperless-Listen; lege neue, sinnvolle Namen an.
Antworte als JSON.

SPRACHE (PFLICHT):
- Alle Namen MUSS vollständig in der Dokumentsprache ({lang}) verfasst sein.
- NIEMALS in einer anderen Sprache antworten — auch nicht teilweise.
- Eigennamen, Firmennamen und Beträge unverändert übernehmen.""",
    ]
    if need_document_type:
        sections.append(
            f"""\
DOKUMENTTYP:
- document_type: passender Dokumenttyp auf {lang}, kurz und generisch (z.B. Rechnung, Vertrag, Kontoauszug)
- Nicht zu spezifisch: keine Rechnungsnummern, keine Datumsangaben, keine Beträge im Namen
- Der Typ muss klar zum Inhalt der Summary passen"""
        )
    if need_correspondent:
        sections.append(
            f"""\
KORRESPONDENT:
- correspondent: Absender aus der Summary — möglichst kurz und einfach
- Nur der Kernname: keine Rechtsformen (GmbH, AG, Inc., Ltd. etc.), keine Domains (.com), keine Zusätze
- Beispiel: "Amazon.com, Inc." → "Amazon"; "Deutsche Telekom AG" → "Deutsche Telekom"
- Bei Personen: Vor- und Nachname, ohne Anrede oder Titel
- Keine Adressen, keine E-Mail-Adressen"""
        )
    schema = build_generate_missing_schema(need_document_type, need_correspondent)
    sections.append(_json_schema_instruction(schema))
    return "\n\n".join(sections)


def build_generate_missing_user_prompt(doc_id: int, summary: str) -> str:
    return f"""\
Erzeuge die fehlenden Metadaten aus der folgenden Summary.

Dokument-ID: {doc_id}

Summary:
{summary.strip()}"""


def build_analyze_user_prompt(
    doc_id: int,
    summary: str,
    document_types: list[str],
    tags: list[str],
    correspondents: list[str],
    current_tags: list[str] | None = None,
) -> str:
    types_json = json.dumps(document_types, ensure_ascii=False)
    tags_json = json.dumps(tags, ensure_ascii=False)
    correspondents_json = json.dumps(correspondents, ensure_ascii=False)
    current = list(current_tags or [])
    current_tags_block = (
        f"AKTUELLE TAGS (bereits am Dokument — prüfen und bereinigen):\n"
        f"{json.dumps(current, ensure_ascii=False)}\n\n"
        if current
        else ""
    )
    return f"""\
VORHANDENE DOKUMENTTYPEN (NUR diese exakten Namen verwenden):
{types_json}

VORHANDENE KORRESPONDENTEN (NUR diese exakten Namen verwenden):
{correspondents_json}

VORHANDENE TAGS (NUR diese exakten Namen verwenden):
{tags_json}

{current_tags_block}Ordne anhand der folgenden Summary zu. Nur exakte Namen aus den obigen Listen verwenden.

Dokument-ID: {doc_id}

Summary:
{summary.strip()}"""


def build_chunk_prompt(document_language: str) -> str:
    lang = document_language
    return f"""\
Du teilst den Volltext eines Dokuments in semantische Such-Chunks auf.
Die Dokumentsprache laut Paperless ist: {lang}.
Antworte als JSON.

Regeln:
- chunks: Liste von Abschnitten mit "text" und "label"
- text: vollständiger Abschnittstext aus dem Dokument (keine Kürzung, keine Auslassungen mit "...")
- label: kurze Beschreibung auf {lang} (2-6 Wörter), z.B. Rechnungspositionen, Kündigungsfrist
- Bevorzuge wenige, größere Chunks statt vieler kleiner — zusammengehörige Inhalte in einem Chunk belassen
- Teile nur bei klar getrennten Themen (z.B. Vertragskern vs. Anlagen, Rechnungskopf vs. AGB)
- Kleine Absätze, Einleitungen oder Detailblöcke nicht einzeln abtrennen, wenn sie zum gleichen Thema gehören
- Tabellen und zugehörige Erläuterungen zusammen in einem Chunk belassen
- Teile nach inhaltlicher Logik, nicht nach Zeichen-, Token- oder Seitengrenzen
- Jeder Chunk soll für sich in einer Vektorsuche sinnvoll und ausreichend substanziell sein
- Keine Überschneidungen zwischen Chunks
- Zusammen sollen die Chunks den relevanten Dokumentinhalt abdecken
- Boilerplate (AGB, Datenschutz, Impressum) in einen Chunk bündeln
- Erzeuge KEINE Zusammenfassung — die wird separat gespeichert
- Mindestens 1 Chunk; kurze Dokumente oft in 1 Chunk, längere typischerweise in 2-5 Chunks (nur mehr wenn klar getrennte Hauptthemen)

{_json_schema_instruction(CHUNK_SCHEMA)}"""
