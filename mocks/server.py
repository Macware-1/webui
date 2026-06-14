#!/usr/bin/env python3
"""
CAN-ETH Gateway — mock backend server for web UI development.

Runs as a drop-in replacement for the firmware's HTTP API so the Vue
frontend can be developed on any machine without physical hardware.

Run with Docker (recommended — no Python install needed):
    cd webui && docker compose up

Run directly (needs: pip install -r mocks/requirements.txt):
    python3 mocks/server.py

Then in a second terminal start the Vue dev server:
    cd webui && npm run dev
    → open http://localhost:5173

Vite proxies /api/* to this server (port 3001) automatically.
"""

import json
import math
import threading
import time

import msgpack
from flask import Flask, Response, jsonify, request

PORT = 3001
app  = Flask(__name__)

# ── In-memory state ───────────────────────────────────────────────────────────

_reboot_until = 0.0          # epoch time until which /api/info returns 503
_reboot_lock  = threading.Lock()

RULE_SLOTS = [f'r{i}' for i in range(8)]

def _make_rule():
    return {'can_id': 0, 'mask': 0x1FFFFFFF, 'remap_id': 0,
            'action': 0, 'rflags': 0, 'rdlc': 0, 'rpayload': [0]*8}

_cfg = {
    'board': {
        'eth_ip':     [10, 104, 3, 64],
        'eth_mask':   [255, 255, 255, 0],
        'eth_gw':     [10, 104, 3, 1],
        'usb_ip':     [192, 168, 7, 64],
        'ptp_enable': 0,
    },
    'can': {
        'dlc': 8, 'id': 0, 'j1939': 1,
        'nbrp': 4,  'ntseg1': 59, 'ntseg2': 20, 'nsjw': 20,
        'dbrp': 2,  'dtseg1': 15, 'dtseg2':  4, 'dsjw':  4,
        'fd_mode': 1, 'brs': 1,
    },
    'usb':     {'usbmode': 1},
    'logging': {
        'ch1': {'enabled': 1, 'logging_id': 0, 'target': 1},
        'ch2': {'enabled': 0, 'logging_id': 0, 'target': 0},
    },
    'filters': {s: _make_rule() for s in RULE_SLOTS},
}
_cfg_lock = threading.Lock()

_dtc_list = [
    {'spn': 100, 'fmi': 3, 'count': 2, 'desc': 'Voltage high', 'ecu': '0x00'},
]
_node_list = [{'addr': '0x80'}, {'addr': '0x00'}]

_radxa = {
    'alive':       True,
    'heartbeat':   0,
    'status':      0x03,       # BOOT_OK | WIFI_READY
    'version':     '1.0.0',
    'uptime':      0,
    'wifi_status': 2,          # CONNECTED
    'wifi_ip':     '192.168.4.55',
    'wifi_rssi':   -62,
    'wifi_enable': True,
    'wifi_ssid':   'MockNetwork',
    'data_enable': False,
    'dest_ip':     '192.168.1.100',
    'dest_port':   47808,
    'pkts_fwd':    0,
    'pkts_drop':   0,
}
_radxa_lock = threading.Lock()

# ── Telemetry simulation ──────────────────────────────────────────────────────

_sim = {
    't': 0.0, 'rpm': 1200.0, 'dir': 1.0,
    'speed': 0.0, 'fuel': 74.5, 'temp': 82.0, 'volt': 13.8,
    'load': 0.0,
}
_sim_lock = threading.Lock()

def _sim_loop():
    _hb_tick = 0
    while True:
        with _sim_lock:
            _sim['t']    += 0.1
            _sim['rpm']  += _sim['dir'] * 12
            if _sim['rpm'] > 2400: _sim['dir'] = -1.0
            if _sim['rpm'] <  800: _sim['dir'] =  1.0
            _sim['speed'] = max(0.0, (_sim['rpm'] - 900) / 13.0)
            _sim['load']  = min(100.0, max(0.0, (_sim['rpm'] - 700) / 17.0))
            _sim['temp']  = 85.0 + math.sin(_sim['t'] * 0.07) * 6.0
            _sim['fuel']  = max(0.0, _sim['fuel'] - 0.0008)
            _sim['volt']  = 13.8 + math.sin(_sim['t'] * 0.25) * 0.4
        _hb_tick += 1
        if _hb_tick >= 10:   # every ~1 s
            _hb_tick = 0
            with _radxa_lock:
                _radxa['heartbeat'] = (_radxa['heartbeat'] + 1) & 0xFF
                _radxa['uptime']    = int(time.monotonic() - _start)
                _radxa['wifi_rssi'] = -60 + int(math.sin(time.monotonic() * 0.2) * 8)
                if _radxa['data_enable']:
                    _radxa['pkts_fwd'] += 12
        time.sleep(0.1)

