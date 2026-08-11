#!/usr/bin/env python3
"""
Voice-Controlled Rover with Bluetooth Following - Complete Solution
- Voice commands: forward, backward, left, right, stop, follow me, stop follow
- Bluetooth following with RSSI-based distance maintenance
- Realtime operation with proper motor control for Pi 5 (gpiod)
- Fixed PWM for speed control
"""

import time
import logging
import subprocess
import threading
import re
import tempfile
import os
import sys
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VoiceRover')

# ==================== MOTOR CONTROL ====================
try:
    import gpiod
    from gpiod.line import Value
    GPIO_LIB = 'gpiod'
    VAL_ACTIVE = Value.ACTIVE
    VAL_INACTIVE = Value.INACTIVE
    logger.info("Using gpiod for GPIO")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi'
        VAL_ACTIVE = GPIO.HIGH
        VAL_INACTIVE = GPIO.LOW
        logger.info("Using RPi.GPIO")
    except ImportError:
        GPIO_LIB = None
        logger.error("No GPIO library available")

class MotorController:
    def __init__(self):
        self.initialized = False
        self.chip = None
        self.request = None
        self.current_direction = 'stop'
        self.speed = 70
        self.turn_speed = 60
        self._pwm_running = False
        self._pwm_duty_a = 0
        self._pwm_duty_b = 0
        self._pwm_lock = threading.Lock()
        self._pwm_thread_a = None
        self._pwm_thread_b = None

        # Motor pins (BCM numbering)
        self.IN1 = 17
        self.IN2 = 18
        self.IN3 = 22
        self.IN4 = 23
        self.ENA = 27
        self.ENB = 25

    def initialize(self):
        if GPIO_LIB is None:
            logger.error("No GPIO library available")
            return False

        try:
            if GPIO_LIB == 'gpiod':
                self.chip = gpiod.Chip('/dev/gpiochip0')
                pins = [self.IN1, self.IN2, self.IN3, self.IN4, self.ENA, self.ENB]
                config = {
                    pin: gpiod.LineSettings(
                        direction=gpiod.line.Direction.OUTPUT,
                        drive=gpiod.line.Drive.PUSH_PULL
                    ) for pin in pins
                }
                self.request = self.chip.request_lines(
                    config=config,
                    consumer="voice_rover"
                )
                # All pins inactive initially
                self._set_all_inactive()
                # Start software PWM for speed control
                self._start_software_pwm()
                logger.info(f"Motors initialized with gpiod - Pins: IN1={self.IN1}, IN2={self.IN2}, IN3={self.IN3}, IN4={self.IN4}, ENA={self.ENA}, ENB={self.ENB}")
            else:
                GPIO.setmode(GPIO.BCM)
                for pin in [self.IN1, self.IN2, self.IN3, self.IN4]:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
                GPIO.setup(self.ENA, GPIO.OUT)
                GPIO.setup(self.ENB, GPIO.OUT)
                self.pwm_ena = GPIO.PWM(self.ENA, 1000)
                self.pwm_enb = GPIO.PWM(self.ENB, 1000)
                self.pwm_ena.start(self.speed)
                self.pwm_enb.start(self.speed)
                logger.info("Motors initialized with RPi.GPIO")

            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Motor init failed: {e}")
            return False

    def _set_all_inactive(self):
        if self.request:
            values = {
                self.IN1: VAL_INACTIVE,
                self.IN2: VAL_INACTIVE,
                self.IN3: VAL_INACTIVE,
                self.IN4: VAL_INACTIVE,
                self.ENA: VAL_ACTIVE,
                self.ENB: VAL_ACTIVE
            }
            self.request.set_values(values)

    def _start_software_pwm(self):
        self._pwm_running = True
        self._pwm_duty_a = self.speed
        self._pwm_duty_b = self.speed
        self._pwm_thread_a = threading.Thread(target=self._pwm_loop, args=(self.ENA, 'a'), daemon=True)
        self._pwm_thread_b = threading.Thread(target=self._pwm_loop, args=(self.ENB, 'b'), daemon=True)
        self._pwm_thread_a.start()
        self._pwm_thread_b.start()
        logger.info("Software PWM started")

    def _pwm_loop(self, pin, motor_id):
        period = 0.01  # 10ms period = 100Hz
        while self._pwm_running:
            with self._pwm_lock:
                duty = self._pwm_duty_a if motor_id == 'a' else self._pwm_duty_b
            if duty <= 0:
                time.sleep(period)
                continue
            if duty >= 100:
                if self.request:
                    self.request.set_value(pin, VAL_ACTIVE)
                time.sleep(period)
                continue
            on_time = period * duty / 100.0
            off_time = period - on_time
            if self.request:
                self.request.set_value(pin, VAL_ACTIVE)
            time.sleep(on_time)
            if self.request:
                self.request.set_value(pin, VAL_INACTIVE)
            time.sleep(off_time)

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

    def _set_motors(self, in1, in2, in3, in4):
        if not self.request:
            return
        values = {
            self.IN1: in1,
            self.IN2: in2,
            self.IN3: in3,
            self.IN4: in4
        }
        self.request.set_values(values)

    def forward(self, speed=None):
        if not self.initialized:
            logger.warning("Motors not initialized")
            return
        spd = speed or self.speed
        self._set_speed(spd)
        self._set_motors(VAL_ACTIVE, VAL_INACTIVE, VAL_ACTIVE, VAL_INACTIVE)
        self.current_direction = 'forward'
        logger.info(f"Forward at {spd}%")

    def backward(self, speed=None):
        if not self.initialized:
            logger.warning("Motors not initialized")
            return
        spd = speed or self.speed
        self._set_speed(spd)
        self._set_motors(VAL_INACTIVE, VAL_ACTIVE, VAL_INACTIVE, VAL_ACTIVE)
        self.current_direction = 'backward'
        logger.info(f"Backward at {spd}%")

    def left(self, speed=None):
        if not self.initialized:
            logger.warning("Motors not initialized")
            return
        spd = speed or self.turn_speed
        self._set_speed(spd)
        self._set_motors(VAL_INACTIVE, VAL_ACTIVE, VAL_ACTIVE, VAL_INACTIVE)
        self.current_direction = 'left'
        logger.info(f"Left at {spd}%")

    def right(self, speed=None):
        if not self.initialized:
            logger.warning("Motors not initialized")
            return
        spd = speed or self.turn_speed
        self._set_speed(spd)
        self._set_motors(VAL_ACTIVE, VAL_INACTIVE, VAL_INACTIVE, VAL_ACTIVE)
        self.current_direction = 'right'
        logger.info(f"Right at {spd}%")

    def stop(self):
        if not self.initialized:
            return
        self._set_motors(VAL_INACTIVE, VAL_INACTIVE, VAL_INACTIVE, VAL_INACTIVE)
        self.current_direction = 'stop'
        logger.info("Stopped")

    def cleanup(self):
        self._pwm_running = False
        if self._pwm_thread_a:
            self._pwm_thread_a.join(timeout=1)
        if self._pwm_thread_b:
            self._pwm_thread_b.join(timeout=1)
        self.stop()
        if GPIO_LIB == 'gpiod':
            if self.request:
                self.request.release()
                self.request = None
            if self.chip:
                self.chip.close()
                self.chip = None
        elif GPIO_LIB == 'RPi':
            if hasattr(self, 'pwm_ena'):
                self.pwm_ena.stop()
            if hasattr(self, 'pwm_enb'):
                self.pwm_enb.stop()
            GPIO.cleanup()
        logger.info("Motor cleanup done")


