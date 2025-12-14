"""
Assetto Corsa Telemetry Reader
Reads telemetry from AC shared memory
"""

import mmap
import struct
import ctypes
from typing import Optional, Dict, Any

class ACPhysics(ctypes.Structure):
    """Assetto Corsa Physics shared memory structure"""
    _fields_ = [
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
        ('wheelLoad', ctypes.c_float * 4),
        ('wheelsPressure', ctypes.c_float * 4),
        ('wheelAngularSpeed', ctypes.c_float * 4),
        ('tyreWear', ctypes.c_float * 4),
        ('tyreDirtyLevel', ctypes.c_float * 4),
        ('tyreCoreTemperature', ctypes.c_float * 4),
        ('camberRAD', ctypes.c_float * 4),
        ('suspensionTravel', ctypes.c_float * 4),
        ('drs', ctypes.c_float),
        ('tc', ctypes.c_float),
        ('heading', ctypes.c_float),
        ('pitch', ctypes.c_float),
        ('roll', ctypes.c_float),
        ('cgHeight', ctypes.c_float),
        ('carDamage', ctypes.c_float * 5),
        ('numberOfTyresOut', ctypes.c_int),
        ('pitLimiterOn', ctypes.c_int),
        ('abs', ctypes.c_float),
        ('kersCharge', ctypes.c_float),
        ('kersInput', ctypes.c_float),
        ('autoShifterOn', ctypes.c_int),
        ('rideHeight', ctypes.c_float * 2),
        ('turboBoost', ctypes.c_float),
        ('ballast', ctypes.c_float),
        ('airDensity', ctypes.c_float),
        ('airTemp', ctypes.c_float),
        ('roadTemp', ctypes.c_float),
        ('localAngularVel', ctypes.c_float * 3),
        ('finalFF', ctypes.c_float),
        ('performanceMeter', ctypes.c_float),
        ('engineBrake', ctypes.c_int),
        ('ersRecoveryLevel', ctypes.c_int),
        ('ersPowerLevel', ctypes.c_int),
        ('ersHeatCharging', ctypes.c_int),
        ('ersIsCharging', ctypes.c_int),
        ('kersCurrentKJ', ctypes.c_float),
        ('drsAvailable', ctypes.c_int),
        ('drsEnabled', ctypes.c_int),
        ('brakeTemp', ctypes.c_float * 4),
        ('clutch', ctypes.c_float),
        ('tyreTempI', ctypes.c_float * 4),
        ('tyreTempM', ctypes.c_float * 4),
        ('tyreTempO', ctypes.c_float * 4),
        ('isAIControlled', ctypes.c_int),
        ('tyreContactPoint', ctypes.c_float * 4 * 3),
        ('tyreContactNormal', ctypes.c_float * 4 * 3),
        ('tyreContactHeading', ctypes.c_float * 4 * 3),
        ('brakeBias', ctypes.c_float),
        ('localVelocity', ctypes.c_float * 3),
    ]

class ACGraphics(ctypes.Structure):
    """Assetto Corsa Graphics shared memory structure"""
    _fields_ = [
        ('packetId', ctypes.c_int),
        ('AC_STATUS', ctypes.c_int),
        ('AC_SESSION_TYPE', ctypes.c_int),
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
        ('carCoordinates', ctypes.c_float * 3),
        ('penaltyTime', ctypes.c_float),
        ('flag', ctypes.c_int),
        ('idealLineOn', ctypes.c_int),
        ('isInPitLane', ctypes.c_int),
        ('surfaceGrip', ctypes.c_float),
        ('mandatoryPitDone', ctypes.c_int),
        ('windSpeed', ctypes.c_float),
        ('windDirection', ctypes.c_float),
    ]

