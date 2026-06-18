#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


INGRESS_PORT = 8099
OPTIONS_PATH = Path("/data/options.json")
ADDON_VERSION = "0.1.2"


def load_options() -> dict[str, Any]:
    if OPTIONS_PATH.exists():
        return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    return {
        "external_host": "",
        "external_port": 8088,
        "api_base_path": "/api/v1",
        "api_token": "",
        "request_timeout_seconds": 30,
    }


def build_base_url(options: dict[str, Any]) -> str:
    host = str(options.get("external_host") or "").strip()
    port = int(options.get("external_port") or 8088)
    base_path = str(options.get("api_base_path") or "/api/v1").strip()
    if not host:
        return ""
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    parsed = urlparse(host)
    netloc = parsed.netloc
    if ":" not in netloc:
        netloc = f"{netloc}:{port}"
    root = f"{parsed.scheme}://{netloc}"
    return urljoin(root.rstrip("/") + "/", base_path.strip("/") + "/")


def tool_request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    options = load_options()
    base_url = build_base_url(options)
    if not base_url:
        return 400, {"status": "error", "message": "external_host ist nicht konfiguriert"}

    headers: dict[str, str] = {}
    token = str(options.get("api_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = int(options.get("request_timeout_seconds") or 30)
    try:
        response = requests.request(
            method,
            urljoin(base_url, path.lstrip("/")),
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return 502, {"status": "error", "message": str(exc), "base_url": base_url}

    try:
        body = response.json()
    except ValueError:
        body = {"status": "error", "message": response.text}
    return response.status_code, body


def render_page() -> bytes:
    options = load_options()
    base_url = build_base_url(options) or "nicht konfiguriert"
    html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LMS Gateway</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Segoe UI, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f5f7f9; color: #1f2933; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 22px; }}
    h1 {{ font-size: 26px; margin: 0 0 16px; display: flex; gap: 10px; align-items: center; }}
    h2 {{ font-size: 17px; margin: 0 0 12px; }}
    section {{ background: #fff; border: 1px solid #d8e0e8; border-radius: 8px; padding: 16px; margin-bottom: 14px; }}
    .badge {{ font-size: 12px; font-weight: 600; color: #52606d; background: #e8eef5; border-radius: 999px; padding: 4px 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .tile {{ border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; background: #f9fbfd; }}
    .label {{ color: #596673; font-size: 12px; margin-bottom: 4px; }}
    .value {{ font-size: 15px; font-weight: 600; word-break: break-word; }}
    .banner {{ padding: 12px; border-radius: 6px; border: 1px solid #fed7aa; background: #fff7ed; margin: 12px 0; }}
    .banner.ok {{ border-color: #bbf7d0; background: #ecfdf5; }}
    .banner.error {{ border-color: #fecaca; background: #fef2f2; }}
    textarea {{ width: 100%; min-height: 360px; box-sizing: border-box; border: 1px solid #b8c4d0; border-radius: 6px; padding: 10px; font: 13px Consolas, monospace; resize: vertical; }}
    label {{ display: block; font-size: 12px; color: #596673; margin-bottom: 5px; }}
    input, select {{ width: 100%; box-sizing: border-box; border: 1px solid #b8c4d0; border-radius: 6px; padding: 8px 9px; font: inherit; background: #fff; color: #1f2933; }}
    .form-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .field {{ min-width: 0; }}
    .subhead {{ font-size: 15px; font-weight: 700; margin: 18px 0 10px; }}
    .rows {{ display: grid; gap: 10px; }}
    .row-card {{ border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; background: #f9fbfd; }}
    .player-grid {{ display: grid; grid-template-columns: 1fr 1.4fr 1.2fr 1.4fr 1.6fr auto; gap: 8px; align-items: end; }}
    .device-grid {{ display: grid; grid-template-columns: 1.3fr 1.3fr auto; gap: 8px; align-items: end; }}
    button {{ border: 0; border-radius: 6px; background: #2563eb; color: white; padding: 9px 13px; font: inherit; cursor: pointer; }}
    button.secondary {{ background: #52606d; }}
    button.danger {{ background: #b42318; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; max-height: 300px; overflow: auto; }}
    #message {{ min-height: 22px; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #11161c; color: #e6edf3; }}
      section, textarea, input, select {{ background: #171d24; color: #e6edf3; border-color: #344250; }}
      .tile, pre {{ background: #111820; border-color: #344250; }}
      .label, label {{ color: #aab6c2; }}
      .row-card {{ background: #111820; border-color: #344250; }}
      .badge {{ background: #273444; color: #d6e0ea; }}
      .banner {{ background: #332414; border-color: #7a4b18; }}
      .banner.ok {{ background: #133226; border-color: #246b4a; }}
      .banner.error {{ background: #371818; border-color: #7a3030; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>LMS Gateway <span class="badge" id="versionBadge">Add-on {ADDON_VERSION}</span></h1>
  <section>
    <div class="grid">
      <div class="tile"><div class="label">Externer Dienst</div><div class="value">{base_url}</div></div>
      <div class="tile"><div class="label">Add-on</div><div class="value">Ingress Control</div></div>
      <div class="tile"><div class="label">Timeout</div><div class="value">{options.get("request_timeout_seconds", 30)} Sekunden</div></div>
    </div>
  </section>
  <section>
    <div class="actions">
      <h2 style="margin-right:auto">Status</h2>
      <button onclick="loadAll()">Aktualisieren</button>
      <button class="secondary" onclick="runAction('test_connection')">Verbindung testen</button>
      <button class="secondary" onclick="runAction('refresh_players')">Player aktualisieren</button>
      <button class="secondary" onclick="runAction('reload')">Neu laden</button>
      <button class="danger" onclick="runCritical('restart')">Neustart</button>
      <button class="danger" onclick="runCritical('shutdown')">Beenden</button>
    </div>
    <p id="message"></p>
    <div id="statusBanner" class="banner">Status noch nicht geladen.</div>
    <div class="grid">
      <div class="tile"><div class="label">LMS</div><div class="value" id="tileLms">-</div></div>
      <div class="tile"><div class="label">Player</div><div class="value" id="tilePlayers">-</div></div>
      <div class="tile"><div class="label">Raeume</div><div class="value" id="tileRooms">-</div></div>
      <div class="tile"><div class="label">Konfiguration</div><div class="value" id="tileConfig">-</div></div>
    </div>
  </section>
  <section>
    <div class="actions">
      <h2 style="margin-right:auto">Konfiguration</h2>
      <button class="secondary" onclick="loadConfig()">Einlesen</button>
      <button onclick="saveConfig()">Speichern</button>
      <button class="secondary" onclick="toggleAdvanced()">JSON anzeigen</button>
    </div>
    <div class="subhead">Server und LMS</div>
    <div class="form-grid">
      <div class="field"><label for="lmsHost">LMS IP oder Host</label><input id="lmsHost"></div>
      <div class="field"><label for="lmsHttpPort">LMS Web-Port</label><input id="lmsHttpPort" type="number" min="1" max="65535"></div>
      <div class="field"><label for="lmsCliPort">LMS CLI-Port</label><input id="lmsCliPort" type="number" min="1" max="65535"></div>
      <div class="field"><label for="lmsTimeout">Timeout Sekunden</label><input id="lmsTimeout" type="number" min="1" max="300"></div>
      <div class="field"><label for="dialogTtl">Dialog-Zeitfenster Sekunden</label><input id="dialogTtl" type="number" min="30" max="3600"></div>
      <div class="field"><label for="gatewayHost">Gateway Host</label><input id="gatewayHost"></div>
      <div class="field"><label for="gatewayPort">Gateway Port</label><input id="gatewayPort" type="number" min="1" max="65535"></div>
      <div class="field"><label for="gatewayPublicUrl">Adresse des Pipedienstes</label><input id="gatewayPublicUrl"></div>
    </div>

    <div class="subhead">Sicherheit und Suche</div>
    <div class="form-grid">
      <div class="field"><label for="securityToken">API-Token optional</label><input id="securityToken" type="password" autocomplete="new-password"></div>
      <div class="field"><label for="matchMinScore">Mindesttreffer Suche</label><input id="matchMinScore" type="number" min="0" max="1" step="0.01"></div>
      <div class="field"><label for="artistLimit">Kuenstler-Suchlimit</label><input id="artistLimit" type="number" min="1" max="500"></div>
      <div class="field"><label for="albumLimit">Album-Suchlimit</label><input id="albumLimit" type="number" min="1" max="500"></div>
    </div>

    <div class="actions" style="margin-top:18px">
      <div class="subhead" style="margin:0 auto 0 0">Player und Raeume</div>
      <button class="secondary" onclick="scanLmsPlayers()">LMS auslesen</button>
    </div>
    <div id="playersRows" class="rows"></div>

    <div class="actions" style="margin-top:18px">
      <div class="subhead" style="margin:0 auto 0 0">Eingabegeraete</div>
      <button class="secondary" onclick="addDeviceRow()">Geraet hinzufuegen</button>
    </div>
    <div id="devicesRows" class="rows"></div>

    <div id="advancedConfig" style="display:none; margin-top:18px">
      <div class="subhead">Erweiterte JSON-Konfiguration</div>
      <textarea id="configText" spellcheck="false"></textarea>
    </div>
  </section>
  <section>
    <div class="actions">
      <h2 style="margin-right:auto">Logs</h2>
      <button class="secondary" onclick="loadLogs()">Aktualisieren</button>
    </div>
    <pre id="logs">Noch keine Logs.</pre>
  </section>
  <section>
    <h2>Diagnose</h2>
    <pre id="diagnostics">Noch keine Daten.</pre>
  </section>
</main>
<script>
async function requestJson(url, options) {{
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok || data.status === 'error') {{
    throw new Error(data.message || data.detail || `HTTP ${{response.status}}`);
  }}
  return data;
}}

let currentConfig = {{}};
let advancedVisible = false;

function value(id) {{
  return document.getElementById(id).value.trim();
}}

function setValue(id, nextValue) {{
  document.getElementById(id).value = nextValue ?? '';
}}

function numberValue(id, fallback) {{
  const raw = value(id);
  if (raw === '') return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}}

async function loadAll() {{
  const [manifest, health, status] = await Promise.all([
    requestJson('./api/manifest').catch(error => ({{status: 'error', message: String(error)}})),
    requestJson('./api/health').catch(error => ({{status: 'error', message: String(error)}})),
    requestJson('./api/status').catch(error => ({{status: 'error', message: String(error)}})),
  ]);
  document.getElementById('versionBadge').textContent = `Add-on {ADDON_VERSION} | Dienst ${{manifest.tool_version || manifest.version || '-'}}`;
  renderStatus(status);
  document.getElementById('diagnostics').textContent = JSON.stringify({{manifest, health, status}}, null, 2);
}}

function renderStatus(status) {{
  const banner = document.getElementById('statusBanner');
  banner.className = status.status === 'ok' ? 'banner ok' : 'banner error';
  banner.textContent = status.status === 'ok' ? 'LMS Gateway ist erreichbar.' : (status.message || 'LMS Gateway meldet einen Fehler.');
  document.getElementById('tileLms').textContent = status.lms ? `${{status.lms.status}} ${{status.lms.host || ''}}:${{status.lms.http_port || ''}}` : '-';
  document.getElementById('tilePlayers').textContent = String(status.player_count ?? '-');
  document.getElementById('tileRooms').textContent = (status.rooms || []).join(', ') || '-';
  document.getElementById('tileConfig').textContent = status.config_path || '-';
}}

async function loadConfig() {{
  const data = await requestJson('./api/config');
  currentConfig = data.config || {{}};
  renderConfigForm();
}}

async function saveConfig() {{
  const message = document.getElementById('message');
  try {{
    const config = advancedVisible
      ? JSON.parse(document.getElementById('configText').value || '{{}}')
      : collectConfigForm();
    const data = await requestJson('./api/config', {{
      method: 'PUT',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{config}})
    }});
    currentConfig = config;
    renderConfigForm();
    message.textContent = data.message || 'Gespeichert.';
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
  }}
}}

function renderConfigForm() {{
  const cfg = currentConfig || {{}};
  const lms = cfg.lms || {{}};
  const gateway = cfg.gateway || {{}};
  const security = cfg.security || {{}};
  const dialog = cfg.dialog || {{}};
  const matching = cfg.matching || {{}};

  setValue('lmsHost', lms.host || '');
  setValue('lmsHttpPort', lms.http_port ?? 9000);
  setValue('lmsCliPort', lms.cli_port ?? 9090);
  setValue('lmsTimeout', lms.timeout_seconds ?? 8);
  setValue('dialogTtl', dialog.session_ttl_seconds ?? 180);
  setValue('gatewayHost', gateway.host || '0.0.0.0');
  setValue('gatewayPort', gateway.port ?? 8088);
  setValue('gatewayPublicUrl', gateway.public_url || '');
  setValue('securityToken', security.token || '');
  setValue('matchMinScore', matching.min_score ?? 0.55);
  setValue('artistLimit', matching.artist_limit ?? 100);
  setValue('albumLimit', matching.album_limit ?? 100);

  renderPlayers(cfg.players || {{}});
  renderDevices(cfg.devices || {{}});
  document.getElementById('configText').value = JSON.stringify(cfg, null, 2);
}}

function collectConfigForm() {{
  const cfg = structuredClone(currentConfig || {{}});
  cfg.lms = cfg.lms || {{}};
  cfg.gateway = cfg.gateway || {{}};
  cfg.security = cfg.security || {{}};
  cfg.dialog = cfg.dialog || {{}};
  cfg.matching = cfg.matching || {{}};

  cfg.lms.host = value('lmsHost');
  cfg.lms.http_port = numberValue('lmsHttpPort', 9000);
  cfg.lms.cli_port = numberValue('lmsCliPort', 9090);
  cfg.lms.timeout_seconds = numberValue('lmsTimeout', 8);
  cfg.gateway.host = value('gatewayHost') || '0.0.0.0';
  cfg.gateway.port = numberValue('gatewayPort', 8088);
  cfg.gateway.public_url = value('gatewayPublicUrl');
  cfg.security.token = value('securityToken');
  cfg.dialog.session_ttl_seconds = numberValue('dialogTtl', 180);
  cfg.matching.min_score = numberValue('matchMinScore', 0.55);
  cfg.matching.artist_limit = numberValue('artistLimit', 100);
  cfg.matching.album_limit = numberValue('albumLimit', 100);

  cfg.players = collectPlayers();
  cfg.devices = collectDevices();
  return cfg;
}}

function renderPlayers(players) {{
  const container = document.getElementById('playersRows');
  container.innerHTML = '';
  Object.entries(players).forEach(([room, player]) => addPlayerRow(room, player));
}}

function addPlayerRow(room = '', player = {{}}) {{
  const container = document.getElementById('playersRows');
  const row = document.createElement('div');
  row.className = 'row-card player-grid';
  row.innerHTML = `
    <div class="field"><label>Raum</label><input data-player-field="room"></div>
    <div class="field"><label>LMS Player-ID</label><input data-player-field="id"></div>
    <div class="field"><label>Anzeigename</label><input data-player-field="name"></div>
    <div class="field"><label>LMS Name</label><input data-player-field="lms_name"></div>
    <div class="field"><label>Aliasse kommagetrennt</label><input data-player-field="aliases"></div>
    <button class="danger" type="button">Entfernen</button>
  `;
  row.querySelector('[data-player-field="room"]').value = room;
  row.querySelector('[data-player-field="id"]').value = player.id || '';
  row.querySelector('[data-player-field="name"]').value = player.name || '';
  row.querySelector('[data-player-field="lms_name"]').value = player.lms_name || '';
  row.querySelector('[data-player-field="aliases"]').value = (player.aliases || []).join(', ');
  row.querySelector('button').onclick = () => row.remove();
  container.appendChild(row);
}}

function collectPlayers() {{
  const players = {{}};
  document.querySelectorAll('#playersRows .row-card').forEach(row => {{
    const room = row.querySelector('[data-player-field="room"]').value.trim();
    if (!room) return;
    const player = {{
      id: row.querySelector('[data-player-field="id"]').value.trim()
    }};
    const name = row.querySelector('[data-player-field="name"]').value.trim();
    const lmsName = row.querySelector('[data-player-field="lms_name"]').value.trim();
    const aliases = row.querySelector('[data-player-field="aliases"]').value
      .split(',')
      .map(item => item.trim())
      .filter(Boolean);
    if (name) player.name = name;
    if (lmsName) player.lms_name = lmsName;
    if (aliases.length) player.aliases = aliases;
    players[room] = player;
  }});
  return players;
}}

async function scanLmsPlayers() {{
  const message = document.getElementById('message');
  try {{
    const data = await requestJson('./api/actions/refresh_players', {{method: 'POST'}});
    const existing = collectPlayers();
    for (const lmsPlayer of data.players || []) {{
      const playerId = String(lmsPlayer.playerid || lmsPlayer.id || '').trim();
      const lmsName = String(lmsPlayer.name || lmsPlayer.player_name || lmsPlayer.playername || '').trim();
      if (!playerId && !lmsName) continue;
      const room = findRoomForLmsPlayer(existing, playerId, lmsName) || normalizeRoomName(lmsName || playerId);
      const current = existing[room] || {{}};
      existing[room] = {{
        ...current,
        id: playerId || current.id || '',
        name: current.name || lmsName || room,
        lms_name: lmsName || current.lms_name || ''
      }};
    }}
    currentConfig.players = existing;
    renderPlayers(existing);
    message.textContent = data.message || 'LMS-Player aktualisiert.';
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
  }}
}}

function findRoomForLmsPlayer(players, playerId, lmsName) {{
  const normalizedName = normalizeRoomName(lmsName);
  for (const [room, player] of Object.entries(players)) {{
    if (playerId && String(player.id || '').trim().toLowerCase() === playerId.toLowerCase()) return room;
    if (normalizedName && normalizeRoomName(player.lms_name || player.name || room) === normalizedName) return room;
  }}
  return '';
}}

function normalizeRoomName(value) {{
  return String(value || '')
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\\s+/g, ' ');
}}

function renderDevices(devices) {{
  const container = document.getElementById('devicesRows');
  container.innerHTML = '';
  Object.entries(devices).forEach(([device, config]) => addDeviceRow(device, config));
}}

function addDeviceRow(device = '', config = {{}}) {{
  const container = document.getElementById('devicesRows');
  const row = document.createElement('div');
  row.className = 'row-card device-grid';
  row.innerHTML = `
    <div class="field"><label>Geraet oder Quelle</label><input data-device-field="device"></div>
    <div class="field"><label>Standardraum</label><input data-device-field="default_room"></div>
    <button class="danger" type="button">Entfernen</button>
  `;
  row.querySelector('[data-device-field="device"]').value = device;
  row.querySelector('[data-device-field="default_room"]').value = config.default_room || '';
  row.querySelector('button').onclick = () => row.remove();
  container.appendChild(row);
}}

function collectDevices() {{
  const devices = {{}};
  document.querySelectorAll('#devicesRows .row-card').forEach(row => {{
    const device = row.querySelector('[data-device-field="device"]').value.trim();
    if (!device) return;
    const defaultRoom = row.querySelector('[data-device-field="default_room"]').value.trim();
    devices[device] = defaultRoom ? {{default_room: defaultRoom}} : {{}};
  }});
  return devices;
}}

function toggleAdvanced() {{
  advancedVisible = !advancedVisible;
  const panel = document.getElementById('advancedConfig');
  panel.style.display = advancedVisible ? 'block' : 'none';
  if (advancedVisible) {{
    document.getElementById('configText').value = JSON.stringify(collectConfigForm(), null, 2);
  }}
}}

async function runAction(action) {{
  const message = document.getElementById('message');
  try {{
    const data = await requestJson(`./api/actions/${{action}}`, {{method: 'POST'}});
    message.textContent = data.message || JSON.stringify(data);
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
  }}
}}

function runCritical(action) {{
  if (confirm(`Aktion wirklich ausfuehren: ${{action}}?`)) runAction(action);
}}

async function loadLogs() {{
  const data = await requestJson('./api/logs/recent');
  document.getElementById('logs').textContent = (data.lines || []).join('\\n') || 'Keine Logs.';
}}

loadAll();
loadConfig().catch(() => {{}});
loadLogs().catch(() => {{}});
setInterval(loadAll, 10000);
setInterval(loadLogs, 4000);
</script>
</body>
</html>"""
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.write_html(render_page())
            return
        if self.path.startswith("/api/"):
            self.proxy_api("GET", self.path.removeprefix("/api/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def do_POST(self) -> None:
        if self.path.startswith("/api/"):
            self.proxy_api("POST", self.path.removeprefix("/api/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def do_PUT(self) -> None:
        if self.path.startswith("/api/"):
            self.proxy_api("PUT", self.path.removeprefix("/api/"))
            return
        self.write_json(404, {"status": "error", "message": "not found"})

    def proxy_api(self, method: str, path: str) -> None:
        payload = None
        if method in {"POST", "PUT"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw or "{}")
        self.write_json(*tool_request(method, path, payload))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", INGRESS_PORT))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"LMS Gateway Control listening on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
