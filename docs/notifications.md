# Benachrichtigungen

Steuerung über `NOTIFY_MODE` in `.env`:

| Modus | Beschreibung |
|-------|--------------|
| `log` | Nur Windmill-Logs (Standard) |
| `matrix` | Direkt an Matrix-Room (ohne Hermes) |
| `hermes` | HTTP POST an Hermes-Webhook → Matrix/Telegram/etc. |

Nach `.env`-Änderung:

```bash
docker compose up -d windmill-worker
```

## Wann wird benachrichtigt?

| Event | Script | Inhalt |
|-------|--------|--------|
| Erfolg mit Warnings | `notify` | Titel, Metadaten, Warning-Liste |
| Flow-Fehler | `handle_flow_failure` | Step, Fehlermeldung, doc_id |

## Hermes-Webhook (`NOTIFY_MODE=hermes`)

Voraussetzungen:
- Hermes Gateway mit Webhook-Adapter (`WEBHOOK_ENABLED=true`, Port standardmäßig `8644`)
- Matrix (oder anderes Ziel) in Hermes konfiguriert

**1. Route anlegen:**

```bash
hermes webhook subscribe paperless-chain \
  --deliver matrix \
  --deliver-only \
  --prompt "{message}" \
  --description "Paperless-chAIn Dokumenten-Benachrichtigungen"
```

**2. In `.env`:**

```bash
NOTIFY_MODE=hermes
HERMES_WEBHOOK_URL=http://192.168.178.158:8644/webhooks/paperless-chain
HERMES_WEBHOOK_SECRET=<secret-aus-dem-subscribe-befehl>
```

**3. Testen:**

```bash
hermes webhook test paperless-chain --payload '{"message":"Test von Paperless-chAIn","doc_id":1,"event":"paperless_chain.document_processed"}'
```

## Alternative ohne Hermes

- `NOTIFY_MODE=matrix` — direkt Matrix-API (`MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID`)
- `NOTIFY_MODE=log` — kein externer Dienst nötig
