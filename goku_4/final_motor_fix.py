#!/usr/bin/env python3
"""
FINAL MOTOR FIX - Tests pins and provides working solution
Run: sudo python3 final_motor_fix.py
"""
import time
import gpiod
from gpiod.line import Value

print("="*60)
print("FINAL MOTOR DIAGNOSTIC & FIX")
print("="*60)

# Original pins from config.py
ORIGINAL = [(17, 'IN1'), (18, 'IN2'), (22, 'IN3'), (23, 'IN4'), (27, 'ENA'), (25, 'ENB')]

# Alternate pins (more reliable on Pi 5)
ALTERNATE = [(5, 'IN1'), (6, 'IN2'), (13, 'IN3'), (19, 'IN4'), (26, 'ENA'), (16, 'ENB')]

def test_pin(chip, pin, name):
    """Test a single pin"""
    try:
        line = chip.get_line(pin)
        line.request(consumer=f"test_{name}", type=gpiod.LINE_REQ_DIR_OUT)

        # Set HIGH
        line.set_value(1)
        time.sleep(0.5)
        val_high = line.get_value()

        # Set LOW
        line.set_value(0)
        time.sleep(0.5)
        val_low = line.get_value()

        line.release()

        if val_high == 1 and val_low == 0:
            return True, "OK"
        else:
            return False, f"HIGH={val_high}, LOW={val_low}"
    except Exception as e:
        return False, str(e)

# Test original pins
print("\n" + "="*60)
print("TESTING ORIGINAL PINS")
print("="*60)
print("Pins: IN1=17, IN2=18, IN3=22, IN4=23, ENA=27, ENB=25\n")

chip = gpiod.Chip('/dev/gpiochip0')
original_results = {}

for pin, name in ORIGINAL:
    success, msg = test_pin(chip, pin, name)
    original_results[name] = success
    status = "WORKS" if success else "FAILED"
    print(f"  {name} (GPIO {pin}): {status} - {msg}")

# Test alternate pins
print("\n" + "="*60)
print("TESTING ALTERNATE PINS")
print("="*60)
print("Pins: IN1=5, IN2=6, IN3=13, IN4=19, ENA=26, ENB=16\n")

alternate_results = {}

for pin, name in ALTERNATE:
    success, msg = test_pin(chip, pin, name)
    alternate_results[name] = success
    status = "WORKS" if success else "FAILED"
    print(f"  {name} (GPIO {pin}): {status} - {msg}")

chip.close()

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

failed_original = [name for name, result in original_results.items() if not result]
failed_alternate = [name for name, result in alternate_results.items() if not result]

if failed_original:
    print(f"\nFAILED ORIGINAL PINS: {', '.join(failed_original)}")
    print("These pins are NOT working on your Pi 5!")
else:
    print("\nAll original pins work!")

if failed_alternate:
    print(f"\nFAILED ALTERNATE PINS: {', '.join(failed_alternate)}")
else:
    print("\nAll alternate pins work!")

# Recommendation
print("\n" + "="*60)
print("RECOMMENDATION")
print("="*60)

if failed_original and not failed_alternate:
    print("\nUSE ALTERNATE PINS! Update config.py with:")
    print("""
MOTOR_PINS = {
    'IN1': 5,
    'IN2': 6,
    'IN3': 13,
    'IN4': 19,
    'ENA': 26,
    'ENB': 16,
}
""")
    print("Then run: sudo python3 final_test_with_alt_pins.py")
elif failed_original and failed_alternate:
    print("\nBOTH pin sets have issues. Possible causes:")
    print("1. Motor driver is not powered (check 12V supply)")
    print("2. Wiring is incorrect")
    print("3. GPIO chip is not /dev/gpiochip0 (try gpiochip4 for Pi 5)")
else:
    print("\nAll pins work! Check your motor driver wiring:")
    print("1. Make sure ENA and ENB are HIGH (or PWM)")
    print("2. Check that motors are connected to L298N outputs")
    print("3. Verify 12V power supply is connected to motor driver")

# Now test actual motor movement with working pins
print("\n" + "="*60)
print("TESTING MOTOR MOVEMENT")
print("="*60)

# Determine which pin set to use
if failed_original:
    pins_to_use = ALTERNATE
    print("\nUsing ALTERNATE pins for motor test...")
else:
    pins_to_use = ORIGINAL
    print("\nUsing ORIGINAL pins for motor test...")

try:
    chip = gpiod.Chip('/dev/gpiochip0')

    # Request all pins
    lines = {}
    for pin, name in pins_to_use:
        line = chip.get_line(pin)
        line.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
        line.set_value(0)
        lines[name] = line

    print("\nTesting FORWARD (IN1=1, IN2=0, IN3=1, IN4=0)...")
    lines['IN1'].set_value(1)
    time.sleep(0.1)
    lines['IN2'].set_value(0)
    time.sleep(0.1)
    lines['IN3'].set_value(1)
    time.sleep(0.1)
    lines['IN4'].set_value(0)
    time.sleep(0.1)
    lines['ENA'].set_value(1)
    time.sleep(0.1)
    lines['ENB'].set_value(1)

    print("Forward active for 2 seconds...")
    time.sleep(2)

    print("\nStopping...")
    for name, line in lines.items():
        line.set_value(0)
        time.sleep(0.05)

    time.sleep(1)

    print("\nTesting BACKWARD (IN1=0, IN2=1, IN3=0, IN4=1)...")
    lines['IN1'].set_value(0)
    time.sleep(0.1)
    lines['IN2'].set_value(1)
    time.sleep(0.1)
    lines['IN3'].set_value(0)
    time.sleep(0.1)
    lines['IN4'].set_value(1)
    time.sleep(0.1)
    lines['ENA'].set_value(1)
    time.sleep(0.1)
    lines['ENB'].set_value(1)

    print("Backward active for 2 seconds...")
    time.sleep(2)

    print("\nFinal stop...")
    for name, line in lines.items():
        line.set_value(0)
        line.release()

    chip.close()
    print("\n[OK] Motor test complete!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("\nIf motors moved, run:")
print("  sudo python3 /home/sai/Desktop/goku_4/voice_rover_final.py")
print("\nIf motors didn't move, check:")
print("  1. L298N motor driver power (12V supply)")
print("  2. L298N logic power (5V from Pi)")
print("  3. Motor connections to L298N outputs")
print("  4. Try swapping motor wires (polarity)")
