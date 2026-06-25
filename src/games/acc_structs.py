"""
Full ACC shared-memory structures (SPageFilePhysics / SPageFileGraphics /
SPageFileStatic).

The physics prefix up to `localVelocity` and the graphics prefix up to
`normalizedCarPosition` are identical to Assetto Corsa (and rig-confirmed via
the basic reader). Past those points ACC diverges — notably ACC's graphics page
inserts `activeCars` + a `carCoordinates[60][3]` array — so reading the rich
channels (slip ratio/angle, tyre forces, pad/disc life, surface grip, weather,
predictive delta) requires these ACC-specific layouts rather than the AC structs.

Field order follows the published Kunos ACC SDK layout. `sizeof` is logged on
import so it can be checked against the live page size on the rig.
"""

import ctypes
import logging

logger = logging.getLogger(__name__)


class ACCPhysics(ctypes.Structure):
    """SPageFilePhysics — updated every physics tick (the realtime page)."""
    _fields_ = [
        # --- shared AC/ACC prefix (rig-confirmed) ---
        ('packetId', ctypes.c_int),
        ('gas', ctypes.c_float),
        ('brake', ctypes.c_float),
        ('fuel', ctypes.c_float),
        ('gear', ctypes.c_int),
        ('rpms', ctypes.c_int),
        ('steerAngle', ctypes.c_float),
        ('speedKmh', ctypes.c_float),
        ('velocity', ctypes.c_float * 3),
        ('accG', ctypes.c_float * 3),
        ('wheelSlip', ctypes.c_float * 4),
        ('wheelLoad', ctypes.c_float * 4),          # not used in ACC
        ('wheelsPressure', ctypes.c_float * 4),
        ('wheelAngularSpeed', ctypes.c_float * 4),
        ('tyreWear', ctypes.c_float * 4),           # not used in ACC
        ('tyreDirtyLevel', ctypes.c_float * 4),     # not used in ACC
        ('tyreCoreTemperature', ctypes.c_float * 4),
        ('camberRAD', ctypes.c_float * 4),          # not used in ACC
        ('suspensionTravel', ctypes.c_float * 4),
        ('drs', ctypes.c_float),                    # not used in ACC
        ('tc', ctypes.c_float),
        ('heading', ctypes.c_float),
        ('pitch', ctypes.c_float),
        ('roll', ctypes.c_float),
        ('cgHeight', ctypes.c_float),               # not used in ACC
        ('carDamage', ctypes.c_float * 5),
        ('numberOfTyresOut', ctypes.c_int),
        ('pitLimiterOn', ctypes.c_int),
        ('abs', ctypes.c_float),
        ('kersCharge', ctypes.c_float),             # not used in ACC
        ('kersInput', ctypes.c_float),              # not used in ACC
        ('autoShifterOn', ctypes.c_int),
        ('rideHeight', ctypes.c_float * 2),
        ('turboBoost', ctypes.c_float),
        ('ballast', ctypes.c_float),                # not used in ACC
        ('airDensity', ctypes.c_float),
        ('airTemp', ctypes.c_float),
        ('roadTemp', ctypes.c_float),
        ('localAngularVel', ctypes.c_float * 3),
        ('finalFF', ctypes.c_float),
        ('performanceMeter', ctypes.c_float),       # not used in ACC
        ('engineBrake', ctypes.c_int),              # not used in ACC
        ('ersRecoveryLevel', ctypes.c_int),         # not used in ACC
        ('ersPowerLevel', ctypes.c_int),            # not used in ACC
        ('ersHeatCharging', ctypes.c_int),          # not used in ACC
        ('ersIsCharging', ctypes.c_int),            # not used in ACC
        ('kersCurrentKJ', ctypes.c_float),          # not used in ACC
        ('drsAvailable', ctypes.c_int),             # not used in ACC
        ('drsEnabled', ctypes.c_int),               # not used in ACC
        ('brakeTemp', ctypes.c_float * 4),
        ('clutch', ctypes.c_float),
        ('tyreTempI', ctypes.c_float * 4),          # not used in ACC
        ('tyreTempM', ctypes.c_float * 4),          # not used in ACC
        ('tyreTempO', ctypes.c_float * 4),          # not used in ACC
        ('isAIControlled', ctypes.c_int),
        ('tyreContactPoint', ctypes.c_float * 3 * 4),
        ('tyreContactNormal', ctypes.c_float * 3 * 4),
        ('tyreContactHeading', ctypes.c_float * 3 * 4),
        ('brakeBias', ctypes.c_float),
        ('localVelocity', ctypes.c_float * 3),
        # --- ACC-specific extension (the rich channels) ---
        ('P2PActivations', ctypes.c_int),           # not used in ACC
        ('P2PStatus', ctypes.c_int),                # not used in ACC
        ('currentMaxRpm', ctypes.c_int),
        ('mz', ctypes.c_float * 4),                 # tyre self-aligning torque
        ('fx', ctypes.c_float * 4),                 # tyre longitudinal force
        ('fy', ctypes.c_float * 4),                 # tyre lateral force
        ('slipRatio', ctypes.c_float * 4),
        ('slipAngle', ctypes.c_float * 4),
        ('tcinAction', ctypes.c_int),               # deprecated
        ('absInAction', ctypes.c_int),              # deprecated
        ('suspensionDamage', ctypes.c_float * 4),
        ('tyreTemp', ctypes.c_float * 4),
        ('waterTemp', ctypes.c_float),
        ('brakePressure', ctypes.c_float * 4),
        ('frontBrakeCompound', ctypes.c_int),
        ('rearBrakeCompound', ctypes.c_int),
        ('padLife', ctypes.c_float * 4),
        ('discLife', ctypes.c_float * 4),
        ('ignitionOn', ctypes.c_int),
        ('starterEngineOn', ctypes.c_int),
        ('isEngineRunning', ctypes.c_int),
        ('kerbVibration', ctypes.c_float),
        ('slipVibrations', ctypes.c_float),
        ('gVibrations', ctypes.c_float),
        ('absVibrations', ctypes.c_float),
    ]


