"""
Canonical telemetry schema.

Every sim reader emits its own shape (AC and LMU nest inputs/tyres, ACC's
broadcasting feed has no inputs at all). The backend's `telemetry` table is the
single source of truth for what gets stored, so this module maps each reader's
raw output onto exactly those columns before the frame goes on the wire.

Unit conventions (the backend/viewer already assume these):
  - Pedals (throttle/brake/clutch): 0-100 (percent). Sim shared memory gives
    0.0-1.0, so we scale x100.
  - Lap times: integer milliseconds.
  - Gear: -1 = reverse, 0 = neutral, 1+ = forward.
  - Tyre/brake arrays: order is FL, FR, RL, RR.
  - Steering: passed through raw. Units differ per sim (AC radians vs rF2
    -1..1), so this is calibrated against the rig rather than guessed here.

`session_id`, `timestamp` and `id` are NOT produced here - the backend injects
them (it owns the session id from the WS URL).
"""

# Fields the client must supply for the backend insert. The NOT NULL columns
# come first; the rest are nullable enrichment. Defaults guarantee a complete
# row even when a sim doesn't expose a given channel.
REQUIRED_FIELDS = (
    "lap_number", "speed_kmh", "rpm", "gear",
    "throttle_input", "brake_input", "steering_input",
    "current_lap_time_ms", "delta_to_best_ms",
)

DEFAULTS = {
    # required (NOT NULL on the backend)
    "lap_number": 0,
    "speed_kmh": 0.0,
    "rpm": 0,
    "gear": 0,
    "throttle_input": 0.0,
    "brake_input": 0.0,
    "steering_input": 0.0,
    "current_lap_time_ms": 0,
    "delta_to_best_ms": 0,
    # nullable enrichment
    "clutch_input": 0.0,
    "best_lap_time_ms": 0,
    "last_lap_time_ms": 0,
    "is_valid_lap": True,
    "tire_temp_fl": None, "tire_temp_fr": None, "tire_temp_rl": None, "tire_temp_rr": None,
    "tire_wear_fl": None, "tire_wear_fr": None, "tire_wear_rl": None, "tire_wear_rr": None,
    "tire_pressure_fl": None, "tire_pressure_fr": None, "tire_pressure_rl": None, "tire_pressure_rr": None,
    "brake_temp_fl": None, "brake_temp_fr": None, "brake_temp_rl": None, "brake_temp_rr": None,
    "fuel_remaining_liters": None,
    "drs_available": False,
    "drs_enabled": False,
}

# Friendly game id carried through for the client status line / debugging.
GAME_IDS = {
    "ac": "assetto_corsa",
    "acc": "assetto_corsa_competizione",
    "lmu": "le_mans_ultimate",
}


def _delta_to_best(current_ms, best_ms):
    """Gap of the current lap time to the session best, in ms (0 if no best yet)."""
    if best_ms and current_ms:
        return int(current_ms - best_ms)
    return 0


def _finalize(game_key, fields):
    """Merge a reader's mapped fields onto the canonical defaults."""
    frame = dict(DEFAULTS)
    frame.update({k: v for k, v in fields.items() if v is not None or k not in REQUIRED_FIELDS})
    frame["game"] = GAME_IDS.get(game_key, game_key)
    if "delta_to_best_ms" not in fields:
        frame["delta_to_best_ms"] = _delta_to_best(
            frame["current_lap_time_ms"], frame["best_lap_time_ms"]
        )
    return frame


def _map_ac_shape(raw):
    """Map an AC/ACC shared-memory frame (games/ac.py shape) to contract fields.

    Shared by AC and the ACC shared-memory reader, which emit the same shape.
    """
    tires = raw.get("tires", [])
    brake_temps = raw.get("brakes", {}).get("temps", [])
    lap = raw.get("lap", {})
    drs = raw.get("drs", {})

    def tyre(i, key):
        return tires[i].get(key) if i < len(tires) else None

    return {
        "lap_number": lap.get("current", 0),
        "speed_kmh": raw.get("speed_kmh", 0.0),
        "rpm": int(raw.get("rpm", 0)),
        "gear": int(raw.get("gear", 1)) - 1,  # AC: 0=R, 1=N, 2=1st -> -1/0/1
        "throttle_input": raw.get("throttle", 0.0) * 100.0,
        "brake_input": raw.get("brake", 0.0) * 100.0,
        "clutch_input": raw.get("clutch", 0.0) * 100.0,
        "steering_input": raw.get("steering", 0.0),
        "current_lap_time_ms": lap.get("current_time_ms", 0),
        "best_lap_time_ms": lap.get("best_time_ms", 0),
        "last_lap_time_ms": lap.get("last_time_ms", 0),
        "is_valid_lap": bool(raw.get("is_valid_lap", True)),
        "tire_temp_fl": tyre(0, "temp_core"), "tire_temp_fr": tyre(1, "temp_core"),
        "tire_temp_rl": tyre(2, "temp_core"), "tire_temp_rr": tyre(3, "temp_core"),
        "tire_wear_fl": tyre(0, "wear"), "tire_wear_fr": tyre(1, "wear"),
        "tire_wear_rl": tyre(2, "wear"), "tire_wear_rr": tyre(3, "wear"),
        "tire_pressure_fl": tyre(0, "pressure"), "tire_pressure_fr": tyre(1, "pressure"),
        "tire_pressure_rl": tyre(2, "pressure"), "tire_pressure_rr": tyre(3, "pressure"),
        "brake_temp_fl": brake_temps[0] if len(brake_temps) > 0 else None,
        "brake_temp_fr": brake_temps[1] if len(brake_temps) > 1 else None,
        "brake_temp_rl": brake_temps[2] if len(brake_temps) > 2 else None,
        "brake_temp_rr": brake_temps[3] if len(brake_temps) > 3 else None,
        "fuel_remaining_liters": raw.get("fuel"),
        "drs_available": bool(drs.get("available", 0)),
        "drs_enabled": bool(drs.get("enabled", 0)),
    }


