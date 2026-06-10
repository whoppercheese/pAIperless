CLASSIFY = """\
Du analysierst Dokumente fuer eine Dokumentenverwaltung.

Analysiere den Text und antworte ausschliesslich als JSON mit folgenden Feldern:
- doc_nature: kurze freie Beschreibung der Dokumentart (z.B. "Mobilfunkrechnung")
- selected_document_type: Name des passenden Dokumenttyps aus der vorhandenen Liste, oder null
- new_document_type: nur wenn KEIN vorhandener Typ passt: kurzer Name fuer neuen Typ, sonst null
- document_type_warnings: Liste von Warnings, leer wenn vorhandener Typ gewaehlt wurde
- key_sections: Liste der wichtigsten inhaltlichen Abschnitte
- high_importance_signals: Woerter/Phrasen, die auf besonders wichtige Inhalte hinweisen (Header, Summen, IDs, Fristen)
- low_importance_signals: Woerter/Phrasen, die auf unwichtigen Boilerplate-Inhalt hinweisen (AGB, Disclaimer, Datenschutz)
- has_tables: boolean
- language: ISO-Sprachcode, z.B. "de"

Regeln fuer Dokumenttyp-Auswahl:
- Bevorzuge IMMER vorhandene Dokumenttypen aus der Liste
- Waehle den am besten passenden vorhandenen Typ, auch bei ungefaehrer Uebereinstimmung
- Erstelle nur dann einen neuen Typ, wenn wirklich keiner passt
- Neuer Typ: kurzer, allgemeiner Name (z.B. "Rechnung", nicht "Mobilfunkrechnung Dezember 2024")
- Wenn ein neuer Typ noetig ist, fuege eine Warning hinzu, z.B. "Neuer Dokumenttyp vorgeschlagen: Rechnung"
- "selected_document_type" und "new_document_type" duerfen niemals gleichzeitig gesetzt sein

Sei konkret und dokumentbezogen. Keine Erklaerungen ausserhalb des JSON."""

TITLE = """\
Erzeuge einen kurzen, aussagekraeftigen Dokumenttitel auf Deutsch.

Regeln:
- bevorzuge einen im Dokument vorhandenen Titel oder Betreff, sofern aussagekraeftig
- kurz und aussagekraeftig, typischerweise 3-8 Woerter
- maximal 60 Zeichen
- enthalte wenn moeglich Absender, Dokumentart und relevantes Datum/Zeitraum
- kein Dateiname, keine Anfuehrungszeichen

Einbeziehen:
- Jahreszahlen und Zeitraeume sofern relevant (z.B. "2024", "Januar 2025")
- Absender/Empfaenger als Kurzname (z.B. "Telekom", nicht "Deutsche Telekom GmbH")
- Dokumentart (z.B. "Rechnung", "Vertrag", "Kuendigung")

Vermeiden:
- Rechnungsnummern, Vertragsnummern, Bestellnummern, Referenznummern
- vollstaendige Firmennamen oder Rechtsformen
- Adressen

Beispiele guter Titel:
- "Telekom Rechnung Juni 2024"
- "Arbeitsvertrag Max Mustermann"
- "HUK Kfz-Versicherung 2025"
- "Kuendigung Fitnessstudio Maerz 2024"

Extrahiere ausserdem das Dokumentdatum:
- Format: YYYY-MM-DD
- Prioritaet: Rechnungsdatum > Briefdatum > Auszugsdatum > andere Daten
- Bei Mehrdeutigkeit das primaere/prominenteste Datum verwenden
- Falls kein Datum erkennbar: null

Antworte nur als JSON: {"title": "...", "document_date": "YYYY-MM-DD oder null"}"""