threading.Thread(target=_sim_loop, daemon=True).start()

# ── Helpers ───────────────────────────────────────────────────────────────────

_start = time.monotonic()

def _uptime():
    return int(time.monotonic() - _start)

def _r(v, d):
    return round(v, d)

def _reboot(delay=2.0):
    with _reboot_lock:
        global _reboot_until
        _reboot_until = time.time() + delay
    def _log():
        time.sleep(delay)
        print('[mock] reboot complete')
    threading.Thread(target=_log, daemon=True).start()

def _is_rebooting():
    with _reboot_lock:
        return time.time() < _reboot_until

def _hex32(s, default=0):
    try:
        return int(str(s), 16) & 0xFFFFFFFF
    except (ValueError, TypeError):
        return default

def _hex_bytes(s):
    s = s or ''
    out = [int(s[i:i+2], 16) for i in range(0, min(len(s), 16), 2)
           if len(s[i:i+2]) == 2]
    return (out + [0]*8)[:8]

# ── CORS ──────────────────────────────────────────────────────────────────────

@app.after_request
def _cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

@app.route('/api/<path:_>', methods=['OPTIONS'])
def _options(_):
    return Response(status=204)

# ── GET /api/info ─────────────────────────────────────────────────────────────

@app.get('/api/info')
def api_info():
    if _is_rebooting():
        return Response(status=503)
    with _cfg_lock:
        ip = '.'.join(map(str, _cfg['board']['eth_ip']))
        gw = '.'.join(map(str, _cfg['board']['eth_gw']))
    return jsonify({
        'ip': ip, 'mac': '02:00:00:00:00:01', 'gateway': gw,
        'phy': 'LAN8742A', 'link_up': True,
        'speed': '100 Mbps', 'duplex': 'Full', 'clock': '64 MHz',
        'heap': 31744, 'tasks': 8, 'uptimeSec': _uptime(),
    })

# ── GET /api/telemetry ────────────────────────────────────────────────────────

@app.get('/api/telemetry')
def api_telemetry():
    with _sim_lock:
        s = dict(_sim)
    return jsonify({
        'engine_speed':    _r(s['rpm'],   1),
        'vehicle_speed':   _r(s['speed'], 1),
        'fuel_level':      _r(s['fuel'],  1),
        'engine_load':     _r(s['load'],  1),
        'coolant_temp':    _r(s['temp'],  1),
        'battery_voltage': _r(s['volt'],  2),
        'throttle_pct':    _r(s['load'],  1),
        'status': {
            'engine_running': s['rpm'] > 500,
            'brake': False, 'pto': False, 'cruise': False,
        },
    })

# ── GET /api/dtc ──────────────────────────────────────────────────────────────

@app.get('/api/dtc')
def api_dtc():
    return jsonify({
        'red_stop_lamp':   any(d['fmi'] <= 4 for d in _dtc_list),
        'amber_warn_lamp': any(d['fmi'] >  4 for d in _dtc_list),
        'active': _dtc_list,
    })

# ── GET /api/nodes ────────────────────────────────────────────────────────────

@app.get('/api/nodes')
def api_nodes():
    return jsonify({'count': len(_node_list), 'nodes': _node_list})

# ── GET /api/can/config ───────────────────────────────────────────────────────

@app.get('/api/can/config')
def api_can_config():
    with _cfg_lock:
        j      = _cfg['can']['j1939']
        active = sum(1 for s in RULE_SLOTS if _cfg['filters'][s]['action'] != 0)
    return jsonify({'j1939_mode': j, 'filter_count': active})

# ── GET /api/can/mode?mode=raw|j1939 ─────────────────────────────────────────

@app.get('/api/can/mode')
def api_can_mode():
    mode = request.args.get('mode', '')
    with _cfg_lock:
        if   mode == 'j1939': _cfg['can']['j1939'] = 1
        elif mode == 'raw':   _cfg['can']['j1939'] = 0
        j = _cfg['can']['j1939']
    return jsonify({'status': 'ok', 'j1939_mode': j})

