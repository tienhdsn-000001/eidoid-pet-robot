# pico_motor_controller.py
# This script runs on the Raspberry Pi Pico.
# It listens for JSON commands over USB serial to control two VEX 393 motors.

import machine
import time
import json
import select

# --- Configuration ---
# Assign GPIO pins for the motors.
# Ensure these are PWM-capable pins on your Pico.
LEFT_MOTOR_PIN = 16  # Example: GP16
RIGHT_MOTOR_PIN = 17 # Example: GP17
UART_ID = 0
BAUD_RATE = 115200

# VEX 393 motors are controlled like servos.
# PWM frequency is typically 50Hz.
PWM_FREQ = 50

# --- PWM Duty Cycle Calculation ---
# The Pico's PWM duty cycle is a 16-bit value (0-65535).
# We need to map the millisecond pulse width to this range.
# Period of 50Hz is 20ms.
def duty_for_ms(ms):
    """Converts a pulse width in milliseconds to a 16-bit duty cycle value."""
    if not 0.5 <= ms <= 2.5:
        ms = 1.5  # Safety check, default to stop
    return int((ms / 20.0) * 65535)

# Calculate duty cycles for standard motor commands
# Note: You may need to fine-tune these values slightly for your specific motors.
DUTY_FORWARD = duty_for_ms(2.0)  # Max speed one direction
DUTY_BACKWARD = duty_for_ms(1.0) # Max speed other direction
DUTY_STOP = duty_for_ms(1.5)     # Stop

# --- Initialization ---
# Initialize UART for communication with the Raspberry Pi 5
uart = machine.UART(UART_ID, baudrate=BAUD_RATE)

# Initialize PWM for left motor
pwm_left = machine.PWM(machine.Pin(LEFT_MOTOR_PIN))
pwm_left.freq(PWM_FREQ)
pwm_left.duty_u16(DUTY_STOP)

# Initialize PWM for right motor
pwm_right = machine.PWM(machine.Pin(RIGHT_MOTOR_PIN))
pwm_right.freq(PWM_FREQ)
pwm_right.duty_u16(DUTY_STOP)

print("Pico Motor Controller Initialized. Waiting for commands...")

# --- Motor Control Functions ---
def move_forward():
    print("Moving forward")
    pwm_left.duty_u16(DUTY_FORWARD)
    # To make the right motor spin in the same direction, we give it the opposite signal.
    pwm_right.duty_u16(DUTY_BACKWARD)

def move_backward():
    print("Moving backward")
    pwm_left.duty_u16(DUTY_BACKWARD)
    pwm_right.duty_u16(DUTY_FORWARD)

def turn_left():
    print("Turning left")
    pwm_left.duty_u16(DUTY_BACKWARD)
    pwm_right.duty_u16(DUTY_BACKWARD)

def turn_right():
    print("Turning right")
    pwm_left.duty_u16(DUTY_FORWARD)
    pwm_right.duty_u16(DUTY_FORWARD)

def stop_motors():
    print("Stopping motors")
    pwm_left.duty_u16(DUTY_STOP)
    pwm_right.duty_u16(DUTY_STOP)

# --- Main Loop ---
# Use select.poll() for non-blocking reads from UART
poller = select.poll()
poller.register(uart, select.POLLIN)

command_buffer = ""

while True:
    # Check if there is data available to be read
    if poller.poll(1): # 1ms timeout
        # Read the available characters
        char = uart.read(1).decode('utf-8')
        
        # If we receive a newline, we have a complete command
        if char == '\n':
            try:
                # Attempt to parse the buffered string as JSON
                command = json.loads(command_buffer)
                print(f"Received command: {command}")
                
                direction = command.get("direction")
                duration = command.get("duration_s", 0.0)
                
                # Execute the command
                if direction == "forward":
                    move_forward()
                elif direction == "backward":
                    move_backward()
                elif direction == "left":
                    turn_left()
                elif direction == "right":
                    turn_right()
                else: # Includes "stop" or any invalid command
                    stop_motors()
                
                # If a duration is specified, run for that time then stop
                if duration > 0:
                    time.sleep(float(duration))
                    stop_motors()
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error decoding JSON: {e}")
                print(f"Buffer content was: '{command_buffer}'")
                stop_motors() # Stop motors as a safety precaution
            finally:
                # Clear the buffer for the next command
                command_buffer = ""
        else:
            # Append the character to our buffer
            command_buffer += char
            # Safety break if buffer gets too long (prevents memory issues)
            if len(command_buffer) > 256:
                print("Buffer overflow, clearing.")
                command_buffer = ""
