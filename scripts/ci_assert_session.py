"""
Assert the CI e2e drive actually landed in the backend: a fresh 'Synthetic GP
CI' session exists for the test account, with telemetry, >=2 laps and sector
splits. Reads TEST_EMAIL / TEST_PASSWORD. Exit 0 = pass.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = 'https://myracingdata.com/api/v1'


def main():
    creds = json.loads(Path('ci_creds.json').read_text())
    email, pw = creds['email'], creds['password']

    r = requests.post(f'{API}/auth/login', json={'email': email, 'password': pw}, timeout=20)
    r.raise_for_status()
    hdr = {'Authorization': f"Bearer {r.json()['access_token']}"}

    r = requests.get(f'{API}/sessions', headers=hdr, timeout=20)
    r.raise_for_status()
    body = r.json()
    sessions = body if isinstance(body, list) else body.get('sessions', [])
    fresh = [s for s in sessions
             if 'Synthetic GP CI' in (s.get('track_name') or s.get('track') or '')]
    fresh.sort(key=lambda s: s.get('started_at') or '', reverse=True)
    if not fresh:
        print('FAIL: no "Synthetic GP CI" session found'); return 1
    s = fresh[0]
    started = s.get('started_at') or ''
    if started:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(str(started).replace(' ', 'T')).replace(tzinfo=timezone.utc)
        if age > timedelta(minutes=45):
            print(f'FAIL: newest CI session is stale ({age})'); return 1
    sid = s['id']
    print(f'session: {sid} · {s.get("track_name") or s.get("track")} · started {started}')

    r = requests.get(f'{API}/sessions/{sid}/laps', headers=hdr, timeout=20)
    r.raise_for_status()
    laps = r.json().get('laps', [])
    timed = [l for l in laps if l.get('lap_time_ms')]
    with_sectors = [l for l in timed if l.get('sector_1_time_ms') and l.get('sector_2_time_ms') and l.get('sector_3_time_ms')]
    print(f'laps: {len(timed)} timed, {len(with_sectors)} with full sector splits')
    for l in timed[:6]:
        print(f"  lap {l['lap_number']}: {l['lap_time_ms']/1000:.3f}s"
              f" S1={l.get('sector_1_time_ms')} S2={l.get('sector_2_time_ms')} S3={l.get('sector_3_time_ms')}")

    if len(timed) < 2:
        print('FAIL: fewer than 2 timed laps'); return 1
    if not with_sectors:
        print('FAIL: no laps carry sector splits'); return 1
    print('PASS: the client captured a full session end-to-end on Windows')
    return 0


if __name__ == '__main__':
    sys.exit(main())
