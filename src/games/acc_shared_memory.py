"""
Assetto Corsa Competizione (ACC) Telemetry Reader — shared memory.

Reads the full ACC shared-memory pages (see games/acc_structs.py) so capture
carries not just the basics but the rich engineer channels: per-tyre slip
ratio/angle, tyre forces (Fx/Fy/Mz), brake pressure, pad/disc life, suspension
damage, normalized track position, surface grip, weather and the predictive
delta. Emits the AC-shaped core (consumed by normalize_acc) plus an `ext` dict
of the rich channels (stored server-side as JSON).

NOTE: the physics/graphics prefixes are rig-confirmed; the ACC-specific
extensions are validated on the rig (sanity-check the values — slip angle in
radians, brake pressure 0-1, pad life decreasing, normalized_position 0-1).
"""

import ctypes
import mmap
import time

from games.acc_structs import ACCPhysics, ACCGraphics, ACCStatic

WHEELS = ['fl', 'fr', 'rl', 'rr']


class ACCSharedMemoryReader:
    """Reads ACC telemetry from shared memory (full physics + graphics + static)."""

    def __init__(self):
        self.physics_map = None
        self.graphics_map = None
        self.static_map = None
        self.connected = False
        self.last_packet_id = -1
        self.car_name = "unknown"
        self.track_name = "unknown"

    @property
    def is_connected(self) -> bool:
        return self.connected

    def connect(self) -> bool:
        """Open ACC's physics, graphics and static shared-memory pages."""
        try:
            self.physics_map = mmap.mmap(-1, ctypes.sizeof(ACCPhysics), "acpmf_physics")
            self.graphics_map = mmap.mmap(-1, ctypes.sizeof(ACCGraphics), "acpmf_graphics")
            self.static_map = mmap.mmap(-1, ctypes.sizeof(ACCStatic), "acpmf_static")

            # mmap(-1, name) CREATES the region on Windows if no sim is running,
            # so "opened" is not "a sim is live". The graphics status (AC_OFF=0,
            # REPLAY=1, LIVE=2, PAUSE=3) tells us a session is actually running.
            gfx = ACCGraphics.from_buffer_copy(self.graphics_map.read(ctypes.sizeof(ACCGraphics)))
            if gfx.status == 0:
                self.disconnect()
                return False

            static = ACCStatic.from_buffer_copy(self.static_map.read(ctypes.sizeof(ACCStatic)))
            self.car_name = static.carModel or "unknown"
            self.track_name = static.track or "unknown"

            self.connected = True
            print("[OK] Connected to Assetto Corsa Competizione")
            return True
        except Exception:
            self.connected = False
            return False

    def disconnect(self):
        """Close all shared-memory pages."""
        for m in (self.physics_map, self.graphics_map, self.static_map):
            if m:
                try:
                    m.close()
                except Exception:
                    pass
        self.physics_map = self.graphics_map = self.static_map = None
        self.connected = False

    def read(self):
        """Read one frame (None if no new physics packet yet)."""
        if not self.connected:
            return None
        try:
            # Read graphics first to check session status — when the driver
            # leaves to the menu/exits, status -> AC_OFF while the physics packet
            # id just freezes, so this is what lets us detect "session finished".
            self.graphics_map.seek(0)
            gfx = ACCGraphics.from_buffer_copy(self.graphics_map.read(ctypes.sizeof(ACCGraphics)))
            if gfx.status == 0:
                self.connected = False
                return None

            self.physics_map.seek(0)
            phys = ACCPhysics.from_buffer_copy(self.physics_map.read(ctypes.sizeof(ACCPhysics)))
            if phys.packetId == self.last_packet_id:
                return None
            self.last_packet_id = phys.packetId
            return self._parse(phys, gfx)
        except Exception as e:
            print(f"Error reading ACC telemetry: {e}")
            self.connected = False
            return None

    def _parse(self, p, g):
        """AC-shaped core (for normalize_acc) + an `ext` dict of rich channels."""
        return {
            'game': 'assetto_corsa_competizione',
            'timestamp': time.time(),
            'car_name': self.car_name,
            'track_name': self.track_name,
            # core (consumed by normalize_acc via the shared AC mapping)
            'speed_kmh': p.speedKmh,
            'rpm': p.rpms,
            'gear': p.gear,
            'throttle': p.gas,
            'brake': p.brake,
            'clutch': p.clutch,
            'steering': p.steerAngle,
            'fuel': p.fuel,
            'tires': [
                {'temp_core': p.tyreCoreTemperature[i], 'pressure': p.wheelsPressure[i], 'wear': None}
                for i in range(4)
            ],
            'brakes': {'temps': [p.brakeTemp[i] for i in range(4)]},
            'lap': {
                'current': g.completedLaps,
                'current_time_ms': g.iCurrentTime,
                'last_time_ms': g.iLastTime,
                'best_time_ms': g.iBestTime,
            },
            # 1 while the current lap is clean; ACC flips it to 0 the moment the
            # lap is invalidated (track limits / cut). Used to mark lap validity.
            'is_valid_lap': 1 if g.isValidLap == 1 else 0,
            'drs': {'available': 0, 'enabled': 0},
            'ext': self._ext(p, g),
        }

    def _ext(self, p, g):
        """The rich ACC channels, stored server-side as a JSON blob."""
        ext = {}
        # Player world position (x, y=elevation, z) for the track reconstruction.
        pidx = 0
        try:
            for i in range(60):
                if g.carID[i] == g.playerCarID:
                    pidx = i
                    break
        except Exception:
            pidx = 0
        ext['pos_x'] = round(g.carCoordinates[pidx][0], 2)
        ext['pos_y'] = round(g.carCoordinates[pidx][1], 2)
        ext['pos_z'] = round(g.carCoordinates[pidx][2], 2)
        for i, w in enumerate(WHEELS):
            ext[f'slip_ratio_{w}'] = round(p.slipRatio[i], 4)
            ext[f'slip_angle_{w}'] = round(p.slipAngle[i], 4)
            ext[f'tyre_force_fx_{w}'] = round(p.fx[i], 1)
            ext[f'tyre_force_fy_{w}'] = round(p.fy[i], 1)
            ext[f'tyre_force_mz_{w}'] = round(p.mz[i], 2)
            ext[f'brake_pressure_{w}'] = round(p.brakePressure[i], 4)
            ext[f'pad_life_{w}'] = round(p.padLife[i], 2)
            ext[f'disc_life_{w}'] = round(p.discLife[i], 2)
            ext[f'suspension_damage_{w}'] = round(p.suspensionDamage[i], 3)
            ext[f'suspension_travel_{w}'] = round(p.suspensionTravel[i], 4)
            ext[f'wheel_slip_{w}'] = round(p.wheelSlip[i], 3)
        ext.update({
            'water_temp': round(p.waterTemp, 1),
            'current_max_rpm': p.currentMaxRpm,
            'tc_active': round(p.tc, 3),
            'abs_active': round(p.abs, 3),
            'air_temp': round(p.airTemp, 1),
            'road_temp': round(p.roadTemp, 1),
            'g_lat': round(p.accG[0], 3),
            'g_lon': round(p.accG[1], 3),
            'g_vert': round(p.accG[2], 3),
            'turbo_boost': round(p.turboBoost, 3),
            'normalized_position': round(g.normalizedCarPosition, 5),
            'surface_grip': round(g.surfaceGrip, 4),
            'wind_speed': round(g.windSpeed, 2),
            'wind_direction': round(g.windDirection, 2),
            'predictive_delta_ms': g.iDeltaLapTime,
            'is_valid_lap': g.isValidLap,
            'fuel_per_lap': round(g.fuelXLap, 3),
            'track_grip_status': g.trackGripStatus,
            'rain_intensity': g.rainIntensity,
            'current_sector': g.currentSectorIndex,
        })
        return ext