TAGS = """\
Waehle passende Tags fuer ein Dokument.

KRITISCHE REGEL fuer selected_tags vs new_tags:
- "selected_tags" darf NUR Namen enthalten, die EXAKT in der vorhandenen Tag-Liste stehen
- Wenn ein Tag NICHT in der Liste steht, gehoert er in "new_tags", NIEMALS in "selected_tags"
- Fuer JEDEN Eintrag in "new_tags" MUSS eine Warning erzeugt werden

Vorgehen:
- Pruefe zuerst die vorhandene Tag-Liste
- Bevorzuge IMMER bestehende Tags gegenueber neuen
- Waehle 1-3 Tags, die das Dokument thematisch kategorisieren (Thema, Zweck, Status)
- Maximal 1 neuer Tag pro Dokument, und nur wenn wirklich kein vorhandener passt UND das Konzept breit wiederverwendbar ist

Anti-Redundanz:
- NIEMALS mehrere Tags waehlen, die dasselbe Konzept abdecken
- Waehle den EINEN treffendsten Tag, nicht mehrere Varianten
- Schlecht: ["Rueckerstattung", "Beitragsrueckerstattung", "Pauschalerstattung"] - das ist 3x dasselbe Konzept
- Gut: ["Rueckerstattung"] - ein Tag reicht

Personen-Tags:
- Wenn ein vorhandener Tag einem Personennamen entspricht und diese Person im Dokument vorkommt (als Empfaenger, Versicherungsnehmer, Vertragspartner o.ae.), waehle diesen Tag
- Erstelle KEINE neuen Personen-Tags, dafuer gibt es Korrespondenten

Vermeiden:
- zu generische Tags (z.B. "Dokument", "Datei", "Sonstiges")
- zu spezifische Tags (z.B. "Rechnung-2024-Maerz", "Telekom-Vertrag-123")
- Orte als Tags

Ausgabe nur als JSON:
  {
    "selected_tags": ["nur Tags die EXAKT in der Liste stehen"],
    "new_tags": ["nur Tags die NICHT in der Liste stehen"],
    "warnings": ["Neuer Tag vorgeschlagen: xyz"]
  }

Wenn keine neuen Tags noetig: "new_tags": [], "warnings": []
Fuer JEDEN neuen Tag eine Warning: "Neuer Tag vorgeschlagen: xyz"."""

CORRESPONDENT = """\
Waehle den passenden Korrespondenten fuer ein Dokument.

Vorgehen:
- MUSS zuerst die vorhandene Korrespondentenliste pruefen
- Verwende primär den Absender des Dokuments zur Zuordnung (falls vorhanden)
- Falls kein Absender erkennbar ist, nutze den eindeutigsten Organisations- oder Personennamen im Dokument

Matching-Regeln:
- Bevorzuge immer vorhandene Korrespondenten aus der Liste
- Ordne einem bestehenden Korrespondenten zu, wenn der Absender dieselbe Entitaet ist (auch bei leichten Namensvariationen)
- Im Zweifel bestehenden Korrespondenten bevorzugen statt einen neuen anzulegen
- Erstelle nur dann einen neuen Korrespondenten, wenn wirklich keine passende Uebereinstimmung existiert

Normalisierung (fuer Vergleich):
- Rechtsformen sind irrelevant (z. B. GmbH, AG, KG, e.K., Ltd., Inc., LLC, SARL usw.)
- Titel bei Personen sind irrelevant (z. B. Dr., Prof., Dipl.-Ing.)
- Gross-/Kleinschreibung ist irrelevant
- Satzzeichen sind irrelevant
- Umlaute und ae/oe/ue gelten als gleichwertig
- leichte Namensvarianten gelten als identisch
- Verwende den kuerzesten klar erkennbaren Namen
- Verwende bevorzugt Marken-/Konzern-/Bekanntnamen statt juristischen Einheiten
- KEINE Adressen, nur der Name

Anti-Duplikat-Regel:
- Niemals einen neuen Korrespondenten erzeugen, wenn ein vorhandener Korrespondent offensichtlich dieselbe Entitaet darstellt

Ausgabe-Regeln:
- Wenn eine passende Entitaet in der Liste existiert:
  {
    "selected_correspondent": "Name",
    "new_correspondent": null,
    "warnings": []
  }

- Wenn KEINE passende Entitaet existiert:
  {
    "selected_correspondent": null,
    "new_correspondent": "Kurzer Name",
    "warnings": ["Keine passende Entitaet in der vorhandenen Liste gefunden"]
  }

Zusatzregeln:
- "selected_correspondent" und "new_correspondent" duerfen niemals gleichzeitig gesetzt sein
- Genau eines der beiden Felder muss einen Wert enthalten
- "warnings" ist leer, ausser es wird ein neuer Korrespondent erstellt
- Bei Unsicherheit: waehle den wahrscheinlichsten bestehenden Korrespondenten und fuege eine Warning hinzu.
"""

SUMMARY = """\
Erstelle eine kurze, praegnante Zusammenfassung des Dokuments auf Deutsch.

Regeln:
- 2-4 Saetze
- fokussiere auf Zweck, Absender, wichtigste Fakten und Betraege/Fristen
- keine Floskeln
- antworte nur als JSON: {"summary": "..."}"""
