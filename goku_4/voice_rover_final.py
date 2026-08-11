#!/usr/bin/env python3
"""
Voice-Controlled Rover - FINAL FIXED VERSION
Uses ALTERNATE PINS that work reliably on Pi 5:
- IN1 = GPIO 5 (was 17)
- IN2 = GPIO 6 (was 18)  
- IN3 = GPIO 13 (was 22)
- IN4 = GPIO 19 (was 23)
- ENA = GPIO 26 (was 27)
- ENB = GPIO 16 (was 25)
"""
import time
import logging
import subprocess
import threading
import re
import tempfile
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('VoiceRover')

# ==================== MOTOR CONTROL ====================
try:
    import gpiod
    from gpiod.line import Value
    GPIO_LIB = 'gpiod'
    logger.info("Using gpiod")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi'
        logger.info("Using RPi.GPIO")
    except ImportError:
        GPIO_LIB = None
        logger.error("No GPIO library")

class MotorController:
    def __init__(self):
        self.initialized = False
        self.chip = None
        self.lines = {}
        self.current_direction = 'stop'
        self.speed = 70
        self.turn_speed = 60
        self._pwm_running = False
        self._pwm_duty_a = 0
        self._pwm_duty_b = 0
        self._pwm_lock = threading.Lock()
        self._pwm_thread_a = None
        self._pwm_thread_b = None

        # ALTERNATE PINS - More reliable on Pi 5
        self.IN1 = 5    # Motor A + (was 17)
        self.IN2 = 6    # Motor A - (was 18)
        self.IN3 = 13   # Motor B + (was 22)
        self.IN4 = 19   # Motor B - (was 23)
        self.ENA = 26   # Enable A (was 27)
        self.ENB = 16   # Enable B (was 25)

    def initialize(self):
        if GPIO_LIB is None:
            logger.error("No GPIO library")
            return False

        try:
            if GPIO_LIB == 'gpiod':
                self.chip = gpiod.Chip('/dev/gpiochip0')

                # Request each pin individually
                pin_config = {
                    'IN1': self.IN1,
                    'IN2': self.IN2,
                    'IN3': self.IN3,
                    'IN4': self.IN4,
                    'ENA': self.ENA,
                    'ENB': self.ENB
                }

                for name, pin in pin_config.items():
                    line = self.chip.get_line(pin)
                    line.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
                    line.set_value(0)  # Start LOW
                    self.lines[name] = line
                    logger.info(f"  {name} (GPIO {pin}) -> OK")

                logger.info(f"\nMotor pins initialized with gpiod")
                logger.info(f"IN1={self.IN1}, IN2={self.IN2}, IN3={self.IN3}, IN4={self.IN4}")
                logger.info(f"ENA={self.ENA}, ENB={self.ENB}")

                self._start_software_pwm()
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.IN1, GPIO.OUT)
                GPIO.output(self.IN1, GPIO.LOW)
                GPIO.setup(self.IN2, GPIO.OUT)
                GPIO.output(self.IN2, GPIO.LOW)
                GPIO.setup(self.IN3, GPIO.OUT)
                GPIO.output(self.IN3, GPIO.LOW)
                GPIO.setup(self.IN4, GPIO.OUT)
                GPIO.output(self.IN4, GPIO.LOW)
                GPIO.setup(self.ENA, GPIO.OUT)
                GPIO.setup(self.ENB, GPIO.OUT)
                self.pwm_ena = GPIO.PWM(self.ENA, 1000)
                self.pwm_enb = GPIO.PWM(self.ENB, 1000)
                self.pwm_ena.start(self.speed)
                self.pwm_enb.start(self.speed)

            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Motor init failed: {e}")
            return False

    def _start_software_pwm(self):
        self._pwm_running = True
        self._pwm_duty_a = self.speed
        self._pwm_duty_b = self.speed
        self._pwm_thread_a = threading.Thread(target=self._pwm_loop, args=('ENA',), daemon=True)
        self._pwm_thread_b = threading.Thread(target=self._pwm_loop, args=('ENB',), daemon=True)
        self._pwm_thread_a.start()
        self._pwm_thread_b.start()

    def _pwm_loop(self, pin_name):
        period = 0.01
        while self._pwm_running:
            with self._pwm_lock:
                duty = self._pwm_duty_a if pin_name == 'ENA' else self._pwm_duty_b
            if duty <= 0:
                self.lines[pin_name].set_value(0)
                time.sleep(period)
                continue
            if duty >= 100:
                self.lines[pin_name].set_value(1)
                time.sleep(period)
                continue
            on_time = period * duty / 100.0
            off_time = period - on_time
            self.lines[pin_name].set_value(1)
            time.sleep(on_time)
            self.lines[pin_name].set_value(0)
            time.sleep(off_time)

    def _set_pin(self, name, value):
        if GPIO_LIB == 'gpiod' and name in self.lines:
            self.lines[name].set_value(value)
        elif GPIO_LIB == 'RPi':
            GPIO.output(getattr(self, name), value)

    def _set_speed(self, speed):
        if GPIO_LIB == 'RPi':
            if hasattr(self, 'pwm_ena'):
                self.pwm_ena.ChangeDutyCycle(speed)
            if hasattr(self, 'pwm_enb'):
                self.pwm_enb.ChangeDutyCycle(speed)
        elif GPIO_LIB == 'gpiod':
            with self._pwm_lock:
                self._pwm_duty_a = speed
                self._pwm_duty_b = speed

    def forward(self, speed=None):
        if not self.initialized:
            return
        spd = speed or self.speed
        self._set_speed(spd)
        # Motor A forward: IN1=1, IN2=0
        self._set_pin('IN1', 1)
        time.sleep(0.002)
        self._set_pin('IN2', 0)
        time.sleep(0.002)
        # Motor B forward: IN3=1, IN4=0
        self._set_pin('IN3', 1)
        time.sleep(0.002)
        self._set_pin('IN4', 0)
        self.current_direction = 'forward'
        logger.info(f"Forward at {spd}%")

    def backward(self, speed=None):
        if not self.initialized:
            return
        spd = speed or self.speed
        self._set_speed(spd)
        # Motor A backward: IN1=0, IN2=1
        self._set_pin('IN1', 0)
        time.sleep(0.002)
        self._set_pin('IN2', 1)
        time.sleep(0.002)
        # Motor B backward: IN3=0, IN4=1
        self._set_pin('IN3', 0)
        time.sleep(0.002)
        self._set_pin('IN4', 1)
        self.current_direction = 'backward'
        logger.info(f"Backward at {spd}%")

    def left(self, speed=None):
        if not self.initialized:
            return
        spd = speed or self.turn_speed
        self._set_speed(spd)
        # Motor A backward, Motor B forward
        self._set_pin('IN1', 0)
        time.sleep(0.002)
        self._set_pin('IN2', 1)
        time.sleep(0.002)
        self._set_pin('IN3', 1)
        time.sleep(0.002)
        self._set_pin('IN4', 0)
        self.current_direction = 'left'
        logger.info(f"Left at {spd}%")

    def right(self, speed=None):
        if not self.initialized:
            return
        spd = speed or self.turn_speed
        self._set_speed(spd)
        # Motor A forward, Motor B backward
        self._set_pin('IN1', 1)
        time.sleep(0.002)
        self._set_pin('IN2', 0)
        time.sleep(0.002)
        self._set_pin('IN3', 0)
        time.sleep(0.002)
        self._set_pin('IN4', 1)
        self.current_direction = 'right'
        logger.info(f"Right at {spd}%")

    def stop(self):
        if not self.initialized:
            return
        self._set_pin('IN1', 0)
        self._set_pin('IN2', 0)
        self._set_pin('IN3', 0)
        self._set_pin('IN4', 0)
        self.current_direction = 'stop'
        logger.info("Stopped")

    def test_pins(self):
        """Test each pin individually"""
        logger.info("\n" + "="*60)
        logger.info("TESTING EACH PIN INDIVIDUALLY")
        logger.info("="*60)
        for name in ['IN1', 'IN2', 'IN3', 'IN4', 'ENA', 'ENB']:
            logger.info(f"\nTesting {name} (GPIO {getattr(self, name)})...")
            self.lines[name].set_value(1)
            logger.info(f"  {name} = HIGH (CHECK WITH MULTIMETER NOW!)")
            time.sleep(3)
            self.lines[name].set_value(0)
            logger.info(f"  {name} = LOW")
            time.sleep(0.5)
        logger.info("\nTest complete!")

    def cleanup(self):
        self._pwm_running = False
        if hasattr(self, '_pwm_thread_a') and self._pwm_thread_a:
            self._pwm_thread_a.join(timeout=1)
        if hasattr(self, '_pwm_thread_b') and self._pwm_thread_b:
            self._pwm_thread_b.join(timeout=1)
        self.stop()
        if GPIO_LIB == 'gpiod':
            for line in self.lines.values():
                line.release()
            self.lines.clear()
            if self.chip:
                self.chip.close()
        elif GPIO_LIB == 'RPi':
            if hasattr(self, 'pwm_ena'):
                self.pwm_ena.stop()
            if hasattr(self, 'pwm_enb'):
                self.pwm_enb.stop()
            GPIO.cleanup()
        logger.info("Cleanup done")


