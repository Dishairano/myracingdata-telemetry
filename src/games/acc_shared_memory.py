"""
Assetto Corsa Competizione (ACC) Telemetry Reader — shared memory.

ACC exposes the same Kunos shared memory as Assetto Corsa (acpmf_physics /
acpmf_graphics / acpmf_static). ACC's physics page is AC's with extra fields
appended, so the prefix games/ac.py already defines (gas, brake, clutch,
steerAngle, gear, rpms, speedKmh, tyres, brakeTemp, lap timing) reads correctly
for ACC too — mapping a smaller struct over ACC's larger buffer just reads the
shared prefix. This reader reuses those structs and ac.py's parse, so ACC
capture carries full driver inputs (which the UDP broadcasting reader in
games/acc.py cannot).

NOTE: the live byte layout is confirmed against a running ACC on the rig — same
unverified status AC's reader carries.
"""

import ctypes
import mmap

from games.ac import ACTelemetry, ACPhysics, ACGraphics


class ACCStatic(ctypes.Structure):
    """acpmf_static prefix — enough to read car model and track name."""
    _fields_ = [
        ('smVersion', ctypes.c_wchar * 15),
        ('acVersion', ctypes.c_wchar * 15),
        ('numberOfSessions', ctypes.c_int),
        ('numCars', ctypes.c_int),
        ('carModel', ctypes.c_wchar * 33),
        ('track', ctypes.c_wchar * 33),
        ('playerName', ctypes.c_wchar * 33),
        ('playerSurname', ctypes.c_wchar * 33),
        ('playerNick', ctypes.c_wchar * 33),
    ]


class ACCSharedMemoryReader(ACTelemetry):
    """Reads ACC telemetry from shared memory, reusing AC's physics/graphics parse."""

    def __init__(self):
        super().__init__()
        self.static_map = None
        self.car_name = "unknown"
        self.track_name = "unknown"

    def connect(self) -> bool:
        """Open ACC's physics, graphics and static shared-memory pages."""
        try:
            self.physics_map = mmap.mmap(-1, ctypes.sizeof(ACPhysics), "acpmf_physics")
            self.graphics_map = mmap.mmap(-1, ctypes.sizeof(ACGraphics), "acpmf_graphics")
            self.static_map = mmap.mmap(-1, ctypes.sizeof(ACCStatic), "acpmf_static")

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
        super().disconnect()
        if self.static_map:
            self.static_map.close()
            self.static_map = None

    def _parse_data(self, physics, graphics):
        """Reuse AC's field mapping, relabel as ACC and attach car/track."""
        data = super()._parse_data(physics, graphics)
        data['game'] = 'assetto_corsa_competizione'
        data['car_name'] = self.car_name
        data['track_name'] = self.track_name
        return data
