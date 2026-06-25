"""
PyWebView desktop UI for the MyRacingData telemetry client.

A frameless, branded (Pit Wall) window rendering an HTML/CSS UI, with the Python
capture engine behind it. The JS calls into the `Api` object (start/stop/login,
state polling); the engine is unchanged. Falls back to the legacy tkinter UI in
main.py if pywebview isn't available.
"""

import logging

import requests
import urllib3
import webview

from config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class Api:
    """Bridge exposed to the web UI (window.pywebview.api.*)."""

    def __init__(self, app):
        self.app = app          # TelemetryCapture

    # --- state ---
    def get_state(self):
        return self.app.ui_state()

    # --- capture control ---
    def start_capture(self):
        try:
            ok = self.app.start()
            return {'ok': bool(ok)}
        except Exception as e:
            logger.exception('start_capture failed')
            return {'ok': False, 'error': str(e)}

    def stop_capture(self):
        try:
            self.app.stop()
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # --- account / API key ---
    def get_api_key(self):
        return self.app.config.api_key or ''

    def save_api_key(self, key):
        key = (key or '').strip()
        if not key:
            return {'ok': False, 'error': 'Please enter your API key'}
        try:
            r = requests.get(
                f"{self.app.config.api_url}/users/me",
                headers={'Authorization': f'Bearer {key}'},
                timeout=10, verify=False,
            )
            if r.status_code == 200:
                self.app.config.set('api_key', key)
                u = r.json()
                return {'ok': True, 'name': u.get('name', 'Driver'), 'email': u.get('email', '')}
            return {'ok': False, 'error': 'Invalid API key'}
        except Exception as e:
            return {'ok': False, 'error': f'Could not reach server'}

    # --- updates ---
    def check_update(self):
        try:
            from updater import check_for_update
            return check_for_update(Config.VERSION)
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def apply_update(self):
        try:
            from updater import download_and_apply
            return download_and_apply()
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # --- window controls (frameless) ---
    def minimize(self):
        if webview.windows:
            webview.windows[0].minimize()

    def close(self):
        if webview.windows:
            webview.windows[0].destroy()


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');
  :root{
    --midnight:#0A0A0F; --charcoal:#1E1E24; --graphite:#4B5563; --steel:#9CA3AF;
    --red:#E31E24; --cyan:#00D9FF; --green:#00FF88; --white:#F5F5F7;
    --mono:'JetBrains Mono',monospace; --sans:'Inter',system-ui,sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{background:var(--midnight);color:var(--white);font-family:var(--sans);
       user-select:none;overflow:hidden}
  /* titlebar */
  .titlebar{height:38px;display:flex;align-items:center;justify-content:space-between;
            padding:0 6px 0 14px;background:#0d0d12;border-bottom:1px solid var(--charcoal)}
  .pywebview-drag-region{flex:1;height:100%;display:flex;align-items:center;gap:8px;cursor:default}
  .brand{display:flex;align-items:center;gap:8px;font-weight:700;letter-spacing:.5px;font-size:13px}
  .diamond{width:14px;height:14px;background:var(--red);transform:rotate(45deg);border-radius:2px}
  .winbtns button{width:30px;height:26px;background:transparent;border:0;color:var(--steel);
                  font-size:14px;cursor:pointer;border-radius:5px}
  .winbtns button:hover{background:var(--charcoal);color:var(--white)}
  .winbtns .x:hover{background:var(--red);color:#fff}
  .wrap{padding:18px 18px 14px}
  /* status */
  .status{display:flex;align-items:center;gap:9px;font-family:var(--mono);font-size:12px;
          text-transform:uppercase;letter-spacing:2px;color:var(--steel);margin-bottom:4px}
  .dot{width:9px;height:9px;border-radius:50%;background:var(--graphite)}
  .dot.on{background:var(--green);box-shadow:0 0 10px var(--green)}
  .dot.live{background:var(--red);box-shadow:0 0 10px var(--red);animation:pulse 1.2s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
  .sim{font-size:16px;font-weight:600;margin-bottom:2px}
  .carline{font-family:var(--mono);font-size:12px;color:var(--steel);margin-bottom:14px;min-height:15px}
  /* readouts */
  .readouts{display:grid;grid-template-columns:1.4fr .8fr .6fr;gap:10px;
            background:var(--charcoal);border:1px solid var(--graphite);border-radius:12px;
            padding:14px 16px;margin-bottom:12px}
  .ro{display:flex;flex-direction:column}
  .ro .v{font-family:var(--mono);font-weight:700;line-height:1}
  .ro.big .v{font-size:40px;color:var(--cyan)}
  .ro .v.mid{font-size:26px}
  .ro .l{font-family:var(--mono);font-size:10px;letter-spacing:2px;color:var(--steel);
         text-transform:uppercase;margin-top:5px}
  /* bars */
  .bars{margin-bottom:14px}
  .bar{display:flex;align-items:center;gap:10px;margin-bottom:7px}
  .bar .t{width:34px;font-family:var(--mono);font-size:10px;letter-spacing:1px;color:var(--steel)}
  .track{flex:1;height:9px;background:var(--charcoal);border-radius:6px;overflow:hidden}
  .fill{height:100%;width:0;border-radius:6px;transition:width .08s linear}
  .fill.thr{background:var(--green)} .fill.brk{background:var(--red)}
  .bar .pv{width:34px;text-align:right;font-family:var(--mono);font-size:11px;color:var(--steel)}
  .meta{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;
        color:var(--steel);margin-bottom:16px}
  /* button */
  .btn{width:100%;padding:14px;border:0;border-radius:12px;font-weight:700;font-size:15px;
       letter-spacing:1px;text-transform:uppercase;cursor:pointer;transition:.15s;font-family:var(--sans)}
  .btn.go{background:var(--red);color:#fff} .btn.go:hover{background:#ff2a30}
  .btn.stop{background:var(--charcoal);color:var(--white);border:1px solid var(--graphite)}
  .btn.stop:hover{border-color:var(--red);color:var(--red)}
  /* footer */
  .footer{display:flex;justify-content:space-between;align-items:center;margin-top:14px;
          font-family:var(--mono);font-size:10px;color:var(--graphite)}
  .footer a{color:var(--cyan);cursor:pointer;text-decoration:none}
  /* login */
  .login{padding:6px 0}
  .login h2{font-size:18px;margin-bottom:6px}
  .login p{color:var(--steel);font-size:13px;margin-bottom:16px;line-height:1.5}
  .login input{width:100%;padding:12px 14px;background:var(--midnight);border:1px solid var(--graphite);
               border-radius:10px;color:var(--white);font-family:var(--mono);font-size:12px;margin-bottom:10px}
  .login input:focus{outline:0;border-color:var(--red)}
  .err{color:var(--red);font-size:12px;font-family:var(--mono);min-height:16px;margin-bottom:8px}
  .hide{display:none!important}
</style>
</head>
<body>
  <div class="titlebar">
    <div class="pywebview-drag-region">
      <span class="brand"><span class="diamond"></span>MYRACINGDATA</span>
    </div>
    <div class="winbtns">
      <button onclick="api.minimize()">&#8211;</button>
      <button class="x" onclick="api.close()">&#10005;</button>
    </div>
  </div>

  <!-- LOGIN -->
  <div class="wrap login hide" id="login">
    <h2>Connect your account</h2>
    <p>Paste your API key from <b>myracingdata.com</b> &rarr; Profile &rarr; API Keys.</p>
    <input id="key" type="text" placeholder="race_..." spellcheck="false" autocomplete="off">
    <div class="err" id="loginErr"></div>
    <button class="btn go" onclick="saveKey()">Connect</button>
  </div>

  <!-- MAIN -->
  <div class="wrap hide" id="main">
    <div class="status"><span class="dot" id="dot"></span><span id="statusText">Idle</span></div>
    <div class="sim" id="sim">Waiting for a sim…</div>
    <div class="carline" id="carline"></div>

    <div class="readouts">
      <div class="ro big"><span class="v" id="speed">0</span><span class="l">km/h</span></div>
      <div class="ro"><span class="v mid" id="rpm">0</span><span class="l">rpm</span></div>
      <div class="ro"><span class="v mid" id="gear">N</span><span class="l">gear</span></div>
    </div>

    <div class="bars">
      <div class="bar"><span class="t">THR</span><div class="track"><div class="fill thr" id="thrFill"></div></div><span class="pv" id="thrVal">0</span></div>
      <div class="bar"><span class="t">BRK</span><div class="track"><div class="fill brk" id="brkFill"></div></div><span class="pv" id="brkVal">0</span></div>
    </div>

    <div class="meta"><span id="rateText">120 Hz</span><span id="samplesText">0 samples</span></div>

    <button class="btn go" id="actionBtn" onclick="toggle()">Start Capture</button>

    <div class="footer">
      <span id="verText">v—</span>
      <span id="updateText"></span>
    </div>
  </div>

<script>
  let api = null, running = false;

  function $(id){return document.getElementById(id)}

  window.addEventListener('pywebviewready', async () => {
    api = window.pywebview.api;
    const key = await api.get_api_key();
    if (key) { show('main'); } else { show('login'); }
    poll();
    setInterval(poll, 200);
    checkUpdate();
  });

  function show(which){
    $('login').classList.toggle('hide', which !== 'login');
    $('main').classList.toggle('hide', which !== 'main');
    if (which === 'main') setTimeout(()=>$('key') && ($('key').value=''), 0);
  }

  async function saveKey(){
    $('loginErr').textContent = '';
    const r = await api.save_api_key($('key').value);
    if (r.ok) { show('main'); } else { $('loginErr').textContent = r.error || 'Failed'; }
  }

  async function toggle(){
    if (!running) {
      $('actionBtn').textContent = 'Starting…';
      const r = await api.start_capture();
      if (!r.ok) { $('actionBtn').textContent = 'Start Capture'; alert(r.error||'Could not start'); }
    } else {
      await api.stop_capture();
    }
  }

  async function poll(){
    if (!api) return;
    let s;
    try { s = await api.get_state(); } catch(e){ return; }
    if (!s) return;
    running = s.running;
    $('verText').textContent = 'v' + s.version;
    $('rateText').textContent = s.hz + ' Hz';
    $('samplesText').textContent = (s.data_count||0).toLocaleString() + ' samples';

    const dot = $('dot');
    dot.className = 'dot' + (s.running && s.connected ? (s.game ? ' live' : ' on') : '');
    $('statusText').textContent = !s.running ? 'Idle'
        : (s.connected ? (s.game ? 'Capturing · Live' : 'Connected · waiting for sim') : 'Connecting…');
    $('sim').textContent = s.game ? s.game_label : (s.running ? 'Waiting for a sim…' : 'Not capturing');
    $('carline').textContent = s.session_id && s.running ? ('Lap ' + (s.lap||0)) : '';

    $('speed').textContent = Math.round(s.speed||0);
    $('rpm').textContent = (s.rpm||0).toLocaleString();
    $('gear').textContent = (s.gear>0? s.gear : (s.gear===0?'N':'R'));
    setBar('thr', s.throttle||0); setBar('brk', s.brake||0);

    const b = $('actionBtn');
    b.textContent = running ? 'Stop Capture' : 'Start Capture';
    b.className = 'btn ' + (running ? 'stop' : 'go');
  }

  function setBar(which, v){
    v = Math.max(0, Math.min(100, v));
    $(which+'Fill').style.width = v + '%';
    $(which+'Val').textContent = Math.round(v);
  }

  async function checkUpdate(){
    try{
      const u = await api.check_update();
      if (u && u.available){
        $('updateText').innerHTML = '<a onclick="applyUpdate()">Update to ' + u.version + ' ↻</a>';
      } else { $('updateText').textContent = 'up to date'; }
    }catch(e){ $('updateText').textContent=''; }
  }
  async function applyUpdate(){
    $('updateText').textContent = 'updating…';
    const r = await api.apply_update();
    if (!r.ok) $('updateText').textContent = 'update failed';
  }
</script>
</body>
</html>"""


def run_webview(app):
    """Launch the desktop UI. Returns False if webview can't start (caller falls back)."""
    api = Api(app)
    webview.create_window(
        'MyRacingData',
        html=HTML,
        js_api=api,
        width=440,
        height=640,
        resizable=False,
        frameless=True,
        easy_drag=False,
        background_color='#0A0A0F',
    )
    webview.start()
    return True
