# Batch-Verarbeitung per Tag

Für bestehende Dokumente oder kontrollierte Nachverarbeitung: Dokumente mit einem Queue-Tag finden und Windmill-Jobs starten.

## Konzept

1. In Paperless einem Dokument einen **Queue-Tag** geben (z. B. `AI-Queue` oder `AI-Embed-Queue`)
2. Shell-Script oder Windmill-Script ausführen
3. Script findet alle Docs mit diesem Tag (älteste zuerst) und startet bis zu `limit` Flow-Jobs
4. Docs mit **Skip-Tags** werden übersprungen

## `queue-by-tag.sh` → `process_document`

Vollverarbeitung (Metadaten + Embedding):

```bash
./queue-by-tag.sh AI-Queue 10
```

Ruft `queue_documents_by_tag` auf. Standard-Skip: Dokumente mit `AI-Processed` werden übersprungen.

**Typischer Workflow:**

1. Tag `AI-Queue` in Paperless anlegen
2. Bestehenden Dokumenten `AI-Queue` zuweisen
3. `./queue-by-tag.sh AI-Queue 10` wiederholt ausführen, bis alle verarbeitet sind
4. Erfolgreiche Docs erhalten `AI-Processed` (vom Flow) und werden beim nächsten Lauf übersprungen

## `queue-embeddings.sh` → `embed_document`

Nur Embedding, keine Metadaten-Änderung:

```bash
./queue-embeddings.sh AI-Embed-Queue 10
```

Ruft `queue_embeddings_by_tag` auf. Standard-Skip: Dokumente mit `AI-Embedded`.

**Typischer Workflow:**

1. Tag `AI-Embed-Queue` anlegen
2. Docs taggen, die nur (neu) embedded werden sollen
3. `./queue-embeddings.sh AI-Embed-Queue 10`
4. Erfolgreiche Docs erhalten `AI-Embedded`

## Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `tag_name` | — | Queue-Tag in Paperless (Pflicht) |
| `limit` | `10` | Max. Anzahl Jobs pro Aufruf |
| `skip_tag_names` | siehe unten | Docs mit diesen Tags werden übersprungen |

| Script | Default `skip_tag_names` |
|--------|--------------------------|
| `queue_documents_by_tag` | `AI-Processed` |
| `queue_embeddings_by_tag` | `AI-Embedded` |

## Direkt in Windmill

```bash
wmill script run f/paperless_chain/queue_documents_by_tag \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"tag_name": "AI-Queue", "limit": 10}'

wmill script run f/paperless_chain/queue_embeddings_by_tag \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"tag_name": "AI-Embed-Queue", "limit": 10, "skip_tag_names": ["AI-Embedded"]}'
```

## Voraussetzungen

- `WMILL_BASE_URL`, `WMILL_WORKSPACE`, `WMILL_TOKEN` in `.env` (Shell-Scripts laden `.env` automatisch)
- Queue-Tag und Skip-Tags existieren in Paperless
- Windmill-Worker hat Paperless- und Windmill-Zugang (für `run_flow_async`)

Ausgabe listet `doc_id`, `job_id` und übersprungene Dokumente mit Grund.
