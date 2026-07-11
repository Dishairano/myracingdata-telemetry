"""
Synthetic ACC drive — full-pipeline test without a rig.

Builds real ACCPhysics/ACCGraphics struct BYTES for a simulated multi-lap drive
and feeds them through the UNMODIFIED reader (`ACCSharedMemoryReader.read()`,
via BytesIO stand-ins for the shared-memory maps), the real `normalize('acc')`,
and the real `WebSocketClient` (?key= auth) against a live backend — so struct
layout parsing, normalization, WS auth, batching, backend lap/sector derivation
and everything downstream (pit wall, corners, AI debrief) get exercised.

What it can NOT prove: the byte layout of the real game on Windows, the UI,
packaging. That stays on the rig.

Usage:
  python3 scripts/synthetic_acc_drive.py --email <acct> --password <pw> \
      [--api https://myracingdata.com/api/v1] [--laps 4] [--hz 60]
"""

import argparse
import ctypes
import io
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import requests
from games.acc_structs import ACCPhysics, ACCGraphics
from games.acc_shared_memory import ACCSharedMemoryReader
from capture.canonical import normalize
from network.websocket_client import WebSocketClient


# ---------------------------------------------------------------- fake memory

class SyntheticACCReader(ACCSharedMemoryReader):
    """The real reader, with BytesIO standing in for the Windows shared maps."""

    def __init__(self, car, track):
        super().__init__()
        self.car_name = car
        self.track_name = track
        self.pit_window_start = 0
        self.pit_window_end = 0
        self.connected = True

    def push(self, phys: ACCPhysics, gfx: ACCGraphics):
        # Same bytes the game would put in shared memory; parent read() does
        # seek(0) + read(n) + from_buffer_copy on these exactly as on Windows.
        self.physics_map = io.BytesIO(bytes(phys))
        self.graphics_map = io.BytesIO(bytes(gfx))


# ---------------------------------------------------------------- drive model

TRACK_LEN = 4000.0        # metres
VMAX = 238.0              # km/h on the straights
CORNERS = [               # (position 0..1, apex km/h, width as fraction of lap)
    (0.05, 66, 0.016), (0.18, 122, 0.020), (0.33, 96, 0.018),
    (0.45, 142, 0.022), (0.58, 108, 0.018), (0.72, 168, 0.024), (0.90, 58, 0.015),
]

def corner_speed_profile(pos, lap_deltas):
    """Target speed at normalized position (Gaussian dips at each corner)."""
    v = VMAX
    for i, (c, apex, w) in enumerate(CORNERS):
        d = min(abs(pos - c), abs(pos - c + 1), abs(pos - c - 1))
        v -= (VMAX - (apex + lap_deltas[i])) * math.exp(-((d / w) ** 2))
    return max(35.0, v)


def lap_corner_deltas(lap_no, rng):
    """Per-corner apex-speed offsets: out-lap slow, lap 3 the clean one."""
    if lap_no == 0:
        return [-16 - rng.uniform(0, 8) for _ in CORNERS]      # cautious out-lap
    if lap_no == 2:
        return [rng.uniform(-1, 1.5) for _ in CORNERS]         # the good lap
    return [rng.uniform(-9, 1) for _ in CORNERS]               # human scatter


# ---------------------------------------------------------------- struct fill