class ACTelemetry:
    """Assetto Corsa telemetry reader"""
    
    def __init__(self):
        self.physics_map = None
        self.graphics_map = None
        self.connected = False
        self.last_packet_id = -1
    
    def connect(self) -> bool:
        """Connect to Assetto Corsa shared memory"""
        try:
            # Try to open physics shared memory
            self.physics_map = mmap.mmap(-1, ctypes.sizeof(ACPhysics), "acpmf_physics")
            self.graphics_map = mmap.mmap(-1, ctypes.sizeof(ACGraphics), "acpmf_graphics")
            self.connected = True
            print("✓ Connected to Assetto Corsa")
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from shared memory"""
        if self.physics_map:
            self.physics_map.close()
        if self.graphics_map:
            self.graphics_map.close()
        self.connected = False
    
    def read(self) -> Optional[Dict[str, Any]]:
        """Read telemetry data from shared memory"""
        if not self.connected:
            return None
        
        try:
            # Read physics data
            self.physics_map.seek(0)
            physics_raw = self.physics_map.read(ctypes.sizeof(ACPhysics))
            physics = ACPhysics.from_buffer_copy(physics_raw)
            
            # Read graphics data
            self.graphics_map.seek(0)
            graphics_raw = self.graphics_map.read(ctypes.sizeof(ACGraphics))
            graphics = ACGraphics.from_buffer_copy(graphics_raw)
            
            # Check if data is updated
            if physics.packetId == self.last_packet_id:
                return None
            
            self.last_packet_id = physics.packetId
            
            # Parse into structured format
            return self._parse_data(physics, graphics)
            
        except Exception as e:
            print(f"Error reading AC telemetry: {e}")
            self.connected = False
            return None
    
    def _parse_data(self, physics: ACPhysics, graphics: ACGraphics) -> Dict[str, Any]:
        """Parse AC data into MyRacingData format"""
        
        import time
        
        return {
            'game': 'assetto_corsa',
            'timestamp': time.time(),
            
            # Basic car state
            'speed_kmh': physics.speedKmh,
            'rpm': physics.rpms,
            'gear': physics.gear,
            'throttle': physics.gas,
            'brake': physics.brake,
            'clutch': physics.clutch,
            'steering': physics.steerAngle,
            
            # Position & rotation
            'position': {
                'x': graphics.carCoordinates[0],
                'y': graphics.carCoordinates[1],
                'z': graphics.carCoordinates[2]
            },
            'velocity': {
                'x': physics.velocity[0],
                'y': physics.velocity[1],
                'z': physics.velocity[2]
            },
            'local_velocity': {
                'x': physics.localVelocity[0],
                'y': physics.localVelocity[1],
                'z': physics.localVelocity[2]
            },
            'rotation': {
                'heading': physics.heading,
                'pitch': physics.pitch,
                'roll': physics.roll
            },
            
            # G-forces
            'g_force': {
                'lateral': physics.accG[0],
                'longitudinal': physics.accG[1],
                'vertical': physics.accG[2]
            },
            
            # Tires (4 wheels: FL, FR, RL, RR)
            'tires': [
                {
                    'position': pos,
                    'pressure': physics.wheelsPressure[i],
                    'temp_core': physics.tyreCoreTemperature[i],
                    'temp_inner': physics.tyreTempI[i],
                    'temp_middle': physics.tyreTempM[i],
                    'temp_outer': physics.tyreTempO[i],
                    'wear': physics.tyreWear[i],
                    'slip': physics.wheelSlip[i],
                    'load': physics.wheelLoad[i],
                    'angular_speed': physics.wheelAngularSpeed[i],
                    'dirty_level': physics.tyreDirtyLevel[i],
                    'camber': physics.camberRAD[i],
                    'suspension_travel': physics.suspensionTravel[i]
                }
                for i, pos in enumerate(['front_left', 'front_right', 'rear_left', 'rear_right'])
            ],
            
            # Brakes
            'brakes': {
                'temps': [physics.brakeTemp[i] for i in range(4)],
                'bias': physics.brakeBias
            },
            
            # Fuel & Engine
            'fuel': physics.fuel,
            'turbo_boost': physics.turboBoost,
            'engine_brake': physics.engineBrake,
            
            # Aerodynamics & Electronics
            'drs': {
                'available': physics.drsAvailable,
                'enabled': physics.drsEnabled,
                'level': physics.drs
            },
            'tc': physics.tc,
            'abs': physics.abs,
            'pit_limiter': physics.pitLimiterOn,
            
            # ERS/KERS
            'ers': {
                'charge': physics.kersCharge,
                'input': physics.kersInput,
                'current_kj': physics.kersCurrentKJ,
                'recovery_level': physics.ersRecoveryLevel,
                'power_level': physics.ersPowerLevel,
                'is_charging': physics.ersIsCharging,
                'heat_charging': physics.ersHeatCharging
            },
            
            # Damage
            'damage': {
                'front': physics.carDamage[0],
                'rear': physics.carDamage[1],
                'left': physics.carDamage[2],
                'right': physics.carDamage[3],
                'center': physics.carDamage[4]
            },
            
            # Lap & Session info
            'lap': {
                'current': graphics.completedLaps,
                'current_time_ms': graphics.iCurrentTime,
                'last_time_ms': graphics.iLastTime,
                'best_time_ms': graphics.iBestTime,
                'sector': graphics.currentSectorIndex,
                'last_sector_time_ms': graphics.lastSectorTime
            },
            
            # Session
            'session': {
                'type': graphics.AC_SESSION_TYPE,
                'status': graphics.AC_STATUS,
                'time_left': graphics.sessionTimeLeft,
                'position': graphics.position,
                'distance_traveled': graphics.distanceTraveled,
                'normalized_position': graphics.normalizedCarPosition,
                'is_in_pit': graphics.isInPit,
                'is_in_pit_lane': graphics.isInPitLane,
                'flag': graphics.flag
            },
            
            # Track conditions
            'track': {
                'air_temp': physics.airTemp,
                'road_temp': physics.roadTemp,
                'surface_grip': graphics.surfaceGrip,
                'wind_speed': graphics.windSpeed,
                'wind_direction': graphics.windDirection
            },
            
            # Additional physics
            'ride_height': {
                'front': physics.rideHeight[0],
                'rear': physics.rideHeight[1]
            },
            'cg_height': physics.cgHeight,
            'air_density': physics.airDensity,
            'performance_meter': physics.performanceMeter,
            'force_feedback': physics.finalFF,
            
            # Misc
            'tyres_out': physics.numberOfTyresOut,
            'tyre_compound': graphics.tyreCompound,
            'is_ai_controlled': physics.isAIControlled
        }
    
    @property
    def is_connected(self) -> bool:
        return self.connected