# ==================== SPEECH RECOGNITION ====================
class VoiceRecognizer:
    def __init__(self):
        self.device = "plughw:2,0"

    def listen(self, timeout=5):
        wav_path = tempfile.mktemp(suffix=".wav")
        try:
            cmd = ["arecord", "-D", self.device, "-f", "S16_LE",
                   "-r", "16000", "-d", str(timeout), "-q", wav_path]
            subprocess.run(cmd, capture_output=True, timeout=timeout+2)
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
                return None
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text.lower().strip()
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return None
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)


# ==================== BLUETOOTH FOLLOWER ====================
class BluetoothFollower:
    def __init__(self, motor_controller):
        self.motor = motor_controller
        self.target_mac = None
        self._following = False
        self._stop_event = threading.Event()
        self._thread = None
        self.RSSI_CLOSE = -55
        self.RSSI_OPTIMAL = -70
        self.RSSI_FAR = -85

    def set_target(self, mac):
        self.target_mac = mac.upper()
        logger.info(f"Follow target: {self.target_mac}")

    def _get_rssi(self, mac, timeout=3):
        try:
            proc = subprocess.run(['bluetoothctl', '--timeout', str(timeout), 'info', mac],
                                  capture_output=True, text=True, timeout=timeout+2)
            if proc.returncode == 0:
                m = re.search(r'RSSI:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except:
            pass
        return None

    def _follow_loop(self):
        logger.info("Follow loop started")
        while not self._stop_event.is_set():
            if not self.target_mac:
                break
            rssi = self._get_rssi(self.target_mac)
            if rssi is None:
                logger.warning("Target lost")
                self.motor.stop()
                time.sleep(1)
                continue
            logger.info(f"RSSI: {rssi}")
            if rssi >= self.RSSI_CLOSE:
                self.motor.stop()
            elif self.RSSI_CLOSE > rssi >= self.RSSI_OPTIMAL:
                self.motor.stop()
            elif self.RSSI_OPTIMAL > rssi >= self.RSSI_FAR:
                self.motor.forward(speed=50)
            else:
                self.motor.forward(speed=80)
            time.sleep(1)
        self.motor.stop()
        logger.info("Follow loop ended")

    def start_following(self):
        if not self.target_mac:
            return False
        if self._following:
            self.stop_following()
            time.sleep(0.5)
        self._stop_event.clear()
        self._following = True
        self._thread = threading.Thread(target=self._follow_loop, daemon=True)
        self._thread.start()
        return True

    def stop_following(self):
        self._following = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.motor.stop()

    def is_following(self):
        return self._following


# ==================== MAIN CONTROLLER ====================
class VoiceRoverController:
    def __init__(self):
        self.motor = MotorController()
        self.voice = VoiceRecognizer()
        self.follower = None
        self.running = False

    def initialize(self):
        logger.info("Initializing Voice Rover...")
        if not self.motor.initialize():
            return False
        self.follower = BluetoothFollower(self.motor)
        return True

    def process_command(self, command):
        if not command:
            return True

        logger.info(f"Command: {command}")

        if any(w in command for w in ['forward', 'go forward']):
            self.motor.forward()
        elif any(w in command for w in ['backward', 'go back', 'reverse']):
            self.motor.backward()
        elif any(w in command for w in ['left', 'turn left']):
            self.motor.left()
        elif any(w in command for w in ['right', 'turn right']):
            self.motor.right()
        elif any(w in command for w in ['stop', 'halt']):
            self.motor.stop()
            if self.follower and self.follower.is_following():
                self.follower.stop_following()
        elif 'follow' in command:
            if 'stop' in command:
                self.follower.stop_following()
            else:
                self.follower.start_following()
        elif any(w in command for w in ['quit', 'exit']):
            return False
        return True

    def run(self):
        self.running = True
        print("\n" + "="*50)
        print("VOICE ROVER READY (FIXED PINS)")
        print("NEW PINS: IN1=5, IN2=6, IN3=13, IN4=19")
        print("         ENA=26, ENB=16")
        print("="*50 + "\n")
        try:
            while self.running:
                command = self.voice.listen(timeout=4)
                if command:
                    if not self.process_command(command):
                        break
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down...")
        if self.follower:
            self.follower.stop_following()
        self.motor.stop()
        self.motor.cleanup()
        logger.info("Done")


def main():
    controller = VoiceRoverController()
    if not controller.initialize():
        print("Init failed")
        return 1
    controller.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