def fill_structs(p, g, st):
    """Write one tick of the drive state into the real ctypes structs."""
    v = st['v']
    p.packetId = st['packet']
    p.gas = st['gas']
    p.brake = st['brake']
    p.fuel = st['fuel']
    p.gear = st['gear']
    p.rpms = st['rpm']
    p.steerAngle = st['steer']
    p.speedKmh = v
    p.clutch = 0.0
    p.waterTemp = 92.0
    p.currentMaxRpm = 7400
    p.tc = 0.0 if st['gas'] < 0.9 else 0.12
    p.abs = 0.3 if st['brake'] > 0.7 else 0.0
    p.airTemp = 21.5
    p.roadTemp = 29.8
    p.turboBoost = st['gas'] * 1.4
    p.brakeBias = 0.572
    p.accG[0] = st['g_lat']
    p.accG[1] = (st['gas'] - st['brake']) * 1.3
    p.accG[2] = 0.0
    for i in range(4):
        front = i < 2
        p.tyreCoreTemperature[i] = 79.0 + abs(st['g_lat']) * 8 + (2.5 if front else 0.5)
        p.wheelsPressure[i] = 27.1 + (0.4 if front else 0.2)
        p.brakeTemp[i] = 305.0 + st['brake_heat'] * (330 if front else 190)
        p.slipRatio[i] = 0.03 * st['brake'] + 0.02 * st['gas']
        p.slipAngle[i] = 0.05 * abs(st['steer'])
        p.fx[i] = st['gas'] * 2400 - st['brake'] * 5200
        p.fy[i] = st['g_lat'] * 3100
        p.mz[i] = st['steer'] * 40
        p.brakePressure[i] = st['brake'] * (0.572 if front else 0.428)
        p.padLife[i] = 28.5 - st['laps_done'] * 0.05
        p.discLife[i] = 31.0 - st['laps_done'] * 0.02
        p.suspensionDamage[i] = 0.0
        p.suspensionTravel[i] = 0.012 + 0.004 * abs(st['g_lat'])
        p.wheelSlip[i] = 0.1 * st['brake']

    g.packetId = st['packet']
    g.status = 2  # AC_LIVE
    g.completedLaps = st['laps_done']
    g.iCurrentTime = int(st['lap_ms'])
    g.iLastTime = int(st['last_ms']) if st['last_ms'] else 0
    g.iBestTime = int(st['best_ms']) if st['best_ms'] else 2147483647
    g.isValidLap = 1
    g.normalizedCarPosition = st['pos']
    g.currentSectorIndex = min(2, int(st['pos'] * 3))
    g.surfaceGrip = 0.99
    g.windSpeed = 2.1
    g.windDirection = 140.0
    g.iDeltaLapTime = int(st['lap_ms'] - st['best_ms'] * st['pos']) if st['best_ms'] else 0
    g.fuelXLap = 2.9
    g.trackGripStatus = 4  # optimum
    g.rainIntensity = 0
    g.rainIntensityIn10min = 0
    g.rainIntensityIn30min = 0
    g.TC = 2
    g.TCCut = 6
    g.ABS = 3
    g.EngineMap = 1
    g.tyreCompound = 'dry_compound'
    g.fuelEstimatedLaps = st['fuel'] / 2.9
    g.sessionTimeLeft = max(0.0, 3600000.0 - st['t_total'] * 1000)
    g.playerCarID = 0
    g.carID[0] = 0
    g.activeCars = 1
    # Track map: a stadium-ish loop so the reconstruction has a real shape.
    ang = 2 * math.pi * st['pos']
    g.carCoordinates[0][0] = 620.0 * math.cos(ang)
    g.carCoordinates[0][1] = 12.0
    g.carCoordinates[0][2] = 410.0 * math.sin(ang) + 120.0 * math.sin(2 * ang)


# ---------------------------------------------------------------- main drive

