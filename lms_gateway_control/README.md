# LMS Gateway Control

Dieses Add-on stellt eine Home-Assistant-Seitenleistenoberflaeche fuer einen extern laufenden LMS Gateway Dienst bereit.

## Optionen

- `external_host`: IP oder Hostname des Servers, auf dem LMS Gateway laeuft.
- `external_port`: Port des externen LMS Gateway, Standard `8088`.
- `api_base_path`: API-Basispfad, Standard `/api/v1`.
- `api_token`: optionales gemeinsames API-Token.
- `request_timeout_seconds`: Timeout fuer API-Aufrufe.

## Voraussetzungen

Der externe LMS Gateway Dienst muss erreichbar sein und die Standard-API `/api/v1` bereitstellen.
