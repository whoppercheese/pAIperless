# Entwicklung

## Scripts deployen

```bash
./wmill-sync.sh
./wmill-sync.sh --dry-run    # Vorschau
```

## Einzelne Scripts testen

```bash
wmill script run f/paperless_chain/fetch_document \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"doc_id": 1}'
```

## Flows testen

```bash
# Vollverarbeitung
wmill flow run f/paperless_chain/process_document \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"doc_id": 1}'

# Nur Embedding
wmill flow run f/paperless_chain/embed_document \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"doc_id": 1}'
```

## Logs

```bash
docker compose logs -f windmill-worker
```

LLM-Requests und Paperless-PATCHs erscheinen als:

- `=== Paperless-chAIn LLM Request ===`
- `=== Paperless-chAIn Paperless PATCH ===`

## Stack aktualisieren

```bash
./update-stack.sh
```

Führt aus: `git pull` → `wmill sync push` → `docker compose down` → `docker compose up -d --build`

## Windmill CLI-Profil (optional)

Einmalig registrieren, danach reicht `wmill sync push --yes`:

```bash
wmill workspace add paperless_chain main http://localhost:8000
wmill sync push --yes
```

CLI aktualisieren: `wmill upgrade`
