# Search UI

Semantische Suche über in Qdrant gespeicherte Dokument-Chunks.

**URL:** `http://localhost:8888` (Port via `SEARCH_PORT` in `.env`)

## Funktion

1. Suchanfrage wird via Ollama/bge-m3 in einen Embedding-Vektor umgewandelt
2. Qdrant liefert die ähnlichsten Chunks
3. Treffer werden nach Dokument gruppiert
4. Links führen direkt zum Paperless-Dokument

## Filter

- Korrespondent
- Tag
- Chunk-Typ: Summary oder Teil-Chunks

Filterwerte werden aus der Qdrant-Collection gelesen (scroll über Payload-Felder).

## Voraussetzungen

- Mindestens ein Dokument durch `process_document` oder `embed_document` verarbeitet
- Search-Container läuft (`docker compose up -d`)
- `OLLAMA_URL` und `PAPERLESS_URL` in `.env` für Embedding und Dokument-Links

## Technik

- FastAPI + HTMX
- Quellcode: `search/`
- Docker-Image wird via `docker-compose.yml` gebaut
