"""
Fake ACC for Windows — creates the REAL named shared-memory pages the game
creates (acpmf_physics / acpmf_graphics / acpmf_static) and writes the
synthetic drive into them, so the actual client (source or built .exe) can be
tested end-to-end on a Windows machine with no game installed.

This is the CI "robot rig": the client detects "ACC", captures at full rate,
creates a backend session, and streams — exactly the production path.

Usage (Windows only):
  python scripts/fake_acc_windows.py --laps 3 --track-len 2500 --hz 60
"""

import argparse
import ctypes
import mmap
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from games.acc_structs import ACCPhysics, ACCGraphics, ACCStatic
from synthetic_acc_drive import advance_drive, fresh_state, lap_corner_deltas, fill_structs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--laps', type=int, default=3)
    ap.add_argument('--track-len', type=float, default=2500.0)
    ap.add_argument('--hz', type=int, default=60)
    args = ap.parse_args()

    # Create the named pages exactly like the game does. Both the fake and the
    # client call mmap(-1, size, name) — Windows maps them to the same object.
    phys_mm = mmap.mmap(-1, ctypes.sizeof(ACCPhysics), 'acpmf_physics')
    gfx_mm = mmap.mmap(-1, ctypes.sizeof(ACCGraphics), 'acpmf_graphics')
    static_mm = mmap.mmap(-1, ctypes.sizeof(ACCStatic), 'acpmf_static')

    st_struct = ACCStatic()
    st_struct.smVersion = '1.8'
    st_struct.acVersion = '1.9'
    st_struct.carModel = 'Ferrari 296 GT3 (CI)'
    st_struct.track = 'Synthetic GP CI'
    st_struct.playerName = 'Robot'
    st_struct.playerSurname = 'Rig'
    st_struct.sectorCount = 3
    st_struct.maxRpm = 7400
    st_struct.maxFuel = 110.0
    st_struct.PitWindowStart = 25
    st_struct.PitWindowEnd = 45
    static_mm.seek(0)
    static_mm.write(bytes(st_struct))

    p, g = ACCPhysics(), ACCGraphics()
    rng = random.Random(7)
    st = fresh_state()
    deltas = lap_corner_deltas(0, rng)
    dt = 1.0 / args.hz

    print(f'[fake-acc] pages up · driving {args.laps} laps of {args.track_len:.0f}m at {args.hz}Hz', flush=True)
    while st['laps_done'] < args.laps:
        tick = time.time()
        if advance_drive(st, dt, deltas, track_len=args.track_len):
            print(f"[fake-acc] lap {st['laps_done']}: {st['last_ms'] / 1000:.3f}s", flush=True)
            deltas = lap_corner_deltas(st['laps_done'], rng)
        fill_structs(p, g, st)
        phys_mm.seek(0); phys_mm.write(bytes(p))
        gfx_mm.seek(0); gfx_mm.write(bytes(g))
        time.sleep(max(0, dt - (time.time() - tick)))

    # Leave the session: status -> AC_OFF, like quitting to the menu. The client
    # should end its backend session (lifecycle test) within a few seconds.
    g.status = 0
    gfx_mm.seek(0); gfx_mm.write(bytes(g))
    print('[fake-acc] session over (status=AC_OFF), holding pages 15s…', flush=True)
    time.sleep(15)
    print('[fake-acc] done', flush=True)


if __name__ == '__main__':
    main()
