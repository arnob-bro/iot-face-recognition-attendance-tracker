import logging

logger = logging.getLogger(__name__)

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class ESP32Bridge:
    """Minimal serial bridge to an ESP32-based door controller."""

    def __init__(self, port: str = "", baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.available = False
        self.ser = None

        if not port:
            logger.warning("No ESP32 serial port configured; bridge disabled.")
            return

        if serial is None:
            logger.warning("pyserial is not installed; ESP32 bridge disabled.")
            return

        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            self.available = True
            logger.info(f"ESP32 bridge connected on {port}.")
        except Exception as exc:  # serial.SerialException is the common case
            logger.warning(f"ESP32 serial port unavailable ({port}): {exc}")
            self.available = False

    def send(self, command: str) -> None:
        if not self.available or self.ser is None:
            return
        try:
            self.ser.write((command + "\n").encode("utf-8"))
            self.ser.flush()
        except Exception as exc:
            logger.warning(f"ESP32 command failed: {command} -> {exc}")
            self.available = False

    def open_door(self) -> None:
        self.send("OPEN")

    def buzz(self) -> None:
        self.send("BUZZ")

    def led_green(self) -> None:
        self.send("LED_GREEN")

    def led_red(self) -> None:
        self.send("LED_RED")

    def close(self) -> None:
        if self.ser is not None:
            self.ser.close()
            self.ser = None
        self.available = False