# ── GET /api/can/filters ──────────────────────────────────────────────────────

@app.get('/api/can/filters')
def api_can_filters():
    rules = []
    with _cfg_lock:
        for i, slot in enumerate(RULE_SLOTS):
            r = _cfg['filters'][slot]
            if r['action'] == 0:
                continue
            e = {
                'idx':    i,
                'can_id': f"0x{r['can_id'] & 0xFFFFFFFF:08X}",
                'mask':   f"0x{r['mask']   & 0xFFFFFFFF:08X}",
                'action': r['action'],
            }
            if r['action'] == 2:
                e['remap_flags'] = r['rflags']
                if r['rflags'] & 1:
                    e['remap_id'] = f"0x{r['remap_id'] & 0xFFFFFFFF:08X}"
                if r['rflags'] & 2:
                    e['remap_dlc']  = r['rdlc']
                    e['remap_data'] = ''.join(f'{b:02X}' for b in r['rpayload'])
            rules.append(e)
    return jsonify({'count': len(rules), 'rules': rules})

# ── GET /api/can/filter/set ───────────────────────────────────────────────────

@app.get('/api/can/filter/set')
def api_can_filter_set():
    try:
        idx = int(request.args['idx'])
    except (KeyError, ValueError):
        return jsonify({'status': 'error', 'msg': 'missing idx'})
    if not 0 <= idx < len(RULE_SLOTS):
        return jsonify({'status': 'error', 'msg': 'idx out of range'})
    try:
        action = int(request.args['action'])
    except (KeyError, ValueError):
        return jsonify({'status': 'error', 'msg': 'missing action'})
    if action not in (1, 2):
        return jsonify({'status': 'error', 'msg': 'invalid action'})

    rule = {
        'can_id':   _hex32(request.args.get('can_id', '0')),
        'mask':     _hex32(request.args.get('mask',   '1FFFFFFF'), 0x1FFFFFFF),
        'remap_id': _hex32(request.args.get('remap_id', '0')),
        'action':   action,
        'rflags':   (1 if 'remap_id'   in request.args else 0) |
                    (2 if 'remap_data' in request.args else 0),
        'rdlc':     int(request.args.get('remap_dlc', 0) or 0),
        'rpayload': _hex_bytes(request.args.get('remap_data', '')),
    }
    with _cfg_lock:
        _cfg['filters'][RULE_SLOTS[idx]] = rule
    print(f'[mock] filter set  idx={idx}  action={action}')
    return jsonify({'status': 'ok', 'idx': idx})

# ── GET /api/can/filter/clear?idx=N ──────────────────────────────────────────

@app.get('/api/can/filter/clear')
def api_can_filter_clear():
    try:
        idx = int(request.args['idx'])
    except (KeyError, ValueError):
        return jsonify({'status': 'error', 'msg': 'missing idx'})
    if not 0 <= idx < len(RULE_SLOTS):
        return jsonify({'status': 'error', 'msg': 'idx out of range'})
    with _cfg_lock:
        _cfg['filters'][RULE_SLOTS[idx]] = _make_rule()
    return jsonify({'status': 'ok', 'idx': idx})

# ── GET /api/can/filter/clear_all ────────────────────────────────────────────

@app.get('/api/can/filter/clear_all')
def api_can_filter_clear_all():
    with _cfg_lock:
        for s in RULE_SLOTS:
            _cfg['filters'][s] = _make_rule()
    return jsonify({'status': 'ok'})

# ── GET /api/config/values  →  msgpack binary ─────────────────────────────────

@app.get('/api/config/values')
def api_config_values():
    with _cfg_lock:
        data = msgpack.packb(_cfg, use_bin_type=True)
    return Response(data, mimetype='application/octet-stream')

# ── POST /api/sendconfig  (msgpack body) ──────────────────────────────────────

@app.post('/api/sendconfig')
def api_sendconfig():
    body = request.data
    if not body:
        return jsonify({'status': 'error', 'msg': 'empty body'})
    try:
        decoded = msgpack.unpackb(body, raw=False)
    except Exception:
        return jsonify({'status': 'error', 'msg': 'bad msgpack'})
    with _cfg_lock:
        for key in ('board', 'can', 'usb', 'logging', 'filters'):
            if key in decoded:
                _cfg[key].update(decoded[key])
    print('[mock] config saved')
    _reboot(2.0)
    return jsonify({'status': 'ok', 'msg': 'Saved. Rebooting in 300 ms.'})

