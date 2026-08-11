#!/usr/bin/env python3
"""
PIN DIAGNOSTIC - Tests each GPIO pin individually
Run: sudo python3 pin_diagnostic.py
"""
import time

print("=" * 60)
print("GPIO PIN DIAGNOSTIC TOOL")
print("=" * 60)

# Import gpiod
try:
    import gpiod
    from gpiod.line import Value
    print("\n[OK] gpiod library loaded")
except ImportError:
    print("\n[ERROR] gpiod not found. Install: sudo apt install python3-gpiod")
    exit(1)

# Pins to test (from config.py)
pins = [
    ('IN1', 17),
    ('IN2', 18),
    ('IN3', 22),
    ('IN4', 23),
    ('ENA', 27),
    ('ENB', 25)
]

print(f"\nTesting {len(pins)} pins individually...")
print("Each pin will be set HIGH for 3 seconds.")
print("Use a multimeter to check voltage at each pin.\n")

try:
    chip = gpiod.Chip('/dev/gpiochip0')

    for name, pin in pins:
        print(f"--- Testing {name} (GPIO {pin}) ---")

        # Request the line
        line = chip.get_line(pin)
        line.request(consumer="diagnostic", type=gpiod.LINE_REQ_DIR_OUT)

        # Set LOW first
        print(f"  Setting {name} LOW...")
        line.set_value(0)
        time.sleep(1)

        # Set HIGH
        print(f"  Setting {name} HIGH (CHECK WITH MULTIMETER NOW!)")
        line.set_value(1)
        time.sleep(3)

        # Set LOW again
        print(f"  Setting {name} LOW...")
        line.set_value(0)
        time.sleep(0.5)

        # Release
        line.release()
        print(f"  [OK] {name} test complete\n")

    chip.close()
    print("=" * 60)
    print("ALL PINS TESTED!")
    print("=" * 60)
    print("\nIf any pin didn't change state:")
    print("1. Check wiring - pin might not be connected")
    print("2. Try different pins: 5, 6, 13, 19, 26, 16")
    print("3. Make sure you're running with sudo")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
