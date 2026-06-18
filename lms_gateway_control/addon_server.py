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
ADDON_VERSION = "0.1.0"


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
    button {{ border: 0; border-radius: 6px; background: #2563eb; color: white; padding: 9px 13px; font: inherit; cursor: pointer; }}
    button.secondary {{ background: #52606d; }}
    button.danger {{ background: #b42318; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #d8e0e8; border-radius: 6px; padding: 12px; max-height: 300px; overflow: auto; }}
    #message {{ min-height: 22px; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #11161c; color: #e6edf3; }}
      section, textarea {{ background: #171d24; color: #e6edf3; border-color: #344250; }}
      .tile, pre {{ background: #111820; border-color: #344250; }}
      .label {{ color: #aab6c2; }}
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
    </div>
    <textarea id="configText" spellcheck="false"></textarea>
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
  document.getElementById('configText').value = JSON.stringify(data.config || {{}}, null, 2);
}}

async function saveConfig() {{
  const message = document.getElementById('message');
  try {{
    const config = JSON.parse(document.getElementById('configText').value || '{{}}');
    const data = await requestJson('./api/config', {{
      method: 'PUT',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{config}})
    }});
    message.textContent = data.message || 'Gespeichert.';
    await loadAll();
  }} catch (error) {{
    message.textContent = error.message;
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
