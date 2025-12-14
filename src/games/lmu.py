"""
Le Mans Ultimate (LMU) Telemetry Reader
Reads telemetry from LMU shared memory (rFactor 2 engine)
"""

import mmap
import ctypes
from typing import Optional, Dict, Any

# rFactor 2 / LMU Telemetry Structures

class Vec3(ctypes.Structure):
    """3D Vector"""
    _fields_ = [
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double)
    ]

class Wheel(ctypes.Structure):
    """Wheel telemetry data"""
    _fields_ = [
        ('rotation', ctypes.c_double),
        ('suspensionDeflection', ctypes.c_double),
        ('rideHeight', ctypes.c_double),
        ('tireLoad', ctypes.c_double),
        ('lateralForce', ctypes.c_double),
        ('gripFract', ctypes.c_double),
        ('brakeTemp', ctypes.c_double),
        ('pressure', ctypes.c_double),
        ('temperature', ctypes.c_double * 3),  # inside, middle, outside
        ('wear', ctypes.c_double),
        ('terrainName', ctypes.c_char * 16),
        ('surfaceType', ctypes.c_ubyte),
        ('flat', ctypes.c_bool),
        ('detached', ctypes.c_bool),
    ]

class VehicleTelemetry(ctypes.Structure):
    """Main vehicle telemetry structure for rF2/LMU"""
    _fields_ = [
        # Identification
        ('ID', ctypes.c_int),
        ('deltaTime', ctypes.c_double),
        ('elapsedTime', ctypes.c_double),
        ('lapNumber', ctypes.c_int),
        ('lapStartET', ctypes.c_double),
        ('vehicleName', ctypes.c_char * 64),
        ('trackName', ctypes.c_char * 64),
        
        # Position and velocity
        ('pos', Vec3),
        ('localVel', Vec3),
        ('localAccel', Vec3),
        
        # Orientation
        ('oriX', Vec3),
        ('oriY', Vec3),
        ('oriZ', Vec3),
        ('localRot', Vec3),
        ('localRotAccel', Vec3),
        
        # Vehicle status
        ('gear', ctypes.c_int),
        ('engineRPM', ctypes.c_double),
        ('engineWaterTemp', ctypes.c_double),
        ('engineOilTemp', ctypes.c_double),
        ('clutchRPM', ctypes.c_double),
        
        # Fuel
        ('fuel', ctypes.c_double),
        ('engineMaxRPM', ctypes.c_double),
        ('scheduledStops', ctypes.c_ubyte),
        ('overheating', ctypes.c_bool),
        ('detached', ctypes.c_bool),
        
        # Damage
        ('dentSeverity', ctypes.c_ubyte * 8),
        ('lastImpactET', ctypes.c_double),
        ('lastImpactMagnitude', ctypes.c_double),
        ('lastImpactPos', Vec3),
        
        # Wheels (4 wheels: FL, FR, RL, RR)
        ('wheels', Wheel * 4),
        
        # Speed
        ('speed', ctypes.c_double),
        
        # Input
        ('unfilteredThrottle', ctypes.c_double),
        ('unfilteredBrake', ctypes.c_double),
        ('unfilteredSteering', ctypes.c_double),
        ('unfilteredClutch', ctypes.c_double),
        
        # Filtered input (assists applied)
        ('filteredThrottle', ctypes.c_double),
        ('filteredBrake', ctypes.c_double),
        ('filteredSteering', ctypes.c_double),
        ('filteredClutch', ctypes.c_double),
        
        # Driver options
        ('steeringArmForce', ctypes.c_double),
        
        # Session data
        ('session', ctypes.c_int),
        ('currentSector', ctypes.c_int),
        ('trackLength', ctypes.c_double),
        ('pathLateral', ctypes.c_double),
        ('trackEdge', ctypes.c_double),
        
        # Flags
        ('lapDist', ctypes.c_double),
        ('headlights', ctypes.c_bool),
        ('pitLimiter', ctypes.c_bool),
        ('yellowFlagState', ctypes.c_int),
        
        # Scoring info
        ('inPits', ctypes.c_bool),
        ('place', ctypes.c_ubyte),
        ('vehicleClass', ctypes.c_char * 32),
        
        # Environmental
        ('trackTemp', ctypes.c_double),
        ('ambientTemp', ctypes.c_double),
        ('windSpeed', ctypes.c_double),
        ('onPathOffPath', ctypes.c_double),
        
        # Pit status
        ('numPitstops', ctypes.c_int),
        ('numPenalties', ctypes.c_int),
        
        # Timing
        ('sector1', ctypes.c_double),
        ('sector2', ctypes.c_double),
        ('curSector1', ctypes.c_double),
        ('curSector2', ctypes.c_double),
        
        # Best times
        ('bestSector1', ctypes.c_double),
        ('bestSector2', ctypes.c_double),
        ('bestLapTime', ctypes.c_double),
        ('lastLapTime', ctypes.c_double),
        ('curLapTime', ctypes.c_double),
        
        # Additional physics
        ('frontWingHeight', ctypes.c_double),
        ('frontRideHeight', ctypes.c_double),
        ('rearRideHeight', ctypes.c_double),
        ('drag', ctypes.c_double),
        ('frontDownforce', ctypes.c_double),
        ('rearDownforce', ctypes.c_double),
    ]

