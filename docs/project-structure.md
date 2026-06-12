# Projektstruktur

```
paperless-chain/
├── f/paperless_chain/
│   ├── process_document.flow/     # Haupt-Flow (Webhook)
│   ├── embed_document.flow/       # Nur Embedding
│   ├── preprocess_webhook.py      # doc_url → doc_id
│   ├── fetch_document.py
│   ├── summarize_document.py
│   ├── derive_title.py
│   ├── resolve_document_type.py
│   ├── resolve_correspondent.py
│   ├── update_paperless.py
│   ├── chunk_document.py
│   ├── generate_embeddings.py
│   ├── store_qdrant.py
│   ├── apply_status_tags.py       # AI-Warning
│   ├── apply_embedded_tag.py      # AI-Embedded
│   ├── handle_flow_failure.py     # AI-Error
│   ├── notify.py
│   ├── queue_documents_by_tag.py  # Batch → process_document
│   ├── queue_embeddings_by_tag.py # Batch → embed_document
│   └── shared/
│       ├── ollama_client.py
│       ├── paperless_client.py
│       ├── windmill_client.py
│       ├── notify_client.py
│       ├── prompts.py
│       └── text_utils.py
├── search/                        # Search UI (FastAPI + HTMX)
├── docker-compose.yml
├── wmill.yaml / wmill-lock.yaml
├── wmill-sync.sh
├── update-stack.sh
├── queue-by-tag.sh
└── queue-embeddings.sh
```

## System-Tags

| Tag | Gesetzt von | Bedeutung |
|-----|-------------|-----------|
| `AI-Processed` | `update_paperless` | Vollverarbeitung abgeschlossen |
| `AI-Warning` | `apply_status_tags` | Warnings bei Verarbeitung |
| `AI-Error` | `handle_flow_failure` | Flow abgebrochen |
| `AI-Embedded` | `apply_embedded_tag` | Embedding-Flow abgeschlossen |

System-Tags werden vom LLM bei Tag-Auswahl ignoriert (`text_utils.SYSTEM_TAG_NAMES`).

## Qdrant Chunk-Struktur

Teil-Chunk:

```json
{
  "vector": [0.1, 0.2, "..."],
  "payload": {
    "doc_id": 123,
    "chunk_kind": "chunk",
    "label": "Rechnungspositionen",
    "correspondent": "Telekom",
    "tags": ["rechnung"],
    "text": "...",
    "document_type": "Rechnung"
  }
}
```

Zusätzlich pro Dokument ein Chunk mit `"chunk_kind": "summary"`.

Collection-Name: `QDRANT_COLLECTION` in `.env` (Default: `paperless-chain-documents` in `.env.example`, `paperless_chain_documents` in `docker-compose.yml` — Werte angleichen).

## Docker-Stack

| Service | Rolle |
|---------|-------|
| `qdrant` | Vektor-DB |
| `windmill-db` | PostgreSQL für Windmill |
| `windmill-server` | Windmill API + UI |
| `windmill-worker` | Flow-Ausführung (Ollama, Paperless, Qdrant) |
| `search` | Search UI |

Worker-Umgebungsvariablen werden über `WHITELIST_ENVS` an Python-Scripts durchgereicht.
