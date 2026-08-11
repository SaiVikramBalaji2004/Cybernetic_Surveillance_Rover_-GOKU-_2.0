#!/usr/bin/env python3
"""
GPIO Pin Diagnostic - Tests EACH PIN INDIVIDUALLY
Run: sudo python3 diagnose_all.py

This will help identify which pins actually work on your Pi 5
"""
import time

print("=" * 60)
print("GPIO PIN DIAGNOSTIC FOR RASPBERRY PI 5")
print("=" * 60)

# Import gpiod
try:
    import gpiod
    from gpiod.line import Value
    print("\n[OK] gpiod library loaded")
except ImportError:
    print("\n[ERROR] gpiod not found. Install: sudo apt install python3-gpiod")
    exit(1)

# Original pins from config.py
ORIGINAL_PINS = [
    ('IN1', 17),
    ('IN2', 18),
    ('IN3', 22),
    ('IN4', 23),
    ('ENA', 27),
    ('ENB', 25)
]

# Alternate pins (known to work on Pi 5)
ALTERNATE_PINS = [
    ('IN1', 5),
    ('IN2', 6),
    ('IN3', 13),
    ('IN4', 19),
    ('ENA', 26),
    ('ENB', 16)
]

print("\n" + "="*60)
print("PART 1: TESTING ORIGINAL PINS")
print("="*60)
print("Pins: IN1=17, IN2=18, IN3=22, IN4=23, ENA=27, ENB=25")
print("Each pin will be set HIGH for 3 seconds.")
print("Use a multimeter to check voltage at EACH PIN.\n")

def test_pin_individually(pin, name):
    """Test a single GPIO pin"""
    try:
        chip = gpiod.Chip('/dev/gpiochip0')
        line = chip.get_line(pin)
        line.request(consumer=f"test_{name}", type=gpiod.LINE_REQ_DIR_OUT)

        print(f"--- Testing {name} (GPIO {pin}) ---")
        print(f"  Setting {name} HIGH (CHECK VOLTAGE NOW!)")
        line.set_value(1)
        time.sleep(3)

        print(f"  Setting {name} LOW")
        line.set_value(0)
        time.sleep(0.5)

        line.release()
        chip.close()
        print(f"  [OK] {name} test complete\n")
        return True
    except Exception as e:
        print(f"  [ERROR] {name} failed: {e}\n")
        return False

# Test original pins
original_results = {}
for name, pin in ORIGINAL_PINS:
    original_results[name] = test_pin_individually(pin, name)

print("="*60)
print("PART 2: TESTING ALTERNATE PINS")
print("="*60)
print("Alternate pins: IN1=5, IN2=6, IN3=13, IN4=19, ENA=26, ENB=16")
print("Each pin will be set HIGH for 3 seconds.\n")

# Test alternate pins
alternate_results = {}
for name, pin in ALTERNATE_PINS:
    alternate_results[name] = test_pin_individually(pin, name)

print("="*60)
print("SUMMARY OF RESULTS")
print("="*60)

print("\nORIGINAL PINS:")
for name, result in original_results.items():
    status = "WORKS" if result else "FAILED"
    print(f"  {name} (GPIO {dict(ORIGINAL_PINS)[name]}): {status}")

print("\nALTERNATE PINS:")
for name, result in alternate_results.items():
    status = "WORKS" if result else "FAILED"
    print(f"  {name} (GPIO {dict(ALTERNATE_PINS)[name]}): {status}")

print("\n" + "="*60)
print("RECOMMENDATION")
print("="*60)

failed_original = [name for name, result in original_results.items() if not result]
if failed_original:
    print(f"\nPins that FAILED: {', '.join(failed_original)}")
    print("\nSOLUTION: Use the ALTERNATE PINS instead!")
    print("\nUpdate your code to use:")
    print("  IN1 = GPIO 5 (was 17)")
    print("  IN2 = GPIO 6 (was 18)")
    print("  IN3 = GPIO 13 (was 22)")
    print("  IN4 = GPIO 19 (was 23)")
    print("  ENA = GPIO 26 (was 27)")
    print("  ENB = GPIO 16 (was 25)")
    print("\nRun this command to use the fixed version:")
    print("  sudo python3 /home/sai/Desktop/goku_4/voice_rover_final.py")
else:
    print("\nAll original pins work! The issue might be:")
    print("1. Wiring problem - check motor driver connections")
    print("2. Motor driver issue - try a different L298N module")
    print("3. Power issue - make sure 12V supply is connected")

print("\n" + "="*60)
print("NEXT STEP")
print("="*60)
print("\nIf alternate pins work, edit config.py and change:")
print("  MOTOR_PINS = {")
print("      'IN1': 5,")
print("      'IN2': 6,")
print("      'IN3': 13,")
print("      'IN4': 19,")
print("      'ENA': 26,")
print("      'ENB': 16,")
print("  }")
