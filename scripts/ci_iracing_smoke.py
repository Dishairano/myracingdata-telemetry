"""
Windows smoke test: does the REAL iRacing reader work against REAL Windows
shared memory?

Starts the fake irsdk writer as a subprocess, then drives the actual
IRacingTelemetry reader against it and asserts it connects and produces sane
frames. No exe, no backend, no session plumbing — this isolates the reader so a
failure points at exactly one thing.

Exit 0 = pass.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from games.iracing import IRacingTelemetry  # noqa: E402
from capture.canonical import normalize      # noqa: E402


def main():
    fake = subprocess.Popen(
        [sys.executable, str(ROOT / 'scripts' / 'fake_iracing_windows.py'),
         '--laps', '2', '--track-len', '2000', '--hz', '60'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        time.sleep(4)  # let the writer publish the map
        if fake.poll() is not None:
            print('FAIL: fake writer exited early:\n' + (fake.stdout.read() or ''))
            return 1

        r = IRacingTelemetry()
        connected = False
        for attempt in range(20):
            if r.connect():
                connected = True
                break
            time.sleep(1)
        if not connected:
            print('FAIL: reader could not connect to the iRacing shared memory')
            return 1
        print(f'connected · track={r.track_name!r} car={r.car_name!r} vars={len(r.vars)}')

        frames, speeds, positions = 0, [], []
        deadline = time.time() + 25
        while frames < 200 and time.time() < deadline:
            raw = r.read()
            if not raw:
                time.sleep(0.005)
                continue
            f = normalize('iracing', raw)
            if f:
                frames += 1
                speeds.append(f.get('speed_kmh') or 0)
                ext = f.get('ext') or {}
                positions.append(ext.get('normalized_position') or 0)

        r.disconnect()
        print(f'frames={frames} speed[min/max]={min(speeds, default=0):.1f}/{max(speeds, default=0):.1f} '
              f'pos[min/max]={min(positions, default=0):.3f}/{max(positions, default=0):.3f}')

        if frames < 50:
            print(f'FAIL: only {frames} frames read'); return 1
        if max(speeds, default=0) < 50:
            print('FAIL: speeds look wrong (no real motion)'); return 1
        if max(positions, default=0) <= 0:
            print('FAIL: no normalized_position — corner analysis would not work'); return 1
        if r.track_name != 'Synthetic Ring CI':
            print(f'FAIL: track name {r.track_name!r}'); return 1

        print('PASS: the iRacing reader works against real Windows shared memory')
        return 0
    finally:
        if fake.poll() is None:
            fake.terminate()
            try:
                fake.wait(timeout=10)
            except Exception:
                fake.kill()


if __name__ == '__main__':
    sys.exit(main())
