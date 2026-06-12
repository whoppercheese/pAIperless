# Paperless-chAIn

AI-Erweiterung für [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx): automatische Metadaten, semantisches Chunking und Vektor-Suche — orchestriert mit [Windmill](https://www.windmill.dev/).

## Was es macht

- **Neue Dokumente** (Webhook): Summary, Titel, Tags, Korrespondent, Dokumenttyp → Paperless-Update → Embeddings in Qdrant
- **Nur Embeddings** (`embed_document`): bestehende Metadaten beibehalten, nur Chunking + Qdrant
- **Batch-Verarbeitung**: Dokumente per Tag in die Queue stellen (`queue-by-tag.sh`, `queue-embeddings.sh`)
- **Search UI**: semantische Suche über alle Chunks (FastAPI + HTMX)

## Quick Start

```bash
cp .env.example .env          # PAPERLESS_*, OLLAMA_*, WMILL_* setzen
docker compose up -d          # Qdrant, Windmill, Search UI
./wmill-sync.sh               # Scripts & Flows deployen
```

Paperless-Workflow: **Document Added → Webhook** auf `process_document`.  
Details: [Setup](docs/setup.md) · [Paperless-Webhook](docs/setup.md#paperless-workflow)

| Dienst | URL |
|--------|-----|
| Windmill | `http://localhost:8000` |
| Search UI | `http://localhost:8888` |
| Qdrant | `http://localhost:6333` |

**Paperless-Tags anlegen:** `AI-Processed`, `AI-Warning`, `AI-Error`, `AI-Embedded`

## Dokumentation

| Thema | Datei |
|-------|-------|
| Installation & Konfiguration | [docs/setup.md](docs/setup.md) |
| Flows & Schritte | [docs/flows.md](docs/flows.md) |
| Batch-Queue per Tag | [docs/batch-processing.md](docs/batch-processing.md) |
| Search UI | [docs/search.md](docs/search.md) |
| Benachrichtigungen | [docs/notifications.md](docs/notifications.md) |
| Entwicklung & Tests | [docs/development.md](docs/development.md) |
| Projektstruktur & Qdrant | [docs/project-structure.md](docs/project-structure.md) |

## Hilfsskripte

| Script | Zweck |
|--------|-------|
| `./wmill-sync.sh` | Windmill-Scripts/Flows pushen |
| `./update-stack.sh` | git pull + sync + Docker rebuild |
| `./queue-by-tag.sh <tag> [limit]` | `process_document` für getaggte Docs |
| `./queue-embeddings.sh <tag> [limit]` | `embed_document` für getaggte Docs |
