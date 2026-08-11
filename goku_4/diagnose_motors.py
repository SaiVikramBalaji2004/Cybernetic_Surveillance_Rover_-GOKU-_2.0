#!/usr/bin/env python3
"""
Motor Pin Diagnostic Tool
Tests each motor pin individually to identify which pins work
"""
import time
import gpiod
from gpiod.line import Value

# Motor pins
IN1 = 17
IN2 = 18
IN3 = 22
IN4 = 23
ENA = 27
ENB = 25

print("=" * 60)
print("MOTOR PIN DIAGNOSTIC TOOL")
print("=" * 60)
print(f"\nTesting pins: IN1={IN1}, IN2={IN2}, IN3={IN3}, IN4={IN4}, ENA={ENA}, ENB={ENB}")
print("\nEach pin will be set HIGH for 2 seconds.")
print("Use a multimeter or LED to verify each pin changes state.")
print("Press Ctrl+C to stop\n")

try:
    chip = gpiod.Chip('/dev/gpiochip0')
    pins = [IN1, IN2, IN3, IN4, ENA, ENB]
    pin_names = ['IN1', 'IN2', 'IN3', 'IN4', 'ENA', 'ENB']

    # Configure all pins as outputs
    config = {
        pin: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            drive=gpiod.line.Drive.PUSH_PULL
        ) for pin in pins
    }
    request = chip.request_lines(config=config, consumer="motor_diagnostic")

    # Set all pins LOW initially
    for pin in pins:
        request.set_value(pin, Value.INACTIVE)
    print("All pins set to LOW initially")
    time.sleep(2)

    # Test each pin individually
    for i, (pin, name) in enumerate(zip(pins, pin_names)):
        print(f"\n>>> Setting {name} (GPIO {pin}) to HIGH for 2 seconds...")
        request.set_value(pin, Value.ACTIVE)
        time.sleep(2)

        print(f">>> Setting {name} (GPIO {pin}) to LOW...")
        request.set_value(pin, Value.INACTIVE)
        time.sleep(1)

    # Test forward pattern
    print("\n" + "=" * 60)
    print("Testing FORWARD pattern (IN1=HIGH, IN2=LOW, IN3=HIGH, IN4=LOW)")
    print("=" * 60)
    request.set_value(IN1, Value.ACTIVE)
    time.sleep(0.5)
    request.set_value(IN2, Value.INACTIVE)
    time.sleep(0.5)
    request.set_value(IN3, Value.ACTIVE)
    time.sleep(0.5)
    request.set_value(IN4, Value.INACTIVE)
    print("Forward pattern set. ENA and ENB should also be HIGH.")
    request.set_value(ENA, Value.ACTIVE)
    request.set_value(ENB, Value.ACTIVE)
    time.sleep(3)

    # Stop
    print("\nStopping - all pins to LOW")
    for pin in pins:
        request.set_value(pin, Value.INACTIVE)

    # Cleanup
    request.release()
    chip.close()
    print("\nDiagnostic complete!")

except KeyboardInterrupt:
    print("\nStopped by user")
except Exception as e:
    print(f"\nError: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure you're running with sudo: sudo python3 diagnose_motors.py")
    print("2. Check that /dev/gpiochip0 exists")
    print("3. Verify wiring - pins might be different than expected")
    print("4. Some GPIO pins on Pi 5 have different functions - try pins 5, 6, 13, 19, 26")
