"""
Fake iRacing for Windows — creates the REAL named shared memory the sim creates
("Local\\IRSDKMemMapFileName") and writes a synthetic drive into it in the exact
irsdk layout, so the actual client (source or built .exe) can be tested
end-to-end on a Windows machine with no iRacing subscription.

The ACC robot rig's counterpart. Reuses the same drive model so the laps look
like real driving (corner speed profile, braking, lap times).

Usage (Windows only):
  python scripts/fake_iracing_windows.py --laps 3 --track-len 2500 --hz 60
"""

import argparse
import mmap
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from synthetic_acc_drive import advance_drive, fresh_state, lap_corner_deltas

MEM_NAME = 'Local\\IRSDKMemMapFileName'
HEADER_SIZE, VARBUF_SIZE, VARHEADER_SIZE = 112, 16, 144
MAX_BUFS = 4
ST_CONNECTED = 1

# (name, irsdk type, struct fmt) — the channels our reader consumes.
VARS = [
    ('SessionTime',           5, 'd'),
    ('Speed',                 4, 'f'),   # m/s
    ('Throttle',              4, 'f'),   # 0..1
    ('Brake',                 4, 'f'),   # 0..1
    ('Clutch',                4, 'f'),
    ('RPM',                   4, 'f'),
    ('Gear',                  2, 'i'),
    ('Lap',                   2, 'i'),
    ('LapDistPct',            4, 'f'),   # 0..1  -> normalized_position
    ('LapCurrentLapTime',     4, 'f'),   # seconds
    ('LapLastLapTime',        4, 'f'),
    ('LapBestLapTime',        4, 'f'),
    ('FuelLevel',             4, 'f'),
    ('SteeringWheelAngle',    4, 'f'),   # radians
    ('SteeringWheelAngleMax', 4, 'f'),
    ('LatAccel',              4, 'f'),
    ('LongAccel',             4, 'f'),
    ('Lat',                   5, 'd'),   # -> pos_z
    ('Lon',                   5, 'd'),   # -> pos_x
    ('Alt',                   4, 'f'),
    ('LFtempCM',              4, 'f'),
    ('RFtempCM',              4, 'f'),
    ('LRtempCM',              4, 'f'),
    ('RRtempCM',              4, 'f'),
    ('TrackTempCrew',         4, 'f'),
]
SIZES = {2: 4, 4: 4, 5: 8}

SESSION_YAML = (
    "---\n"
    "WeekendInfo:\n"
    " TrackName: syntheticringci\n"
    " TrackDisplayName: Synthetic Ring CI\n"
    "DriverInfo:\n"
    " CarScreenName: Robot Rig GT3\n"
    "...\n\x00"
).encode()


def build_layout():
    """var headers + per-var offsets inside a telemetry row."""
    headers, offsets, off = b'', {}, 0
    for name, vtype, fmt in VARS:
        headers += (struct.pack('<3i', vtype, off, 1) + b'\x00' * 4
                    + name.encode().ljust(32, b'\x00')
                    + b''.ljust(64, b'\x00') + b''.ljust(32, b'\x00'))
        offsets[name] = (off, fmt)
        off += SIZES[vtype]
    return headers, offsets, off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--laps', type=int, default=3)
    ap.add_argument('--track-len', type=float, default=2500.0)
    ap.add_argument('--hz', type=int, default=60)
    args = ap.parse_args()

    headers, offsets, row_len = build_layout()
    var_hdr_off = HEADER_SIZE
    sess_off = var_hdr_off + len(headers)
    buf0 = sess_off + len(SESSION_YAML)
    total = buf0 + row_len * MAX_BUFS + 64

    mm = mmap.mmap(-1, total, MEM_NAME)

    def write_header(status=ST_CONNECTED):
        h = struct.pack('<10i', 2, status, args.hz, 1, len(SESSION_YAML), sess_off,
                        len(VARS), var_hdr_off, MAX_BUFS, row_len) + b'\x00' * 8
        for i in range(MAX_BUFS):
            h += struct.pack('<2i', ticks[i], buf0 + i * row_len) + b'\x00' * 8
        mm.seek(0); mm.write(h)

    ticks = [0] * MAX_BUFS
    write_header()
    mm.seek(var_hdr_off); mm.write(headers)
    mm.seek(sess_off); mm.write(SESSION_YAML)

    st = fresh_state()
    import random
    rng = random.Random(11)
    deltas = lap_corner_deltas(0, rng)
    dt = 1.0 / args.hz
    tick = 0
    print(f'[fake-iracing] pages up · driving {args.laps} laps of {args.track_len:.0f}m at {args.hz}Hz', flush=True)

    while st['laps_done'] < args.laps:
        t0 = time.time()
        if advance_drive(st, dt, deltas, track_len=args.track_len):
            print(f"[fake-iracing] lap {st['laps_done']}: {st['last_ms'] / 1000:.3f}s", flush=True)
            deltas = lap_corner_deltas(st['laps_done'], rng)

        tick += 1
        slot = tick % MAX_BUFS
        base = buf0 + slot * row_len
        vals = {
            'SessionTime': st['t_total'], 'Speed': st['v'] / 3.6,
            'Throttle': st['gas'], 'Brake': st['brake'], 'Clutch': 0.0,
            'RPM': float(st['rpm']), 'Gear': int(st['gear']), 'Lap': int(st['laps_done']) + 1,
            'LapDistPct': st['pos'], 'LapCurrentLapTime': st['lap_ms'] / 1000.0,
            'LapLastLapTime': st['last_ms'] / 1000.0, 'LapBestLapTime': st['best_ms'] / 1000.0,
            'FuelLevel': st['fuel'], 'SteeringWheelAngle': st['steer'] * 4.5,
            'SteeringWheelAngleMax': 4.5, 'LatAccel': st['g_lat'], 'LongAccel': 0.0,
            # A closed loop of lat/lon so the track map reconstructs.
            'Lat': 50.44 + 0.010 * __import__('math').sin(st['pos'] * 6.28318),
            'Lon': 5.25 + 0.014 * __import__('math').cos(st['pos'] * 6.28318),
            'Alt': 80.0, 'LFtempCM': 82.0, 'RFtempCM': 81.0, 'LRtempCM': 83.0, 'RRtempCM': 82.5,
            'TrackTempCrew': 31.0,
        }
        for name, (voff, fmt) in offsets.items():
            mm.seek(base + voff); mm.write(struct.pack('<' + fmt, vals[name]))
        ticks[slot] = tick
        write_header()

        time.sleep(max(0, dt - (time.time() - t0)))

    # Leave the session: clear the connected bit, like quitting to the menu.
    write_header(status=0)
    print('[fake-iracing] session over (status=0), holding pages 15s…', flush=True)
    time.sleep(15)
    print('[fake-iracing] done', flush=True)


if __name__ == '__main__':
    main()
