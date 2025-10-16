# test_motors.py
# A simple script to run on a host computer (like a MacBook)
# to send motor commands to the Pico for testing purposes.

import serial
import json
import time
import sys

def send_command(ser, direction, duration):
    """Constructs and sends a JSON command to the Pico."""
    command = {
        "direction": direction,
        "duration_s": float(duration)
    }
    try:
        payload = json.dumps(command) + "\n"
        print(f"Sending: {payload.strip()}")
        ser.write(payload.encode('utf-8'))
        ser.flush()
    except Exception as e:
        print(f"Error sending command: {e}")

def main():
    """Main function to run the interactive motor test."""
    if len(sys.argv) < 2:
        print("Usage: python test_motors.py <serial_port>")
        print("Example: python test_motors.py /dev/tty.usbmodem12345")
        sys.exit(1)
        
    port_name = sys.argv[1]
    baud_rate = 115200

    print(f"Attempting to connect to Pico on {port_name} at {baud_rate} baud...")

    try:
        # The timeout is important so the script doesn't hang
        pico_serial = serial.Serial(port_name, baud_rate, timeout=1)
        # Allow time for the serial connection to establish
        time.sleep(2) 
        print("Successfully connected to Pico.")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port '{port_name}'.")
        print(f"Details: {e}")
        print("Please ensure the Pico is connected and you have the correct port name.")
        sys.exit(1)

    print("\n--- Interactive Motor Test ---")
    print("Commands:")
    print("  f - forward")
    print("  b - backward")
    print("  l - turn left")
    print("  r - turn right")
    print("  s - stop")
    print("  q - quit")
    print("----------------------------")

    try:
        while True:
            cmd = input("\nEnter command (f, b, l, r, s, q): ").lower().strip()

            if cmd == 'q':
                break
            
            if cmd not in ['f', 'b', 'l', 'r', 's']:
                print("Invalid command. Please try again.")
                continue

            if cmd == 's':
                send_command(pico_serial, "stop", 0)
                continue

            while True:
                try:
                    duration_str = input(f"Enter duration in seconds (e.g., 1.5): ")
                    duration = float(duration_str)
                    if duration > 0:
                        break
                    else:
                        print("Duration must be a positive number.")
                except ValueError:
                    print("Invalid number. Please enter a valid duration.")
            
            direction_map = {
                'f': 'forward',
                'b': 'backward',
                'l': 'left',
                'r': 'right'
            }
            
            send_command(pico_serial, direction_map[cmd], duration)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if 'pico_serial' in locals() and pico_serial.is_open:
            # Send one final stop command as a safety measure
            send_command(pico_serial, "stop", 0)
            pico_serial.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
