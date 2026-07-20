"""
iRacing telemetry via the iRacing SDK shared memory ("Local\\IRSDKMemMapFileName").

Unlike ACC/AC (fixed ctypes structs), iRacing publishes a *self-describing*
buffer: a header, a table of variable headers (name/type/offset), and up to 4
rotating telemetry buffers. We parse the variable table once at connect, then
read values by name from whichever buffer has the newest tickCount.

Layout is per the official irsdk_defines.h:
  irsdk_header    = 10 ints + 2 pad ints + irsdk_varBuf[4]   (112 bytes)
  irsdk_varBuf    = tickCount, bufOffset, pad[2]             (16 bytes)
  irsdk_varHeader = type, offset, count, countAsTime, pad[3],
                    name[32], desc[64], unit[32]             (144 bytes)
"""

import mmap
import re
import struct
import time

MEM_MAP_NAME = 'Local\\IRSDKMemMapFileName'

MAX_BUFS = 4
MAX_STRING = 32
MAX_DESC = 64
HEADER_SIZE = 112
VARBUF_SIZE = 16
VARHEADER_SIZE = 144
ST_CONNECTED = 1

# irsdk_VarType -> (struct format, size in bytes)
VAR_TYPES = {
    0: ('c', 1),   # char
    1: ('?', 1),   # bool
    2: ('i', 4),   # int
    3: ('I', 4),   # bitField
    4: ('f', 4),   # float
    5: ('d', 8),   # double
}


