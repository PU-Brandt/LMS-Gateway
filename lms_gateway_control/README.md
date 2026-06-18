# LMS Gateway Control

Aktuelle Add-on-Version: `0.1.4`

Dieses Add-on stellt eine Home-Assistant-Seitenleistenoberflaeche fuer einen extern laufenden LMS Gateway Dienst bereit.

## Optionen

- `external_host`: IP oder Hostname des Servers, auf dem LMS Gateway laeuft.
- `external_port`: Port des externen LMS Gateway, Standard `8088`.
- `api_base_path`: API-Basispfad, Standard `/api/v1`.
- `api_token`: optionales gemeinsames API-Token. Standard ist leer; dann arbeitet das Add-on ohne Token.
- `request_timeout_seconds`: Timeout fuer API-Aufrufe.

Die Schaltflaeche `LMS auslesen` liest die aktuell vom Logitech Media Server gemeldeten Player ein und uebernimmt sie in die Player-Konfiguration.

## Voraussetzungen

Der externe LMS Gateway Dienst muss erreichbar sein und die Standard-API `/api/v1` bereitstellen.

Wenn im Python-Dienst unter `security.token` ein Token gesetzt wird, muss im Add-on dasselbe Token eingetragen werden. Bleibt `security.token` leer, bleibt auch `api_token` im Add-on leer.
