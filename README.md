# LMS Gateway Home Assistant Add-on Repository

![LMS Gateway](assets/lms-gateway-icon.svg)

Aktuelle Add-on-Version: `0.1.4`

Dieses Repository stellt das Home-Assistant-Add-on `LMS Gateway Control` bereit.

Das Add-on enthaelt nicht die LMS-Steuerlogik. Es dient als installierbare Home-Assistant-Oberflaeche fuer einen extern laufenden LMS-Gateway-Dienst.

## Installation

1. In Home Assistant den Add-on Store oeffnen.
2. Dieses Repository als benutzerdefiniertes Add-on-Repository hinzufuegen.
3. `LMS Gateway Control` installieren.
4. In den Add-on-Optionen Host und Port des externen LMS Gateway eintragen. Das API-Token bleibt standardmaessig leer.

## Architektur

- Externer Dienst: Python/FastAPI LMS Gateway auf einem Windows- oder Linux-Server.
- Add-on: Home-Assistant-Ingress-Oberflaeche fuer Konfiguration, Diagnose, Logs und Aktionen.
- Schnittstelle: HTTP API unter `/api/v1`.
