"""
End-to-end capture self-test (no sim, no rig).

Drives the real pipeline: register -> create session -> open the real
WebSocket client -> stream synthetic AC frames through the real normalize layer
-> then read the backend's SQLite DB and assert the rows persisted with correct,
non-NULL fields. This is the check that proves a real sim frame would land
correctly, runnable here or in CI.

Usage:
    python scripts/capture_selftest.py \
        --api  http://localhost:5999/api/v1 \
        --ws   ws://localhost:5999/api/v1/ws \
        --db   /path/to/test/data/race_engineer.db \
        --frames 60

Exit code 0 = PASS, 1 = FAIL.
"""

import argparse
import sqlite3
import sys
import time
import uuid
from pathlib import Path

import requests

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from capture.canonical import normalize, REQUIRED_FIELDS  # noqa: E402
from capture.synthetic import SyntheticACSource           # noqa: E402
from network.websocket_client import WebSocketClient       # noqa: E402


def fail(msg):
    print(f"❌ FAIL: {msg}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:5999/api/v1")
    ap.add_argument("--ws", default="ws://localhost:5999/api/v1/ws")
    ap.add_argument("--db", required=True, help="path to the backend's race_engineer.db")
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--game", default="ac", choices=["ac", "acc"],
                    help="which normalizer path to exercise (both consume AC-shaped frames)")
    args = ap.parse_args()

    game_names = {"ac": "assetto_corsa", "acc": "assetto_corsa_competizione"}

    email = f"selftest+{uuid.uuid4().hex[:8]}@myracingdata.test"

    # 1. Register and grab a JWT (session-create accepts JWT or api key).
    r = requests.post(f"{args.api}/auth/register", json={
        "name": "Self Test", "email": email, "password": "Testpass123",
        "roles": {"is_driver": True},
    }, timeout=10)
    if r.status_code not in (200, 201):
        fail(f"register -> {r.status_code}: {r.text}")
    token = r.json().get("access_token")
    if not token:
        fail(f"no access_token in register response: {r.text}")
    print(f"✓ registered {email}")

    # 2. Create a session (same shape the real client sends).
    r = requests.post(f"{args.api}/sessions",
                      headers={"Authorization": f"Bearer {token}"},
                      json={"track_name": "Spa", "car_name": "Ferrari 488 GT3",
                            "game": game_names[args.game]}, timeout=10)
    if r.status_code != 201:
        fail(f"create session -> {r.status_code}: {r.text}")
    body = r.json()
    session_id = body.get("session", {}).get("id") or body.get("id")
    if not session_id:
        fail(f"no session id in response: {r.text}")
    print(f"✓ session created: {session_id}")

    # 3. Open the real WebSocket client and stream normalized synthetic frames.
    ws = WebSocketClient(f"{args.ws}/session/{session_id}", token)
    if not ws.connect():
        fail("websocket connect failed")
    print("✓ websocket connected")

    source = SyntheticACSource()
    sent = 0
    interval = 1.0 / args.hz
    for _ in range(args.frames):
        frame = normalize(args.game, source.read())
        if frame and ws.send_telemetry(frame):
            sent += 1
        time.sleep(interval)
    print(f"✓ streamed {sent}/{args.frames} frames")

    # Give the backend time to flush its batch buffer, then end the session.
    time.sleep(2.0)
    ws.disconnect()
    requests.patch(f"{args.api}/sessions/{session_id}/end",
                   headers={"Authorization": f"Bearer {token}"}, timeout=5)

    # 4. Assert persistence directly against the backend DB.
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM telemetry WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    con.close()

    print(f"\n--- verification ---")
    print(f"rows persisted for session: {len(rows)}")
    if not rows:
        fail("no telemetry rows persisted")

    # Every NOT NULL contract field must be populated on every row.
    for field in REQUIRED_FIELDS:
        if any(row[field] is None for row in rows):
            fail(f"required field '{field}' was NULL on at least one row")

    # The data must actually carry driver inputs in the expected ranges.
    throttles = [row["throttle_input"] for row in rows]
    brakes = [row["brake_input"] for row in rows]
    speeds = [row["speed_kmh"] for row in rows]
    if not any(t > 1 for t in throttles):
        fail("throttle_input never exceeded 1 — inputs look unscaled/empty")
    if max(throttles) > 100 or min(throttles) < 0:
        fail(f"throttle_input out of 0-100 range: {min(throttles)}..{max(throttles)}")

    sample = rows[len(rows) // 2]
    print(f"sample row: speed={sample['speed_kmh']} throttle={sample['throttle_input']} "
          f"brake={sample['brake_input']} gear={sample['gear']} "
          f"tire_fl={sample['tire_temp_fl']} lap={sample['lap_number']} "
          f"session_id={sample['session_id'][:12]}...")
    print(f"ranges: speed {min(speeds):.0f}-{max(speeds):.0f} | "
          f"throttle {min(throttles):.0f}-{max(throttles):.0f} | "
          f"brake {min(brakes):.0f}-{max(brakes):.0f}")
    print(f"\n✅ PASS — {len(rows)} rows, all required fields populated, inputs in range")


if __name__ == "__main__":
    main()
