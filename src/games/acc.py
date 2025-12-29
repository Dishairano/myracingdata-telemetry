"""
Assetto Corsa Competizione (ACC) Telemetry Reader
Reads telemetry from ACC UDP Broadcasting Interface
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
from threading import Thread, Event as ThreadEvent

try:
    from accapi.client import AccClient, Event
except ImportError:
    AccClient = None
    Event = None  # Define Event as None when not available
    logging.warning("accapi not installed - ACC telemetry not available")

logger = logging.getLogger(__name__)


class ACCTelemetryReader:
    """
    Reads telemetry from Assetto Corsa Competizione using UDP Broadcasting

    Requires ACC Broadcasting to be enabled:
    - Edit: Documents/Assetto Corsa Competizione/Config/broadcasting.json
    - Set updListenerPort (default: 9232)
    - Set connectionPassword if needed
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9232,
        password: str = "",
        on_telemetry: Optional[Callable] = None
    ):
        """
        Initialize ACC telemetry reader

        Args:
            host: ACC host address (default: 127.0.0.1)
            port: ACC broadcasting port (default: 9232, configured in broadcasting.json)
            password: ACC connection password (from broadcasting.json)
            on_telemetry: Callback function(telemetry_data: dict) for telemetry updates
        """
        if AccClient is None:
            raise ImportError(
                "accapi library not installed. "
                "Install it with: pip install accapi"
            )

        self.host = host
        self.port = port
        self.password = password
        self.on_telemetry = on_telemetry

        self.client: Optional[AccClient] = None
        self.is_running = False
        self.stop_event = ThreadEvent()
        self.thread: Optional[Thread] = None

        # Latest telemetry data
        self.latest_realtime_update: Optional[Dict] = None
        self.latest_car_update: Optional[Dict] = None
        self.latest_telemetry: Optional[Dict] = None  # Formatted telemetry for polling
        self.track_data: Optional[Dict] = None
        self.entry_list: Dict[int, Dict] = {}

        # Session info
        self.session_id: Optional[str] = None
        self.session_type: str = "unknown"
        self.track_name: str = "unknown"
        self.car_model: str = "unknown"

        logger.info(f"ACC Telemetry Reader initialized (port: {port})")

    def start(self) -> bool:
        """Start telemetry capture"""
        if self.is_running:
            logger.warning("ACC telemetry reader already running")
            return False

        try:
            self.client = AccClient()

            # Subscribe to telemetry events
            self.client.onConnectionStateChange.subscribe(self._on_connection_state)
            self.client.onTrackDataUpdate.subscribe(self._on_track_data)
            self.client.onEntryListCarUpdate.subscribe(self._on_entry_list_update)
            self.client.onRealtimeUpdate.subscribe(self._on_realtime_update)
            self.client.onRealtimeCarUpdate.subscribe(self._on_realtime_car_update)
            self.client.onBroadcastingEvent.subscribe(self._on_broadcasting_event)

            # Start client in separate thread
            self.thread = Thread(target=self._run_client, daemon=True)
            self.is_running = True
            self.thread.start()

            logger.info("ACC telemetry reader started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start ACC telemetry reader: {e}")
            return False

    def stop(self):
        """Stop telemetry capture"""
        if not self.is_running:
            return

        logger.info("Stopping ACC telemetry reader...")
        self.stop_event.set()

        if self.client:
            try:
                self.client.stop()
            except Exception as e:
                logger.error(f"Error stopping ACC client: {e}")

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        self.is_running = False
        logger.info("ACC telemetry reader stopped")

    def _run_client(self):
        """Run ACC client in thread"""
        try:
            self.client.start(self.host, self.port, self.password)

            # Keep thread alive while client is running
            while not self.stop_event.is_set():
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in ACC client thread: {e}")
            self.is_running = False

    def _on_connection_state(self, event):
        """Handle connection state changes"""
        state = event.content
        logger.info(f"ACC connection state: {state}")

    def _on_track_data(self, event):
        """Handle track data update"""
        track_data = event.content

        # Extract track info
        if hasattr(track_data, 'trackName'):
            self.track_name = track_data.trackName

        # Store for later use
        self.track_data = self._event_to_dict(track_data)

        logger.debug(f"Track data updated: {self.track_name}")

    def _on_entry_list_update(self, event):
        """Handle entry list (car list) update"""
        car_data = event.content

        # Extract car info
        if hasattr(car_data, 'carIndex'):
            car_index = car_data.carIndex

            # Update car model for player car (index 0 usually)
            if car_index == 0 and hasattr(car_data, 'carModelType'):
                self.car_model = self._get_car_name(car_data.carModelType)

            # Store in entry list
            self.entry_list[car_index] = self._event_to_dict(car_data)

        logger.debug(f"Entry list updated (cars: {len(self.entry_list)})")

    def _on_realtime_update(self, event):
        """Handle realtime session update"""
        realtime_data = event.content

        # Extract session info
        if hasattr(realtime_data, 'sessionType'):
            self.session_type = self._get_session_type(realtime_data.sessionType)

        # Store realtime update
        self.latest_realtime_update = self._event_to_dict(realtime_data)

        logger.debug(f"Realtime update: {self.session_type}")

    def _on_realtime_car_update(self, event):
        """Handle realtime car telemetry update"""
        car_data = event.content

        # Store car update
        self.latest_car_update = self._event_to_dict(car_data)

        # Format telemetry data
        if hasattr(car_data, 'carIndex') and car_data.carIndex == 0:
            # Only process player car (index 0)
            telemetry = self._format_telemetry(car_data)
            self.latest_telemetry = telemetry  # Store for polling

            # Call callback if provided
            if self.on_telemetry:
                self.on_telemetry(telemetry)

    def _on_broadcasting_event(self, event):
        """Handle broadcasting events"""
        event_data = event.content
        logger.debug(f"Broadcasting event: {event_data.__class__.__name__}")

    def _format_telemetry(self, car_data) -> Dict[str, Any]:
        """
        Format ACC telemetry data to match MyRacingData API format
        """
        telemetry = {
            # Session info
            "sessionId": self.session_id or f"acc_{int(time.time())}",
            "sessionType": self.session_type,
            "trackName": self.track_name,
            "carModel": self.car_model,

            # Timing
            "timestamp": int(time.time() * 1000),  # ms

            # Basic telemetry
            "speed_kmh": getattr(car_data, 'kmh', 0),
            "gear": getattr(car_data, 'gear', 0) - 1,  # ACC gear is 0=R, 1=N, 2=1st, etc.
            "rpm": getattr(car_data, 'engineRpm', 0),

            # Lap data
            "current_lap_time_ms": getattr(car_data, 'currentLap', {}).get('lapTimeMs', 0) if hasattr(car_data, 'currentLap') else 0,
            "last_lap_time_ms": getattr(car_data, 'lastLap', {}).get('lapTimeMs', 0) if hasattr(car_data, 'lastLap') else 0,
            "best_lap_time_ms": getattr(car_data, 'bestSessionLap', {}).get('lapTimeMs', 0) if hasattr(car_data, 'bestSessionLap') else 0,
            "lap_count": getattr(car_data, 'laps', 0),

            # Position
            "position_x": getattr(car_data, 'worldPosX', 0),
            "position_y": getattr(car_data, 'worldPosY', 0),
            "position_z": getattr(car_data, 'worldPosZ', 0),

            # TODO: Add more telemetry fields as needed
            # ACC has extensive telemetry - map to MyRacingData format
        }

        return telemetry

    def _event_to_dict(self, event_obj) -> Dict:
        """Convert event object to dictionary"""
        if event_obj is None:
            return {}

        result = {}
        for attr in dir(event_obj):
            if not attr.startswith('_'):
                try:
                    value = getattr(event_obj, attr)
                    if not callable(value):
                        result[attr] = value
                except:
                    pass

        return result

    def _get_session_type(self, session_type_code: int) -> str:
        """Convert ACC session type code to string"""
        session_types = {
            0: "practice",
            1: "qualifying",
            2: "superpole",
            3: "race",
            4: "hotlap",
            5: "hotstint",
            6: "hotlapsuperpole",
            7: "replay",
        }
        return session_types.get(session_type_code, "unknown")

    def _get_car_name(self, car_model_code: int) -> str:
        """Convert ACC car model code to name"""
        # Simplified car mapping - add more as needed
        car_models = {
            0: "Porsche 911 GT3 R",
            1: "Mercedes-AMG GT3",
            2: "Ferrari 488 GT3",
            3: "Audi R8 LMS",
            4: "Lamborghini Huracan GT3",
            5: "McLaren 650S GT3",
            6: "Nissan GT-R Nismo GT3",
            7: "BMW M6 GT3",
            8: "Bentley Continental GT3",
            9: "Porsche 911 II GT3 Cup",
            # Add more car models as needed
        }
        return car_models.get(car_model_code, f"Unknown Car ({car_model_code})")

    def get_latest_telemetry(self) -> Optional[Dict[str, Any]]:
        """Get latest telemetry data (for polling mode)"""
        return self.latest_telemetry

    def is_connected(self) -> bool:
        """Check if connected to ACC"""
        return self.is_running and self.client is not None
