# led_controller.py
# Manages the state of the indicator LEDs by sending serial commands to a Pi Pico.

import sys
import time
try:
    import serial
except ImportError:
    print("[LED_CTRL] WARNING: pyserial library not found. LED functions will be simulated.", file=sys.stderr)
    # Create a dummy serial class if pyserial is not installed.
    # This allows the app to run without errors on a machine without a Pico connected.
    class serial:
        class Serial:
            def __init__(self, *args, **kwargs): pass
            def write(self, *args, **kwargs): pass
            def close(self, *args, **kwargs): pass
            def flush(self, *args, **kwargs): pass
        SerialException = Exception


from config import CONFIG

class LEDController:
    """A singleton class to manage the robot's indicator LED via a Pi Pico."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LEDController, cls).__new__(cls)
            cls._instance._ser = None
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """Establishes a serial connection to the Pico."""
        try:
            pico_port = CONFIG["pico"]["serial_port"]
            self._ser = serial.Serial(pico_port, 115200, timeout=1)
            # Allow time for the Pico's serial to initialize.
            time.sleep(2)
            print(f"[LED_CTRL] Connected to Pico on {pico_port}.")
        except serial.SerialException as e:
            print(f"[LED_CTRL] ERROR: Could not connect to Pico. Using dummy controller. Error: {e}", file=sys.stderr)
            # Fallback to a dummy object if connection fails.
            self._ser = serial.Serial()

    def _send_command(self, command: str):
        """Sends a command to the Pico over the serial connection."""
        if self._ser and self._ser.is_open:
            # Commands must be encoded to bytes and terminated with a newline character
            # for the Pico's readline() to work.
            self._ser.write(f"{command}\n".encode('utf-8'))
            self._ser.flush()

    def turn_on(self):
        """Turns the LED on to a solid state."""
        print("[LED_CTRL] Sending command: ON")
        self._send_command("ON")

    def turn_off(self):
        """Turns the LED off."""
        print("[LED_CTRL] Sending command: OFF")
        self._send_command("OFF")

    def start_pulse(self):
        """Starts the pulse effect on the Pico."""
        print("[LED_CTRL] Sending command: PULSE_START")
        self._send_command("PULSE_START")

    def stop_pulse(self):
        """Stops the pulse and returns the LED to a solid ON state."""
        print("[LED_CTRL] Sending command: PULSE_STOP")
        self._send_command("PULSE_STOP")

    def close(self):
        """Closes the serial connection."""
        if self._ser and self._ser.is_open:
            self.turn_off() # Ensure LED is off on exit.
            self._ser.close()
            print("[LED_CTRL] Serial connection to Pico closed.")

# Create a single, shared instance of the controller.
led_controller = LEDController()

