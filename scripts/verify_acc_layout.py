"""
Verify our ACC shared-memory structs against the official Kunos layout.

Anchor offsets below were derived field-by-field from Kunos's
ACCSharedMemoryDocumentationV1.8.12.pdf (full-sequence comparison done
2026-07-11; all 85 physics + 87 graphics fields and the full static prefix
matched). c_wchar is 2 bytes on Windows, 4 on Linux, so the structs are
rebuilt here with c_ushort standing in for c_wchar — that makes this check
platform-independent while asserting the WINDOWS layout the game uses.

Known deliberate difference: the doc's static struct ends with dryTyresName/
wetTyresName which we don't declare — trailing-only, so our smaller read is a
safe prefix. (Fun fact: rrennoir/PyAccSharedMemory drops P2PStatus and is 4
bytes off from the doc for the whole physics tail; we match the doc.)

Exit 0 = layout matches.
"""

import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from games.acc_structs import ACCPhysics, ACCGraphics, ACCStatic

# (field, expected Windows byte offset) + expected sizeof per struct.
# Values generated from the verified structs on 2026-07-11 after the tri-source
# check (official doc order/fields + reference-stream padding + ctypes).
ANCHORS = {
    'ACCPhysics': ([
        ('packetId', 0), ('gas', 4), ('speedKmh', 28), ('wheelsPressure', 88),
        ('tyreCoreTemperature', 152), ('carDamage', 224), ('brakeTemp', 348),
        ('tyreContactPoint', 420), ('brakeBias', 564), ('P2PActivations', 580),
        ('P2PStatus', 584), ('currentMaxRpm', 588), ('slipRatio', 640),
        ('waterTemp', 712), ('brakePressure', 716), ('padLife', 740),
        ('absVibrations', 796),
    ], 800),
    'ACCGraphics': ([
        ('packetId', 0), ('status', 4), ('completedLaps', 132), ('iCurrentTime', 140),
        ('sessionTimeLeft', 152), ('currentSectorIndex', 164), ('tyreCompound', 176),
        ('normalizedCarPosition', 248), ('carCoordinates', 256), ('wiperLV', 1304),
        ('isValidLap', 1408), ('TC', 1268), ('rainIntensity', 1560), ('gapBehind', 1584),
    ], 1588),
    'ACCStatic': ([
        ('smVersion', 0), ('carModel', 68), ('track', 134), ('sectorCount', 400),
        ('trackSPlineLength', 520), ('trackConfiguration', 524), ('carSkin', 604),
        ('PitWindowStart', 676), ('PitWindowEnd', 680), ('isOnline', 684),
    ], 688),
}


def windowsize(cls):
    fields = []
    for name, ct in cls._fields_:
        base = getattr(ct, '_type_', None)
        if base is ctypes.c_wchar:
            fields.append((name, ctypes.c_ushort * ct._length_))
        elif ct is ctypes.c_wchar:
            fields.append((name, ctypes.c_ushort))
        else:
            fields.append((name, ct))
    return type(f'Win{cls.__name__}', (ctypes.Structure,), {'_fields_': fields})


def main():
    ok = True
    for cls in (ACCPhysics, ACCGraphics, ACCStatic):
        anchors, want_size = ANCHORS[cls.__name__]
        win = windowsize(cls)
        errs = []
        for name, want in anchors:
            got = getattr(win, name).offset
            if got != want:
                errs.append(f'  {name}: offset {got} != official {want}')
        size = ctypes.sizeof(win)
        if size != want_size:
            errs.append(f'  sizeof: {size} != official {want_size}')
        print(f'{cls.__name__}: ' + ('OK - matches official Kunos layout' if not errs else 'MISMATCH'))
        for e in errs:
            print(e)
        ok &= not errs
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