def run(args):
    rng = random.Random(42)
    api = args.api.rstrip('/')

    # Authenticate as the test account and fetch its long-lived API key.
    r = requests.post(f'{api}/auth/login', json={'email': args.email, 'password': args.password}, timeout=15)
    r.raise_for_status()
    access = r.json()['access_token']
    me = requests.get(f'{api}/auth/me', headers={'Authorization': f'Bearer {access}'}, timeout=15).json()
    key = me.get('api_key')
    if not key:
        k = requests.post(f'{api}/api-keys', headers={'Authorization': f'Bearer {access}'},
                          json={'key_name': 'Synthetic drive'}, timeout=15)
        key = k.json()['api_key']
    print(f'[auth] api key: {key[:8]}…')

    # Session (same payload the client's _begin_session sends).
    reader = SyntheticACCReader('Ferrari 296 GT3 (synthetic)', 'Synthetic GP')
    resp = requests.post(f'{api}/sessions',
                         headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                         json={'track_name': reader.track_name, 'car_name': reader.car_name, 'game': 'acc'},
                         timeout=15)
    if resp.status_code != 201:
        print('session create failed:', resp.status_code, resp.text[:200]); sys.exit(1)
    data = resp.json()
    sid = data.get('session', {}).get('id') or data.get('id')
    print(f'[session] {sid}')

    ws_base = api.replace('https://', 'wss://').replace('http://', 'ws://')
    from urllib.parse import quote
    ws = WebSocketClient(f'{ws_base}/ws/session/{sid}?key={quote(key)}', key)
    if not ws.connect():
        print('WS connect failed'); sys.exit(1)
    print('[ws] connected (authed via ?key=)')

    p, g = ACCPhysics(), ACCGraphics()
    dt = 1.0 / args.hz
    st = {'packet': 0, 'v': 60.0, 'gas': 0.0, 'brake': 0.0, 'brake_heat': 0.0, 'steer': 0.0,
          'g_lat': 0.0, 'gear': 3, 'rpm': 4200, 'fuel': 58.0, 'pos': 0.0, 'lap_ms': 0.0,
          'last_ms': 0.0, 'best_ms': 0.0, 'laps_done': 0, 't_total': 0.0}
    s_dist = 0.0
    deltas = lap_corner_deltas(0, rng)
    buf, last_send, lap_times = [], time.time(), []

    print(f'[drive] {args.laps} laps on {reader.track_name} at {args.hz}Hz…')
    while st['laps_done'] < args.laps:
        tick_start = time.time()
        st['packet'] += 1
        st['t_total'] += dt

        # Chase the target speed profile with a bit of driver lag.
        target_now = corner_speed_profile(st['pos'], deltas)
        target_ahead = corner_speed_profile((st['pos'] + 45.0 / TRACK_LEN) % 1.0, deltas)
        target = min(target_now, target_ahead)
        err = target - st['v']
        if err < -1.5:
            st['brake'] = min(1.0, -err / 22.0); st['gas'] = 0.0
        elif err > 1.5:
            st['gas'] = min(1.0, err / 14.0 + 0.55); st['brake'] = 0.0
        else:
            st['gas'], st['brake'] = 0.62, 0.0
        accel = st['gas'] * 9.5 - st['brake'] * 21.0 - 0.012 * st['v']
        st['v'] = max(35.0, st['v'] + accel * dt * 3.6)
        st['brake_heat'] = min(1.0, st['brake_heat'] * 0.985 + st['brake'] * 0.06)

        # Steering / lateral g from corner proximity.
        prox = (VMAX - target_now) / VMAX
        st['steer'] = prox * (1 if int(st['pos'] * 14) % 2 else -1) * 0.6
        st['g_lat'] = prox * 2.6 * (1 if st['steer'] > 0 else -1)

        # Gears: simple speed bands.
        st['gear'] = min(7, max(2, int(st['v'] // 42) + 2))  # struct gear: 0=R,1=N,2=1st…
        band = (st['v'] % 42) / 42
        st['rpm'] = int(4600 + band * 2600)

        # Advance along the lap by distance.
        s_dist += (st['v'] / 3.6) * dt
        st['lap_ms'] += dt * 1000
        st['fuel'] = max(2, 58.0 - (st['laps_done'] + st['pos']) * 2.9)
        if s_dist >= TRACK_LEN:
            s_dist -= TRACK_LEN
            st['last_ms'] = st['lap_ms']
            st['best_ms'] = min(st['best_ms'], st['lap_ms']) if st['best_ms'] else st['lap_ms']
            lap_times.append(st['lap_ms'])
            print(f"  lap {st['laps_done'] + 1}: {st['lap_ms'] / 60000:.0f}:{(st['lap_ms'] % 60000) / 1000:06.3f}")
            st['lap_ms'] = 0.0
            st['laps_done'] += 1
            deltas = lap_corner_deltas(st['laps_done'], rng)
        st['pos'] = s_dist / TRACK_LEN

        # Real structs → real reader → real normalize → batch buffer.
        fill_structs(p, g, st)
        reader.push(p, g)
        raw = reader.read()
        if raw:
            frame = normalize('acc', raw)
            if frame:
                buf.append(frame)

        # Ship batches on the client's cadence.
        if time.time() - last_send >= 0.05 and buf and ws.is_connected:
            ws.send_batch(buf)
            buf = []
            last_send = time.time()

        time.sleep(max(0, dt - (time.time() - tick_start)))

    if buf and ws.is_connected:
        ws.send_batch(buf)
    time.sleep(1.5)  # let the backend flush its batch buffer
    ws.disconnect()
    requests.post(f'{api}/sessions/{sid}/end', headers={'Authorization': f'Bearer {key}'}, timeout=15)
    print(f'[done] session {sid} ended · laps: {len(lap_times)} · best: {min(lap_times) / 1000:.3f}s')
    print(f'SESSION_ID={sid}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--email', required=True)
    ap.add_argument('--password', required=True)
    ap.add_argument('--api', default='https://myracingdata.com/api/v1')
    ap.add_argument('--laps', type=int, default=4)
    ap.add_argument('--hz', type=int, default=60)
    run(ap.parse_args())