class IRacingTelemetry:
    """Reader with the same interface as the other games: connect/read/disconnect."""

    def __init__(self):
        self.mm = None
        self.connected = False
        self.last_tick = -1
        self.vars = {}          # name -> (type, offset, count)
        self.car_name = 'unknown'
        self.track_name = 'unknown'
        self._session_update = -1

    @property
    def is_connected(self) -> bool:
        return self.connected

    # ---- header helpers ---------------------------------------------------

    def _header(self):
        self.mm.seek(0)
        h = struct.unpack('<10i', self.mm.read(40))
        return {
            'ver': h[0], 'status': h[1], 'tick_rate': h[2],
            'session_info_update': h[3], 'session_info_len': h[4], 'session_info_offset': h[5],
            'num_vars': h[6], 'var_header_offset': h[7], 'num_buf': h[8], 'buf_len': h[9],
        }

    def _buffers(self):
        """The varBuf table: (tickCount, bufOffset) per buffer."""
        out = []
        for i in range(MAX_BUFS):
            self.mm.seek(48 + i * VARBUF_SIZE)
            tick, off = struct.unpack('<2i', self.mm.read(8))
            out.append((tick, off))
        return out

    def _read_var_table(self, hdr):
        """Parse the variable headers once — name -> (type, offset, count)."""
        table = {}
        for i in range(hdr['num_vars']):
            base = hdr['var_header_offset'] + i * VARHEADER_SIZE
            self.mm.seek(base)
            vtype, voff, vcount = struct.unpack('<3i', self.mm.read(12))
            self.mm.seek(base + 16)  # skip countAsTime + pad
            name = self.mm.read(MAX_STRING).split(b'\x00')[0].decode('latin-1', 'replace')
            if name:
                table[name] = (vtype, voff, vcount)
        return table

    def _read_session_yaml(self, hdr):
        """Session info is a YAML blob; we only need track + car names."""
        try:
            self.mm.seek(hdr['session_info_offset'])
            raw = self.mm.read(max(0, hdr['session_info_len'])).split(b'\x00')[0]
            text = raw.decode('latin-1', 'replace')
            track = re.search(r'^\s*TrackDisplayName:\s*(.+)$', text, re.M)
            if not track:
                track = re.search(r'^\s*TrackName:\s*(.+)$', text, re.M)
            car = re.search(r'^\s*CarScreenName:\s*(.+)$', text, re.M)
            if track:
                self.track_name = track.group(1).strip() or self.track_name
            if car:
                self.car_name = car.group(1).strip() or self.car_name
            self._session_update = hdr['session_info_update']
        except Exception:
            pass

    # ---- lifecycle --------------------------------------------------------

    def connect(self) -> bool:
        try:
            self.mm = mmap.mmap(-1, 0, MEM_MAP_NAME, access=mmap.ACCESS_READ)
            hdr = self._header()
            # Not just "the map exists" — the sim must report itself connected.
            if not (hdr['status'] & ST_CONNECTED) or hdr['num_vars'] <= 0:
                self.disconnect()
                return False
            self.vars = self._read_var_table(hdr)
            self._read_session_yaml(hdr)
            self.connected = True
            print('[OK] Connected to iRacing')
            return True
        except Exception:
            self.connected = False
            return False

    def disconnect(self):
        if self.mm:
            try:
                self.mm.close()
            except Exception:
                pass
        self.mm = None
        self.connected = False

    # ---- value access -----------------------------------------------------

    def _value(self, buf_offset, name, default=0):
        v = self.vars.get(name)
        if not v:
            return default
        vtype, voff, vcount = v
        fmt_size = VAR_TYPES.get(vtype)
        if not fmt_size:
            return default
        fmt, size = fmt_size
        try:
            self.mm.seek(buf_offset + voff)
            if vcount > 1:
                vals = struct.unpack('<' + fmt * vcount, self.mm.read(size * vcount))
                return list(vals)
            return struct.unpack('<' + fmt, self.mm.read(size))[0]
        except Exception:
            return default

    def _arr(self, buf_offset, name, idx, default=0):
        v = self._value(buf_offset, name, None)
        if isinstance(v, list):
            return v[idx] if idx < len(v) else default
        return v if v is not None else default

    def read(self):
        """One frame, or None when nothing new / the sim left."""
        if not self.connected:
            return None
        try:
            hdr = self._header()
            if not (hdr['status'] & ST_CONNECTED):
                self.connected = False
                return None

            # Newest buffer wins (the sim rotates through up to 4).
            bufs = [b for b in self._buffers()[:max(1, hdr['num_buf'])]]
            tick, off = max(bufs, key=lambda b: b[0])
            if tick == self.last_tick:
                return None  # no new frame yet
            self.last_tick = tick

            # Track/car change (new session) — refresh the YAML-derived names.
            if hdr['session_info_update'] != self._session_update:
                self._read_session_yaml(hdr)

            return self._parse(off)
        except Exception as e:
            print(f'Error reading iRacing telemetry: {e}')
            self.connected = False
            return None

    def current_ids(self):
        """Live (track, car) — lets the session monitor catch an in-place switch."""
        if self.connected and self.mm:
            try:
                self._read_session_yaml(self._header())
            except Exception:
                pass
        return (self.track_name, self.car_name)

    # ---- frame ------------------------------------------------------------

    def _steering_norm(self, off):
        """Wheel angle (radians) -> roughly -1..1, matching the AC/ACC contract."""
        ang = self._value(off, 'SteeringWheelAngle', 0.0) or 0.0
        lock = self._value(off, 'SteeringWheelAngleMax', 0.0) or 0.0
        if not lock or lock <= 0:
            lock = 4.5  # ~258 deg: sane fallback when the car doesn't publish it
        return max(-1.0, min(1.0, ang / lock))

    def _parse(self, off):
        g = lambda n, d=0: self._value(off, n, d)  # noqa: E731

        speed_ms = g('Speed', 0.0) or 0.0
        gear = g('Gear', 0)
        lap_pct = g('LapDistPct', 0.0) or 0.0

        return {
            'game': 'iracing',
            'timestamp': time.time(),
            'car_name': self.car_name,
            'track_name': self.track_name,
            'speed_kmh': speed_ms * 3.6,
            'rpm': g('RPM', 0.0),
            # The shared AC mapping applies gear-1 (AC: 0=R,1=N,2=1st). iRacing is
            # already -1=R,0=N,1=1st, so pre-add 1 to land on the same contract.
            'gear': gear + 1,
            # 0..1 — the shared AC mapping scales these to percent.
            'throttle': g('Throttle', 0.0),
            'brake': g('Brake', 0.0),
            'clutch': g('Clutch', 0.0),
            # iRacing reports the wheel angle in RADIANS; AC/ACC emit -1..1, so
            # normalise against the car's max lock to stay on the same scale.
            'steering': self._steering_norm(off),
            'fuel': g('FuelLevel', 0.0),
            # Contract: a list of 4 per-wheel dicts (FL, FR, RL, RR) — same as AC/ACC.
            'tires': [
                {'temp_core': self._arr(off, t, 1), 'pressure': g(p, 0.0), 'wear': self._arr(off, w, 1)}
                for t, p, w in (
                    ('LFtempCM', 'LFcoldPressure', 'LFwearM'),
                    ('RFtempCM', 'RFcoldPressure', 'RFwearM'),
                    ('LRtempCM', 'LRcoldPressure', 'LRwearM'),
                    ('RRtempCM', 'RRcoldPressure', 'RRwearM'),
                )
            ],
            'brakes': {'temps': [g(n, 0.0) for n in ('LFbrakeLinePress', 'RFbrakeLinePress', 'LRbrakeLinePress', 'RRbrakeLinePress')]},
            'lap': {
                'current': g('Lap', 0),
                'current_time_ms': int((g('LapCurrentLapTime', 0.0) or 0.0) * 1000),
                'last_time_ms': int((g('LapLastLapTime', 0.0) or 0.0) * 1000),
                'best_time_ms': int((g('LapBestLapTime', 0.0) or 0.0) * 1000),
                'is_valid_lap': True,
            },
            'drs': {'available': False, 'enabled': False},
            'ext': {
                # Position axis for corner detection / lap compare (0..1).
                'normalized_position': lap_pct,
                # iRacing exposes GPS lat/lon rather than world x/z — good enough
                # for the top-down track map (scaled the same way).
                'pos_x': g('Lon', 0.0),
                'pos_y': g('Alt', 0.0),
                'pos_z': g('Lat', 0.0),
                'g_lat': g('LatAccel', 0.0),
                'g_lon': g('LongAccel', 0.0),
                'track_grip_status': g('TrackTempCrew', 0.0),
                'fuel_remaining_liters': g('FuelLevel', 0.0),
                'session_time': g('SessionTime', 0.0),
            },
        }
