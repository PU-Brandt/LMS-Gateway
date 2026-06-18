# Dokumentation

## Standard-API

Das Add-on erwartet diese Endpunkte auf dem externen Dienst:

- `GET /api/v1/manifest`
- `GET /api/v1/health`
- `GET /api/v1/status`
- `GET /api/v1/config`
- `PUT /api/v1/config`
- `POST /api/v1/reload`
- `POST /api/v1/actions/{action_id}`
- `GET /api/v1/logs/recent`

## Aktionen

- `test_connection`
- `refresh_players`
- `reload`
- `restart`
- `shutdown`

`restart` und `shutdown` muessen in der Oberflaeche bestaetigt werden. Wenn im externen Dienst ein Token gesetzt ist, werden schreibende und kritische API-Aufrufe mit `Authorization: Bearer <token>` abgesichert.