class ACCGraphics(ctypes.Structure):
    """SPageFileGraphics — session / timing / conditions (updated per frame)."""
    _fields_ = [
        # --- shared AC/ACC prefix (rig-confirmed through normalizedCarPosition) ---
        ('packetId', ctypes.c_int),
        ('status', ctypes.c_int),
        ('session', ctypes.c_int),
        ('currentTime', ctypes.c_wchar * 15),
        ('lastTime', ctypes.c_wchar * 15),
        ('bestTime', ctypes.c_wchar * 15),
        ('split', ctypes.c_wchar * 15),
        ('completedLaps', ctypes.c_int),
        ('position', ctypes.c_int),
        ('iCurrentTime', ctypes.c_int),
        ('iLastTime', ctypes.c_int),
        ('iBestTime', ctypes.c_int),
        ('sessionTimeLeft', ctypes.c_float),
        ('distanceTraveled', ctypes.c_float),
        ('isInPit', ctypes.c_int),
        ('currentSectorIndex', ctypes.c_int),
        ('lastSectorTime', ctypes.c_int),
        ('numberOfLaps', ctypes.c_int),
        ('tyreCompound', ctypes.c_wchar * 33),
        ('replayTimeMultiplier', ctypes.c_float),
        ('normalizedCarPosition', ctypes.c_float),
        # --- ACC diverges here (AC had carCoordinates[3]) ---
        ('activeCars', ctypes.c_int),
        ('carCoordinates', ctypes.c_float * 3 * 60),
        ('carID', ctypes.c_int * 60),
        ('playerCarID', ctypes.c_int),
        ('penaltyTime', ctypes.c_float),
        ('flag', ctypes.c_int),
        ('penalty', ctypes.c_int),
        ('idealLineOn', ctypes.c_int),
        ('isInPitLane', ctypes.c_int),
        ('surfaceGrip', ctypes.c_float),
        ('mandatoryPitDone', ctypes.c_int),
        ('windSpeed', ctypes.c_float),
        ('windDirection', ctypes.c_float),
        ('isSetupMenuVisible', ctypes.c_int),
        ('mainDisplayIndex', ctypes.c_int),
        ('secondaryDisplayIndex', ctypes.c_int),
        ('TC', ctypes.c_int),
        ('TCCut', ctypes.c_int),
        ('EngineMap', ctypes.c_int),
        ('ABS', ctypes.c_int),
        ('fuelXLap', ctypes.c_float),
        ('rainLights', ctypes.c_int),
        ('flashingLights', ctypes.c_int),
        ('lightsStage', ctypes.c_int),
        ('exhaustTemperature', ctypes.c_float),
        ('wiperLV', ctypes.c_int),
        ('driverStintTotalTimeLeft', ctypes.c_int),
        ('driverStintTimeLeft', ctypes.c_int),
        ('rainTyres', ctypes.c_int),
        ('sessionIndex', ctypes.c_int),
        ('usedFuel', ctypes.c_float),
        ('deltaLapTime', ctypes.c_wchar * 15),
        ('iDeltaLapTime', ctypes.c_int),            # predictive delta (ms)
        ('estimatedLapTime', ctypes.c_wchar * 15),
        ('iEstimatedLapTime', ctypes.c_int),
        ('isDeltaPositive', ctypes.c_int),
        ('iSplit', ctypes.c_int),
        ('isValidLap', ctypes.c_int),
        ('fuelEstimatedLaps', ctypes.c_float),
        ('trackStatus', ctypes.c_wchar * 33),
        ('missingMandatoryPits', ctypes.c_int),
        ('Clock', ctypes.c_float),
        ('directionLightsLeft', ctypes.c_int),
        ('directionLightsRight', ctypes.c_int),
        ('globalYellow', ctypes.c_int),
        ('globalYellow1', ctypes.c_int),
        ('globalYellow2', ctypes.c_int),
        ('globalYellow3', ctypes.c_int),
        ('globalWhite', ctypes.c_int),
        ('globalGreen', ctypes.c_int),
        ('globalChequered', ctypes.c_int),
        ('globalRed', ctypes.c_int),
        ('mfdTyreSet', ctypes.c_int),
        ('mfdFuelToAdd', ctypes.c_float),
        ('mfdTyrePressureLF', ctypes.c_float),
        ('mfdTyrePressureRF', ctypes.c_float),
        ('mfdTyrePressureLR', ctypes.c_float),
        ('mfdTyrePressureRR', ctypes.c_float),
        ('trackGripStatus', ctypes.c_int),
        ('rainIntensity', ctypes.c_int),
        ('rainIntensityIn10min', ctypes.c_int),
        ('rainIntensityIn30min', ctypes.c_int),
        ('currentTyreSet', ctypes.c_int),
        ('strategyTyreSet', ctypes.c_int),
        ('gapAhead', ctypes.c_int),
        ('gapBehind', ctypes.c_int),
    ]


