#!/usr/bin/env python3
"""
Motor Fix Tool - Diagnose and fix motor pin issues
Run with: sudo python3 fix_motors.py
"""
import time

print("=" * 60)
print("MOTOR PIN DIAGNOSTIC & FIX TOOL")
print("=" * 60)

# Check gpiod version
try:
    import gpiod
    print(f"\n[gpiod] Library found")
    print(f"  Version info: {gpiod.__version__ if hasattr(gpiod, '__version__') else 'Unknown'}")

    # Test which API works
    print("\n[gpiod] Testing API compatibility...")

    # Try v2.x API first
    try:
        chip = gpiod.Chip('/dev/gpiochip0')
        line = chip.get_line(17)  # Test pin
        config = gpiod.LineConfig()
        config.set_output_values([gpiod.line.Value.INACTIVE])
        line.request(config=config, consumer="test")
        print("  -> Using gpiod v2.x API (set_output_values)")
        API_VERSION = 'v2'
        line.release()
        chip.close()
    except Exception as e1:
        # Try v1.x API
        try:
            chip = gpiod.Chip('/dev/gpiochip0')
            line = chip.get_line(17)
            line.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)
            print("  -> Using gpiod v1.x API (LINE_REQ_DIR_OUT)")
            API_VERSION = 'v1'
            line.release()
            chip.close()
        except Exception as e2:
            print(f"  -> ERROR: Neither API works. {e1}, {e2}")
            API_VERSION = None

except ImportError:
    print("\n[ERROR] gpiod library not found!")
    print("Install with: sudo apt install python3-gpiod")
    exit(1)

if not API_VERSION:
    print("\nCannot proceed without working gpiod API")
    exit(1)

# Pins from config
IN1 = 17
IN2 = 18
IN3 = 22
IN4 = 23
ENA = 27
ENB = 25

print(f"\n[CONFIG] Motor pins: IN1={IN1}, IN2={IN2}, IN3={IN3}, IN4={IN4}, ENA={ENA}, ENB={ENB}")

def test_pin_individual(pin, name):
    """Test a single pin by setting it HIGH and LOW"""
    print(f"\n  Testing {name} (GPIO {pin})...")
    try:
        chip = gpiod.Chip('/dev/gpiochip0')

        if API_VERSION == 'v2':
            line = chip.get_line(pin)
            config = gpiod.LineConfig()
            config.set_output_values([gpiod.line.Value.INACTIVE])
            line.request(config=config, consumer=f"test_{name}")
        else:
            line = chip.get_line(pin)
            line.request(consumer=f"test_{name}", type=gpiod.LINE_REQ_DIR_OUT)

        # Set HIGH
        print(f"    -> Setting HIGH for 2 seconds...")
        line.set_value(1)
        time.sleep(2)

        # Set LOW
        print(f"    -> Setting LOW for 1 second...")
        line.set_value(0)
        time.sleep(1)

        line.release()
        chip.close()
        print(f"    [OK] {name} works!")
        return True
    except Exception as e:
        print(f"    [ERROR] {name} failed: {e}")
        return False

print("\n" + "=" * 60)
print("INDIVIDUAL PIN TEST")
print("=" * 60)
print("Each pin will be set HIGH for 2 seconds.")
print("Use a multimeter/LED to verify voltage changes.\n")

results = {}
for pin, name in [(IN1, 'IN1'), (IN2, 'IN2'), (IN3, 'IN3'), (IN4, 'IN4'), (ENA, 'ENA'), (ENB, 'ENB')]:
    results[name] = test_pin_individual(pin, name)

print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)
for name, result in results.items():
    status = "OK" if result else "FAILED"
    print(f"  {name}: {status}")

# Now test forward pattern
print("\n" + "=" * 60)
print("TESTING FORWARD PATTERN")
print("=" * 60)
print("Setting: IN1=HIGH, IN2=LOW, IN3=HIGH, IN4=LOW")
print("ENA and ENB should also be HIGH\n")

try:
    chip = gpiod.Chip('/dev/gpiochip0')
    lines = {}

    # Request all lines
    for pin, name in [(IN1, 'IN1'), (IN2, 'IN2'), (IN3, 'IN3'), (IN4, 'IN4'), (ENA, 'ENA'), (ENB, 'ENB')]:
        if API_VERSION == 'v2':
            line = chip.get_line(pin)
            config = gpiod.LineConfig()
            config.set_output_values([gpiod.line.Value.INACTIVE])
            line.request(config=config, consumer=f"motor_{name}")
        else:
            line = chip.get_line(pin)
            line.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
        lines[name] = line

    # Forward: IN1=1, IN2=0, IN3=1, IN4=0
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

    print("Forward pattern active for 3 seconds...")
    time.sleep(3)

    # Stop
    print("Stopping - all pins to LOW...")
    for line in lines.values():
        line.set_value(0)

    # Cleanup
    for line in lines.values():
        line.release()
    chip.close()
    print("[OK] Forward pattern test complete!")

except Exception as e:
    print(f"[ERROR] Forward pattern failed: {e}")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)
failed = [name for name, result in results.items() if not result]
if failed:
    print(f"Pins that FAILED: {', '.join(failed)}")
    print("\nPossible causes:")
    print("1. These GPIO pins might be used by something else")
    print("2. Try different pins: 5, 6, 13, 19, 26")
    print("3. Check /dev/gpiochip0 permissions (run with sudo)")
else:
    print("All pins work individually!")
    print("If motors still don't run, check:")
    print("1. Motor driver wiring (L298N vs L293D)")
    print("2. Power supply (12V for motors, 5V for logic)")
    print("3. ENA/ENB might need PWM or just HIGH")
    print("4. Motor polarity - try swapping motor wires")

print("\nTo run the fixed motor control:")
print("  sudo python3 voice_rover.py")
