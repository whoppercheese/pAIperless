# Setup

## Voraussetzungen

- Docker & Docker Compose
- **Node.js ≥ 20** und **npm** (Windmill CLI)
- Paperless-ngx (läuft bereits)
- Ollama mit LLM (z. B. `qwen3`) und `bge-m3`
- Optional: Hermes Agent oder Matrix für Benachrichtigungen

## Phasen

| Phase | Was |
|-------|-----|
| Vorbereitung | `.env`, Paperless API-Token, Ollama-Modelle, Status-Tags in Paperless |
| Stack | `docker compose up -d` |
| Windmill | Workspace, API-Token, `./wmill-sync.sh` |
| Paperless | Workflow mit Webhook auf `process_document` |
| Test | Flow manuell oder per Test-Webhook |

## 1. `.env` und externe Dienste

```bash
cp .env.example .env
```

Mindestens setzen:

| Variable | Beschreibung |
|----------|--------------|
| `PAPERLESS_URL` | Erreichbar **vom Windmill-Worker** (z. B. `http://host.docker.internal:8010`) |
| `PAPERLESS_API_TOKEN` | Paperless → **Settings → API Tokens** |
| `OLLAMA_URL` | Erreichbar **vom Windmill-Worker** (z. B. `http://host.docker.internal:11434`) |
| `OLLAMA_LLM_MODEL` | z. B. `qwen3` |
| `OLLAMA_EMBED_MODEL` | z. B. `bge-m3` |

**System-Tags in Paperless** (exakte Namen):

| Tag | Wann gesetzt |
|-----|--------------|
| `AI-Processed` | Erfolgreicher `process_document`-Durchlauf |
| `AI-Warning` | Verarbeitung mit Warnings |
| `AI-Error` | Flow-Fehler |
| `AI-Embedded` | Erfolgreicher `embed_document`-Durchlauf |

**Ollama-Modelle:**

```bash
ollama pull qwen3
ollama pull bge-m3
```

## 2. Stack starten

```bash
docker compose up -d
```

| Dienst | Standard-URL |
|--------|--------------|
| Windmill UI | `http://localhost:8000` (`WINDMILL_PORT`) |
| Search UI | `http://localhost:8888` (`SEARCH_PORT`) |
| Qdrant | `http://localhost:6333` (`QDRANT_PORT`) |

Stack aktualisieren:

```bash
./update-stack.sh
```

Nach `.env`-Änderungen Worker neu laden:

```bash
docker compose up -d windmill-worker
```

## 3. Windmill einrichten

`docker compose up` startet nur Container — Scripts und Flows müssen per CLI gepusht werden.

### 3.1 Erster Zugang

1. Windmill UI öffnen: `http://localhost:8000`
2. Admin-Benutzer anlegen
3. Workspace wählen (z. B. `main` oder `paperless-chain`) — ID steckt in der Webhook-URL

### 3.2 API-Token

1. **User-Menü → Account Settings**
2. **Tokens → Add token**
3. Token in `.env` als `WMILL_TOKEN` speichern

### 3.3 CLI & Deploy

```bash
npm install -g windmill-cli
```

In `.env`:

```bash
WMILL_BASE_URL=http://localhost:8000
WMILL_WORKSPACE=main
WMILL_TOKEN=wm_xxxxxxxx
```

Deploy:

```bash
./wmill-sync.sh
```

Dry-Run: `./wmill-sync.sh --dry-run`

**Prüfen:** **Flows** → `process_document` und `embed_document`; unter **Scripts** die einzelnen Schritte.

### 3.4 Flow testen (ohne Paperless)

```bash
wmill flow run f/paperless_chain/process_document \
  --base-url "$WMILL_BASE_URL" \
  --workspace "$WMILL_WORKSPACE" \
  --token "$WMILL_TOKEN" \
  -d '{"doc_id": 1}'
```

Logs:

```bash
docker compose logs -f windmill-worker
```

## Paperless-Workflow

**Settings → Workflows** → neuer Workflow:

| Feld | Wert |
|------|------|
| Name | Paperless-chAIn Auto-Process |
| Trigger | **Document Added** |
| Action | **Webhook** |
| Method | POST |
| Content-Type | `application/json` |
| Body | `{"doc_url": "{{ doc_url }}"}` |

**Webhook-URL:**

```
http://<windmill-host>:<WINDMILL_PORT>/api/w/<workspace>/jobs/run/f/f/paperless_chain/process_document?token=<API-TOKEN>
```

Beispiel lokal, Workspace `main`:

```
http://localhost:8000/api/w/main/jobs/run/f/f/paperless_chain/process_document?token=wm_xxxxxxxx
```

**Netzwerk:** Paperless muss Windmill unter dieser URL erreichen. `localhost` funktioniert nicht, wenn Paperless und Windmill in verschiedenen Containern/Hosts laufen — stattdessen Host-IP oder `host.docker.internal`.

**Test-Webhook:**

```bash
curl -X POST \
  'http://localhost:8000/api/w/main/jobs/run/f/f/paperless_chain/process_document?token=DEIN_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"doc_url": "http://paperless/documents/42/"}'
```

Die `doc_url` muss nicht erreichbar sein — nur die ID im Pfad zählt.

## Checkliste

- [ ] Node.js ≥ 20 + `windmill-cli` (`wmill --version`)
- [ ] `.env` mit `WMILL_*`, `PAPERLESS_*`, `OLLAMA_*`
- [ ] Ollama-Modelle gepullt
- [ ] Tags `AI-Processed`, `AI-Warning`, `AI-Error`, `AI-Embedded` in Paperless
- [ ] Windmill Admin + Workspace, `WMILL_TOKEN` gesetzt
- [ ] `./wmill-sync.sh` erfolgreich
- [ ] Flow-Test mit `wmill flow run` oder curl OK
- [ ] Paperless-Workflow **Document Added → Webhook** aktiv
- [ ] Search UI unter `:8888` erreichbar
- [ ] Optional: Benachrichtigungen — [notifications.md](notifications.md)
