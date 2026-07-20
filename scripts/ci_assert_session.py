"""
Assert the CI e2e drive actually landed in the backend.

Base case: a fresh 'Synthetic GP CI' session for the test account, with
telemetry, >=2 timed laps and sector splits.

CI_PRIMARY_TRACK overrides the expected track (default 'Synthetic GP CI').
If CI_SWITCH_TRACK is set, also assert the mid-run LIVE->LIVE track switch
produced a SECOND, distinct session under that track name (>=2 timed laps) —
proving the client rolled to a new session without the sim hitting the menu.

Reads TEST_EMAIL / TEST_PASSWORD (via ci_creds.json). Exit 0 = pass.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = 'https://myracingdata.com/api/v1'


def track_of(s):
    return s.get('track_name') or s.get('track') or ''


def newest_exact(sessions, name):
    hits = [s for s in sessions if track_of(s) == name]
    hits.sort(key=lambda s: s.get('started_at') or '', reverse=True)
    return hits[0] if hits else None


def fresh_enough(s):
    started = s.get('started_at') or ''
    if not started:
        return True
    age = datetime.now(timezone.utc) - datetime.fromisoformat(str(started).replace(' ', 'T')).replace(tzinfo=timezone.utc)
    return age <= timedelta(minutes=45)


def timed_laps(hdr, sid):
    r = requests.get(f'{API}/sessions/{sid}/laps', headers=hdr, timeout=20)
    r.raise_for_status()
    laps = r.json().get('laps', [])
    timed = [l for l in laps if l.get('lap_time_ms')]
    with_sectors = [l for l in timed if l.get('sector_1_time_ms') and l.get('sector_2_time_ms') and l.get('sector_3_time_ms')]
    return timed, with_sectors


def check(hdr, s, label, min_laps=2, need_sectors=True):
    if not s:
        print(f'FAIL: no "{label}" session found'); return False
    if not fresh_enough(s):
        print(f'FAIL: newest "{label}" session is stale'); return False
    sid = s['id']
    timed, with_sectors = timed_laps(hdr, sid)
    print(f'{label}: {sid} · {track_of(s)} · {len(timed)} timed laps, {len(with_sectors)} with sectors')
    for l in timed[:6]:
        print(f"  lap {l['lap_number']}: {l['lap_time_ms']/1000:.3f}s"
              f" S1={l.get('sector_1_time_ms')} S2={l.get('sector_2_time_ms')} S3={l.get('sector_3_time_ms')}")
    if len(timed) < min_laps:
        print(f'FAIL: "{label}" has fewer than {min_laps} timed laps'); return False
    if need_sectors and not with_sectors:
        print(f'FAIL: "{label}" has no sector splits'); return False
    return True


def main():
    creds = json.loads(Path('ci_creds.json').read_text())
    r = requests.post(f'{API}/auth/login', json={'email': creds['email'], 'password': creds['password']}, timeout=20)
    r.raise_for_status()
    hdr = {'Authorization': f"Bearer {r.json()['access_token']}"}

    r = requests.get(f'{API}/sessions', headers=hdr, timeout=20)
    r.raise_for_status()
    body = r.json()
    sessions = body if isinstance(body, list) else body.get('sessions', [])

    primary_track = os.environ.get('CI_PRIMARY_TRACK', 'Synthetic GP CI')
    primary = newest_exact(sessions, primary_track)
    if not check(hdr, primary, 'primary'):
        return 1

    switch_track = os.environ.get('CI_SWITCH_TRACK')
    if switch_track:
        second = newest_exact(sessions, switch_track)
        # Sector splits need a full lap after the switch; require laps, sectors optional.
        if not check(hdr, second, 'post-switch', min_laps=2, need_sectors=False):
            return 1
        if second['id'] == primary['id']:
            print('FAIL: switch did not create a NEW session (same id)'); return 1
        print(f'PASS: LIVE track switch rolled to a new session ({primary["id"]} -> {second["id"]})')
    else:
        print('PASS: the client captured a full session end-to-end on Windows')
    return 0


if __name__ == '__main__':
    sys.exit(main())