# ==================== SPEECH RECOGNITION ====================
class VoiceRecognizer:
    def __init__(self):
        self.device = "plughw:2,0"  # USB mic

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
        except sr.RequestError:
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

        # RSSI thresholds for distance maintenance
        self.RSSI_CLOSE = -55   # Too close, stop
        self.RSSI_OPTIMAL = -70 # Perfect distance
        self.RSSI_FAR = -85     # Too far, move fast

    def set_target(self, mac):
        self.target_mac = mac.upper()
        logger.info(f"Follow target set: {self.target_mac}")

    def _get_rssi(self, mac, timeout=3):
        try:
            proc = subprocess.run(
                ['bluetoothctl', '--timeout', str(timeout), 'info', mac],
                capture_output=True, text=True, timeout=timeout+2
            )
            if proc.returncode == 0:
                m = re.search(r'RSSI:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except:
            pass

        try:
            proc = subprocess.run(
                ['hcitool', 'rssi', mac],
                capture_output=True, text=True, timeout=timeout+2
            )
            if proc.returncode == 0:
                m = re.search(r'RSSI return value:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except:
            pass

        return None

    def _follow_loop(self):
        logger.info("Follow loop started")
        consecutive_lost = 0
        while not self._stop_event.is_set():
            if not self.target_mac:
                break

            rssi = self._get_rssi(self.target_mac)
            if rssi is None:
                consecutive_lost += 1
                logger.warning(f"Lost target signal ({consecutive_lost})")
                if consecutive_lost > 5:
                    self.motor.stop()
                    time.sleep(2)
                time.sleep(1)
                continue

            consecutive_lost = 0
            logger.info(f"RSSI: {rssi}")

            if rssi >= self.RSSI_CLOSE:
                # Too close - stop
                self.motor.stop()
                logger.info("Too close - stopped")
                time.sleep(2)
            elif self.RSSI_CLOSE > rssi >= self.RSSI_OPTIMAL:
                # Optimal distance - stop
                self.motor.stop()
                logger.info("Optimal distance - idle")
                time.sleep(1)
            elif self.RSSI_OPTIMAL > rssi >= self.RSSI_FAR:
                # Follow slowly
                self.motor.forward(speed=50)
                logger.info("Following (slow)")
                time.sleep(1)
            else:
                # Far away - follow fast
                self.motor.forward(speed=80)
                logger.info("Following (fast)")
                time.sleep(1)

        self.motor.stop()
        logger.info("Follow loop ended")

    def start_following(self):
        if not self.target_mac:
            logger.error("No target MAC set")
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
            logger.error("Motor init failed")
            return False
        self.follower = BluetoothFollower(self.motor)
        logger.info("Initialization complete")
        return True

    def process_command(self, command):
        if not command:
            return True

        logger.info(f"Command: {command}")

        # Movement commands
        if any(w in command for w in ['forward', 'go forward', 'move forward']):
            self.motor.forward()
        elif any(w in command for w in ['backward', 'go back', 'reverse', 'move back']):
            self.motor.backward()
        elif any(w in command for w in ['left', 'turn left']):
            self.motor.left()
        elif any(w in command for w in ['right', 'turn right']):
            self.motor.right()
        elif any(w in command for w in ['stop', 'halt', 'freeze']):
            self.motor.stop()
            if self.follower and self.follower.is_following():
                self.follower.stop_following()
                logger.info("Stopped and following disabled")

        # Follow commands
        elif 'follow' in command:
            if 'stop' in command or 'cancel' in command:
                self.follower.stop_following()
                logger.info("Following stopped")
            else:
                # Try to get MAC from command or use saved one
                mac = self._extract_mac(command)
                if mac:
                    self.follower.set_target(mac)
                logger.info("Starting follow mode...")
                self.follower.start_following()

        # Quit
        elif any(w in command for w in ['quit', 'exit', 'shutdown', 'goodbye']):
            logger.info("Shutdown command received")
            return False

        else:
            logger.info(f"Unknown command: {command}")

        return True

    def _extract_mac(self, command):
        m = re.search(r'([0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2})', command, re.I)
        if m:
            return m.group(1).replace('-', ':').upper()
        return None

    def run(self):
        self.running = True
        logger.info("Voice Rover ready. Listening for commands...")
        print("\n" + "="*50)
        print("VOICE ROVER READY")
        print("Commands: 'forward', 'backward', 'left', 'right', 'stop'")
        print("Follow: 'follow me' / 'stop follow'")
        print("Exit: 'quit' or Ctrl+C")
        print("="*50 + "\n")

        try:
            while self.running:
                command = self.voice.listen(timeout=4)
                if command:
                    if not self.process_command(command):
                        break
                else:
                    # No voice detected, continue loop
                    pass
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down...")
        if self.follower:
            self.follower.stop_following()
        self.motor.stop()
        self.motor.cleanup()
        logger.info("Shutdown complete")


# ==================== ENTRY POINT ====================
def main():
    controller = VoiceRoverController()
    if not controller.initialize():
        print("Failed to initialize. Check connections and permissions.")
        return 1

    controller.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