# ── POST /api/send/can ────────────────────────────────────────────────────────

@app.post('/api/send/can')
def api_send_can():
    body = request.get_json(silent=True) or {}
    can_id = body.get('id')
    if not can_id:
        return jsonify({'status': 'error', 'msg': 'missing id'})
    data = (body.get('data') or '').replace(' ', '')
    dlc  = len(data) // 2
    print(f"[mock] CAN TX  id={can_id}  dlc={dlc}  data={data}  "
          f"fd={body.get('fd')}  brs={body.get('brs')}")
    return jsonify({'status': 'ok', 'dlc': dlc})

# ── GET /api/radxa ────────────────────────────────────────────────────────────

@app.get('/api/radxa')
def api_radxa():
    with _radxa_lock:
        return jsonify(dict(_radxa))

# ── POST /api/radxa/wifi ──────────────────────────────────────────────────────

@app.post('/api/radxa/wifi')
def api_radxa_wifi():
    body = request.get_json(silent=True) or {}
    with _radxa_lock:
        if 'enable' in body:
            _radxa['wifi_enable'] = bool(body['enable'])
        if 'ssid' in body and body['ssid']:
            _radxa['wifi_ssid']   = body['ssid']
            _radxa['wifi_status'] = 1   # connecting
            def _connect():
                time.sleep(3)
                with _radxa_lock:
                    _radxa['wifi_status'] = 2   # connected
                    _radxa['wifi_ip']     = '192.168.4.55'
            threading.Thread(target=_connect, daemon=True).start()
    print(f"[mock] radxa wifi  enable={body.get('enable')}  ssid={body.get('ssid','')}")
    return jsonify({'status': 'ok'})

# ── POST /api/radxa/data ──────────────────────────────────────────────────────

@app.post('/api/radxa/data')
def api_radxa_data():
    body = request.get_json(silent=True) or {}
    with _radxa_lock:
        if 'enable'    in body: _radxa['data_enable'] = bool(body['enable'])
        if 'dest_ip'   in body: _radxa['dest_ip']     = body['dest_ip']
        if 'dest_port' in body: _radxa['dest_port']   = int(body['dest_port'])
        if _radxa['data_enable']:
            _radxa['status'] |= 0x04
        else:
            _radxa['status'] &= ~0x04
    print(f"[mock] radxa data  enable={body.get('enable')}  "
          f"ip={body.get('dest_ip','')}:{body.get('dest_port','')}")
    return jsonify({'status': 'ok'})

# ── POST /api/radxa/reboot ────────────────────────────────────────────────────

@app.post('/api/radxa/reboot')
def api_radxa_reboot():
    def _do_reboot():
        with _radxa_lock:
            _radxa['alive'] = False
        time.sleep(8)
        with _radxa_lock:
            _radxa['alive']       = True
            _radxa['heartbeat']   = 0
            _radxa['uptime']      = 0
            _radxa['wifi_status'] = 2
    threading.Thread(target=_do_reboot, daemon=True).start()
    print('[mock] radxa reboot requested')
    return jsonify({'status': 'ok'})

# ── POST /api/bootloader ──────────────────────────────────────────────────────

@app.post('/api/bootloader')
def api_bootloader():
    print('[mock] bootloader requested — simulating 3-second reboot')
    _reboot(3.0)
    return jsonify({'status': 'ok', 'message': 'Entering bootloader in 200 ms'})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('╔══════════════════════════════════════════════════╗')
    print('║  CAN-ETH Gateway — mock backend (Python/Flask)  ║')
    print(f'║  Listening on http://localhost:{PORT}               ║')
    print('║                                                  ║')
    print('║  Recommended: use Docker (see docker-compose.yml)║')
    print('║    cd webui && docker compose up                 ║')
    print('║                                                  ║')
    print('║  Or run directly (pip install -r requirements.txt║')
    print('║    python3 mocks/server.py                       ║')
    print('║                                                  ║')
    print('║  Then: cd webui && npm run dev                   ║')
    print('║  Open:  http://localhost:5173                    ║')
    print('╚══════════════════════════════════════════════════╝')
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