class LMUTelemetry:
    """Le Mans Ultimate telemetry reader"""
    
    def __init__(self):
        self.shared_memory = None
        self.connected = False
        self.last_update = 0
    
    def connect(self) -> bool:
        """Connect to LMU shared memory"""
        try:
            # Try rFactor 2 shared memory names
            memory_names = [
                "$rFactor2SMMP_Telemetry$",
                "rFactor2SMMP_Telemetry",
                "Local\\rFactor2SMMP_Telemetry"
            ]
            
            for name in memory_names:
                try:
                    self.shared_memory = mmap.mmap(
                        -1,
                        ctypes.sizeof(VehicleTelemetry),
                        name
                    )
                    self.connected = True
                    print(f"✓ Connected to Le Mans Ultimate (using {name})")
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Failed to connect to LMU: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from shared memory"""
        if self.shared_memory:
            self.shared_memory.close()
        self.connected = False
    
    def read(self) -> Optional[Dict[str, Any]]:
        """Read telemetry data from shared memory"""
        if not self.connected or not self.shared_memory:
            return None
        
        try:
            # Read raw data
            self.shared_memory.seek(0)
            raw_data = self.shared_memory.read(ctypes.sizeof(VehicleTelemetry))
            vehicle = VehicleTelemetry.from_buffer_copy(raw_data)
            
            # Check if data is updated
            if vehicle.elapsedTime == self.last_update:
                return None
            
            self.last_update = vehicle.elapsedTime
            
            # Parse into structured format
            return self._parse_data(vehicle)
            
        except Exception as e:
            print(f"Error reading LMU telemetry: {e}")
            self.connected = False
            return None
    
    def _parse_data(self, vehicle: VehicleTelemetry) -> Dict[str, Any]:
        """Parse LMU data into MyRacingData format"""
        
        import time
        
        return {
            'game': 'le_mans_ultimate',
            'timestamp': time.time(),
            
            # Vehicle identification
            'vehicle': {
                'id': vehicle.ID,
                'name': vehicle.vehicleName.decode('utf-8', errors='ignore'),
                'class': vehicle.vehicleClass.decode('utf-8', errors='ignore')
            },
            
            # Track info
            'track': {
                'name': vehicle.trackName.decode('utf-8', errors='ignore'),
                'length': vehicle.trackLength,
                'temp': vehicle.trackTemp,
                'ambient_temp': vehicle.ambientTemp,
                'wind_speed': vehicle.windSpeed
            },
            
            # Basic car state
            'speed_kmh': vehicle.speed * 3.6,  # m/s to km/h
            'rpm': vehicle.engineRPM,
            'max_rpm': vehicle.engineMaxRPM,
            'gear': vehicle.gear,
            
            # Inputs (unfiltered = driver, filtered = with assists)
            'input_raw': {
                'throttle': vehicle.unfilteredThrottle,
                'brake': vehicle.unfilteredBrake,
                'steering': vehicle.unfilteredSteering,
                'clutch': vehicle.unfilteredClutch
            },
            'input_filtered': {
                'throttle': vehicle.filteredThrottle,
                'brake': vehicle.filteredBrake,
                'steering': vehicle.filteredSteering,
                'clutch': vehicle.filteredClutch
            },
            
            # Position & velocity
            'position': {
                'x': vehicle.pos.x,
                'y': vehicle.pos.y,
                'z': vehicle.pos.z
            },
            'velocity': {
                'x': vehicle.localVel.x,
                'y': vehicle.localVel.y,
                'z': vehicle.localVel.z
            },
            'acceleration': {
                'x': vehicle.localAccel.x,
                'y': vehicle.localAccel.y,
                'z': vehicle.localAccel.z
            },
            
            # Rotation
            'rotation': {
                'x': vehicle.localRot.x,
                'y': vehicle.localRot.y,
                'z': vehicle.localRot.z
            },
            'rotation_acceleration': {
                'x': vehicle.localRotAccel.x,
                'y': vehicle.localRotAccel.y,
                'z': vehicle.localRotAccel.z
            },
            
            # Orientation vectors
            'orientation': {
                'x': {'x': vehicle.oriX.x, 'y': vehicle.oriX.y, 'z': vehicle.oriX.z},
                'y': {'x': vehicle.oriY.x, 'y': vehicle.oriY.y, 'z': vehicle.oriY.z},
                'z': {'x': vehicle.oriZ.x, 'y': vehicle.oriZ.y, 'z': vehicle.oriZ.z}
            },
            
            # G-forces (from acceleration)
            'g_force': {
                'lateral': vehicle.localAccel.x / 9.81,
                'longitudinal': vehicle.localAccel.z / 9.81,
                'vertical': vehicle.localAccel.y / 9.81
            },
            
            # Engine
            'engine': {
                'rpm': vehicle.engineRPM,
                'max_rpm': vehicle.engineMaxRPM,
                'water_temp': vehicle.engineWaterTemp,
                'oil_temp': vehicle.engineOilTemp,
                'clutch_rpm': vehicle.clutchRPM,
                'overheating': vehicle.overheating
            },
            
            # Fuel
            'fuel': vehicle.fuel,
            
            # Tires (4 wheels: FL, FR, RL, RR)
            'tires': [
                {
                    'position': pos,
                    'rotation': vehicle.wheels[i].rotation,
                    'suspension_deflection': vehicle.wheels[i].suspensionDeflection,
                    'ride_height': vehicle.wheels[i].rideHeight,
                    'load': vehicle.wheels[i].tireLoad,
                    'lateral_force': vehicle.wheels[i].lateralForce,
                    'grip': vehicle.wheels[i].gripFract,
                    'brake_temp': vehicle.wheels[i].brakeTemp,
                    'pressure': vehicle.wheels[i].pressure,
                    'temp_inner': vehicle.wheels[i].temperature[0],
                    'temp_middle': vehicle.wheels[i].temperature[1],
                    'temp_outer': vehicle.wheels[i].temperature[2],
                    'wear': vehicle.wheels[i].wear,
                    'terrain': vehicle.wheels[i].terrainName.decode('utf-8', errors='ignore'),
                    'surface_type': vehicle.wheels[i].surfaceType,
                    'flat': vehicle.wheels[i].flat,
                    'detached': vehicle.wheels[i].detached
                }
                for i, pos in enumerate(['front_left', 'front_right', 'rear_left', 'rear_right'])
            ],
            
            # Aerodynamics
            'aero': {
                'front_wing_height': vehicle.frontWingHeight,
                'front_ride_height': vehicle.frontRideHeight,
                'rear_ride_height': vehicle.rearRideHeight,
                'drag': vehicle.drag,
                'front_downforce': vehicle.frontDownforce,
                'rear_downforce': vehicle.rearDownforce
            },
            
            # Damage
            'damage': {
                'dents': [vehicle.dentSeverity[i] for i in range(8)],
                'last_impact_time': vehicle.lastImpactET,
                'last_impact_magnitude': vehicle.lastImpactMagnitude,
                'last_impact_pos': {
                    'x': vehicle.lastImpactPos.x,
                    'y': vehicle.lastImpactPos.y,
                    'z': vehicle.lastImpactPos.z
                },
                'detached': vehicle.detached
            },
            
            # Lap timing
            'lap': {
                'number': vehicle.lapNumber,
                'distance': vehicle.lapDist,
                'start_time': vehicle.lapStartET,
                'current_time': vehicle.curLapTime,
                'last_time': vehicle.lastLapTime,
                'best_time': vehicle.bestLapTime,
                
                # Sectors
                'current_sector': vehicle.currentSector,
                'sector_1_current': vehicle.curSector1,
                'sector_2_current': vehicle.curSector2,
                'sector_1_last': vehicle.sector1,
                'sector_2_last': vehicle.sector2,
                'sector_1_best': vehicle.bestSector1,
                'sector_2_best': vehicle.bestSector2
            },
            
            # Session
            'session': {
                'type': vehicle.session,
                'elapsed_time': vehicle.elapsedTime,
                'delta_time': vehicle.deltaTime,
                'position': vehicle.place,
                'in_pits': vehicle.inPits,
                'num_pitstops': vehicle.numPitstops,
                'num_penalties': vehicle.numPenalties,
                'scheduled_stops': vehicle.scheduledStops
            },
            
            # Track position
            'track_position': {
                'lateral': vehicle.pathLateral,
                'track_edge': vehicle.trackEdge,
                'on_path': vehicle.onPathOffPath
            },
            
            # Flags & controls
            'flags': {
                'yellow': vehicle.yellowFlagState,
                'pit_limiter': vehicle.pitLimiter,
                'headlights': vehicle.headlights
            },
            
            # Force feedback
            'force_feedback': vehicle.steeringArmForce
        }
    
    @property
    def is_connected(self) -> bool:
        return self.connected
