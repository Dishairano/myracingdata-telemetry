"""
Synthetic telemetry source.

Generates AC-shaped frames (matching games/ac.py read() output) for a scripted
lap, so the capture pipeline -> normalize -> WebSocket -> backend can be
exercised end-to-end without a sim or a rig. Used by scripts/capture_selftest.py
and available as a `--simulate` source for manual smoke testing.

The numbers are plausible, not physically exact: speed/throttle/brake follow a
simple corner-straight-corner profile, gears track speed, and lap timing
advances so lap_number, current/last/best lap times all populate.
"""

import math
import time


class SyntheticACSource:
    """Produces a continuous stream of AC-shaped telemetry frames."""

    LAP_MS = 90_000  # 90s synthetic lap

    def __init__(self, fuel_start=60.0):
        self._t0 = time.time()
        self._lap = 0
        self._best_ms = 0
        self._last_ms = 0
        self._fuel = fuel_start

    @property
    def is_connected(self) -> bool:
        return True

    def connect(self) -> bool:
        return True

    def disconnect(self):
        pass

    def read(self) -> dict:
        """Return one AC-shaped frame for the current instant."""
        elapsed_ms = int((time.time() - self._t0) * 1000)
        lap = elapsed_ms // self.LAP_MS
        lap_ms = elapsed_ms % self.LAP_MS

        # Roll over lap timing when a lap completes.
        if lap != self._lap:
            self._last_ms = self.LAP_MS
            self._best_ms = self._last_ms if self._best_ms == 0 else min(self._best_ms, self._last_ms)
            self._lap = lap

        # Corner-straight-corner profile over the lap (0..1 phase).
        phase = lap_ms / self.LAP_MS
        corner = (math.sin(phase * 2 * math.pi * 4) + 1) / 2  # 0=corner, 1=straight
        speed = 80 + corner * 200                              # 80..280 km/h
        throttle = corner                                      # 0..1
        brake = max(0.0, 1.0 - corner * 1.5)                   # brake into corners
        steering = math.sin(phase * 2 * math.pi * 4) * 0.4     # -0.4..0.4
        gear = max(1, min(6, int(speed / 45)))                 # 1..6 (canonical)
        rpm = int(4000 + corner * 4500)
        self._fuel = max(0.0, self._fuel - 0.0005)

        base_tyre = 80 + corner * 25  # hotter on the straights/braking
        return {
            "game": "assetto_corsa",
            "timestamp": time.time(),
            "speed_kmh": round(speed, 2),
            "rpm": rpm,
            "gear": gear + 1,  # AC raw gear: 0=R,1=N,2=1st -> emit canonical+1
            "throttle": round(throttle, 3),
            "brake": round(brake, 3),
            "clutch": 0.0,
            "steering": round(steering, 3),
            "tires": [
                {"temp_core": round(base_tyre + i, 1), "pressure": round(27.0 + i * 0.1, 1),
                 "wear": round(1.0 - lap * 0.01, 3)}
                for i in range(4)
            ],
            "brakes": {"temps": [round(300 + brake * 250 + i, 1) for i in range(4)], "bias": 0.56},
            "fuel": round(self._fuel, 2),
            "lap": {
                "current": lap,
                "current_time_ms": lap_ms,
                "last_time_ms": self._last_ms,
                "best_time_ms": self._best_ms,
            },
            "drs": {"available": 1 if corner > 0.8 else 0, "enabled": 0, "level": 0},
        }