def normalize_ac(raw):
    """Map Assetto Corsa shared-memory output (games/ac.py) onto the contract."""
    return _finalize("ac", _map_ac_shape(raw))


def normalize_lmu(raw):
    """Map Le Mans Ultimate shared-memory output (games/lmu.py) onto the contract."""
    inp = raw.get("input_raw", {})
    tires = raw.get("tires", [])
    lap = raw.get("lap", {})

    def tyre(i, key):
        return tires[i].get(key) if i < len(tires) else None

    # LMU lap times are doubles in seconds; the contract is integer ms.
    def to_ms(seconds):
        return int((seconds or 0) * 1000)

    return _finalize("lmu", {
        "lap_number": lap.get("number", 0),
        "speed_kmh": raw.get("speed_kmh", 0.0),
        "rpm": int(raw.get("rpm", 0)),
        "gear": int(raw.get("gear", 0)),  # rF2: -1=R, 0=N, 1=1st (already canonical)
        "throttle_input": inp.get("throttle", 0.0) * 100.0,
        "brake_input": inp.get("brake", 0.0) * 100.0,
        "clutch_input": inp.get("clutch", 0.0) * 100.0,
        "steering_input": inp.get("steering", 0.0),
        "current_lap_time_ms": to_ms(lap.get("current_time")),
        "best_lap_time_ms": to_ms(lap.get("best_time")),
        "last_lap_time_ms": to_ms(lap.get("last_time")),
        "tire_temp_fl": tyre(0, "temp_middle"), "tire_temp_fr": tyre(1, "temp_middle"),
        "tire_temp_rl": tyre(2, "temp_middle"), "tire_temp_rr": tyre(3, "temp_middle"),
        "tire_wear_fl": tyre(0, "wear"), "tire_wear_fr": tyre(1, "wear"),
        "tire_wear_rl": tyre(2, "wear"), "tire_wear_rr": tyre(3, "wear"),
        "tire_pressure_fl": tyre(0, "pressure"), "tire_pressure_fr": tyre(1, "pressure"),
        "tire_pressure_rl": tyre(2, "pressure"), "tire_pressure_rr": tyre(3, "pressure"),
        "brake_temp_fl": tyre(0, "brake_temp"), "brake_temp_fr": tyre(1, "brake_temp"),
        "brake_temp_rl": tyre(2, "brake_temp"), "brake_temp_rr": tyre(3, "brake_temp"),
        "fuel_remaining_liters": raw.get("fuel"),
    })


def normalize_acc(raw):
    """Map ACC output onto the contract, from either ACC source.

    The shared-memory reader (games/acc_shared_memory.py) emits the same shape as
    AC and carries full driver inputs, so it goes through the shared AC mapping.
    The legacy UDP broadcasting reader (games/acc.py) is timing/leaderboard only
    — no inputs or tyre data — so those fields stay at their defaults.
    """
    if "throttle" in raw or "tires" in raw:
        return _finalize("acc", _map_ac_shape(raw))

    return _finalize("acc", {
        "lap_number": raw.get("lap_count", 0),
        "speed_kmh": raw.get("speed_kmh", 0.0),
        "rpm": int(raw.get("rpm", 0)),
        "gear": int(raw.get("gear", 0)),  # ac.py already applied the -1 offset
        "current_lap_time_ms": raw.get("current_lap_time_ms", 0),
        "best_lap_time_ms": raw.get("best_lap_time_ms", 0),
        "last_lap_time_ms": raw.get("last_lap_time_ms", 0),
    })


_NORMALIZERS = {
    "ac": normalize_ac,
    "acc": normalize_acc,
    "lmu": normalize_lmu,
}


def normalize(game_key, raw):
    """Map a reader's raw frame onto the canonical contract.

    game_key is the active-game key used in main.py ('ac' | 'acc' | 'lmu').
    Returns None if the game is unknown or there's nothing to send.
    """
    if not raw:
        return None
    fn = _NORMALIZERS.get(game_key)
    if fn is None:
        return None
    frame = fn(raw)
    # Carry the rich-channel blob (ACC `ext`) through for server-side JSON storage.
    if frame is not None and isinstance(raw, dict) and raw.get('ext'):
        frame['ext'] = raw['ext']
    return frame