class ACCStatic(ctypes.Structure):
    """SPageFileStatic — set once at session start (identity / car / track)."""
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
        ('sectorCount', ctypes.c_int),
        ('maxTorque', ctypes.c_float),
        ('maxPower', ctypes.c_float),
        ('maxRpm', ctypes.c_int),
        ('maxFuel', ctypes.c_float),
        ('suspensionMaxTravel', ctypes.c_float * 4),
        ('tyreRadius', ctypes.c_float * 4),
        ('maxTurboBoost', ctypes.c_float),
        ('deprecated1', ctypes.c_float),
        ('deprecated2', ctypes.c_float),
        ('penaltiesEnabled', ctypes.c_int),
        ('aidFuelRate', ctypes.c_float),
        ('aidTireRate', ctypes.c_float),
        ('aidMechanicalDamage', ctypes.c_float),
        ('aidAllowTyreBlankets', ctypes.c_float),
        ('aidStability', ctypes.c_float),
        ('aidAutoClutch', ctypes.c_int),
        ('aidAutoBlip', ctypes.c_int),
        ('hasDRS', ctypes.c_int),
        ('hasERS', ctypes.c_int),
        ('hasKERS', ctypes.c_int),
        ('kersMaxJ', ctypes.c_float),
        ('engineBrakeSettingsCount', ctypes.c_int),
        ('ersPowerControllerCount', ctypes.c_int),
        ('trackSPlineLength', ctypes.c_float),
        ('trackConfiguration', ctypes.c_wchar * 33),
        ('ersMaxJ', ctypes.c_float),
        ('isTimedRace', ctypes.c_int),
        ('hasExtraLap', ctypes.c_int),
        ('carSkin', ctypes.c_wchar * 33),
        ('reversedGridPositions', ctypes.c_int),
        ('PitWindowStart', ctypes.c_int),
        ('PitWindowEnd', ctypes.c_int),
        ('isOnline', ctypes.c_int),
    ]


# Logged so the layout can be checked against the live shared-memory page size
# on the rig (a mismatch means a field offset is wrong).
logger.info(
    "ACC struct sizes — physics=%d graphics=%d static=%d bytes",
    ctypes.sizeof(ACCPhysics), ctypes.sizeof(ACCGraphics), ctypes.sizeof(ACCStatic),
)
