# led_controller.py — self-healing version with DTR/RTS "replug" pulse
import sys, time, threading, queue, glob
try:
    import serial
    from serial import SerialException
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from config import CONFIG

CTRL_D = b'\x04'  # soft reboot (Ctrl+D)
ACK_OK, ACK_PONG = "OK", "PONG"


# -------------------------------
# Background line reader
# -------------------------------
class LineReader(threading.Thread):
    def __init__(self, ser):
        super().__init__(daemon=True)
        self.ser = ser
        self.q = queue.Queue(maxsize=100)
        self._stop = threading.Event()

    def run(self):
        buf = bytearray()
        while not self._stop.is_set():
            try:
                chunk = self.ser.read(64)
            except Exception:
                break
            if chunk:
                buf.extend(chunk)
                while True:
                    for sep in (b"\n", b"\r"):
                        idx = buf.find(sep)
                        if idx != -1:
                            raw = bytes(buf[:idx]).decode(errors="ignore").strip()
                            del buf[:idx + 1]
                            if raw:
                                # print(f"[PICO] {raw}") # Can be noisy, uncomment for debugging
                                try: self.q.put_nowait(raw)
                                except queue.Full: pass
                            break
                    else:
                        break
            else:
                time.sleep(0.01)

    def stop(self): self._stop.set()
    def get_line(self, timeout=1.0):
        try: return self.q.get(timeout=timeout)
        except queue.Empty: return ""


# -------------------------------
# Main controller
# -------------------------------
class LEDController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False): return
        self._initialized = True
        self._ser = None
        self._reader = None
        self._newline = b"\r\n" if CONFIG["pico"].get("newline", "LF").upper() == "CRLF" else b"\n"
        if SERIAL_AVAILABLE: self._connect()
        else: print("[LED_CTRL] pyserial missing.", file=sys.stderr)

    # ---------- Discovery ----------
    def _discover_port(self, configured):
        # Raspberry Pi 5 USB serial device discovery
        if configured and "/dev/ttyUSB" in configured: return configured
        if configured and "/dev/ttyACM" in configured: return configured
        
        # Look for common Raspberry Pi 5 USB serial devices
        usb_devices = []
        usb_devices.extend(glob.glob("/dev/ttyUSB*"))
        usb_devices.extend(glob.glob("/dev/ttyACM*"))
        usb_devices.extend(glob.glob("/dev/tty.usbmodem*"))
        
        if usb_devices:
            return sorted(usb_devices)[0]
        
        # Fallback to configured port
        return configured

    # ---------- Connection ----------
    def _connect(self):
        port = self._discover_port(CONFIG["pico"]["serial_port"])
        baud = CONFIG["pico"]["baud_rate"]
        try:
            self._ser = serial.Serial(
                port=port,
                baudrate=baud,
                timeout=1.0,
                write_timeout=1.0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
        except SerialException as e:
            print(f"[LED_CTRL] Open failed: {e}", file=sys.stderr)
            return

        self._ser.rts = True
        self._ser.dtr = True
        time.sleep(0.15)
        print(f"[LED_CTRL] Port open: {port} @ {baud}. DTR=ON RTS=ON")

        self._reader = LineReader(self._ser)
        self._reader.start()

        if not self._handshake():
            print("[LED_CTRL] Handshake failed. Attempting auto-replug…")
            self._auto_replug()

    # ---------- Auto-replug & reboot ----------
    def _auto_replug(self):
        """Simulate unplug/replug + soft reboot if necessary."""
        try:
            self._ser.dtr = False; self._ser.rts = False; time.sleep(0.1)
            self._ser.dtr = True;  self._ser.rts = True;  time.sleep(0.3)
            print("[LED_CTRL] DTR/RTS pulse sent.")
            self._ser.reset_input_buffer(); self._ser.reset_output_buffer()
            self._ser.write(CTRL_D); self._ser.flush()
            time.sleep(1.2)
            self._ser.reset_input_buffer()
            self._send_line("PING")
            line = self._reader.get_line(timeout=1.0)
            if ACK_PONG in line:
                print("[LED_CTRL] Port re-armed successfully (auto-replug).")
            else:
                print("[LED_CTRL] Auto-replug attempted, but no PONG.", file=sys.stderr)
        except Exception as e:
            print(f"[LED_CTRL] Auto-replug failed: {e}", file=sys.stderr)

    # ---------- Helpers ----------
    def _send_line(self, text):
        if self._ser and self._ser.is_open:
            self._ser.write(text.encode("utf-8") + self._newline)
            self._ser.flush()
    def _read_line(self, timeout=1.0):
        if self._reader:
            return self._reader.get_line(timeout)
        return ""

    def _handshake(self):
        try:
            self._send_line("PING")
            line = self._read_line(timeout=1.0)
            if ACK_PONG in line:
                print("[LED_CTRL] Handshake OK.")
                return True
        except Exception: pass
        return False

    # ---------- Command sender with retry ----------
    def _send_expect_ok(self, cmd, retries=1):
        if not (self._ser and self._ser.is_open):
            return False
        for attempt in range(retries + 1):
            try:
                self._send_line(cmd)
            except SerialException:
                if attempt < retries: self._auto_replug()
                continue
            line = self._read_line(timeout=1.0)
            if ACK_OK in line: return True
            if attempt < retries:
                print(f"[LED_CTRL] No ACK for {cmd}, retrying…")
                self._auto_replug()
        return False

    # ---------- Public API ----------
    def turn_on(self):     return self._send_expect_ok("ON")
    def turn_off(self):    return self._send_expect_ok("OFF")
    def start_pulse(self): return self._send_expect_ok("PULSE_START")
    def stop_pulse(self):  return self._send_expect_ok("PULSE_STOP")
    # --- FIX: Removed the unsupported flash_disconnect command ---

    def close(self):
        if self._ser and self._ser.is_open:
            try: self.turn_off(); time.sleep(0.05)
            except Exception: pass
            try: self._reader.stop()
            except Exception: pass
            try: self._ser.close()
            except Exception: pass


# -------------------------------
# Singleton
# -------------------------------
led_controller = LEDController()

