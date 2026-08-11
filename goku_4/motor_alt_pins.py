#!/usr/bin/env python3
"""
Motor Control with ALTERNATE PINS for Pi 5
Uses GPIO 5, 6, 13, 19, 26, 16 (more reliable on Pi 5)
"""
import time
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

try:
    import gpiod
    from gpiod.line import Value
    GPIO_LIB = 'gpiod'
    logger.info("[OK] Using gpiod")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi'
        logger.info("[OK] Using RPi.GPIO")
    except ImportError:
        GPIO_LIB = None
        logger.error("[ERROR] No GPIO library")

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
        self.IN1 = 5    # Motor A +
        self.IN2 = 6    # Motor A -
        self.IN3 = 13   # Motor B +
        self.IN4 = 19   # Motor B -
        self.ENA = 26   # Motor A enable (PWM)
        self.ENB = 16   # Motor B enable (PWM)

    def initialize(self):
        if GPIO_LIB is None:
            logger.error("No GPIO library")
            return False

        try:
            if GPIO_LIB == 'gpiod':
                self.chip = gpiod.Chip('/dev/gpiochip0')

                # Request each pin individually
                pins = {
                    'IN1': self.IN1,
                    'IN2': self.IN2,
                    'IN3': self.IN3,
                    'IN4': self.IN4,
                    'ENA': self.ENA,
                    'ENB': self.ENB
                }

                for name, pin in pins.items():
                    line = self.chip.get_line(pin)
                    line.request(consumer=f"motor_{name}", type=gpiod.LINE_REQ_DIR_OUT)
                    line.set_value(0)  # Start LOW
                    self.lines[name] = line
                    logger.info(f"  {name} (GPIO {pin}) -> OK")

                logger.info(f"\nMotor pins initialized successfully")
                logger.info(f"IN1={self.IN1}, IN2={self.IN2}, IN3={self.IN3}, IN4={self.IN4}")
                logger.info(f"ENA={self.ENA}, ENB={self.ENB}")

                self._start_software_pwm()
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.IN1, GPIO.OUT)
                GPIO.setup(self.IN2, GPIO.OUT)
                GPIO.setup(self.IN3, GPIO.OUT)
                GPIO.setup(self.IN4, GPIO.OUT)
                GPIO.setup(self.ENA, GPIO.OUT)
                GPIO.setup(self.ENB, GPIO.OUT)
                GPIO.output(self.IN1, GPIO.LOW)
                GPIO.output(self.IN2, GPIO.LOW)
                GPIO.output(self.IN3, GPIO.LOW)
                GPIO.output(self.IN4, GPIO.LOW)
                self.pwm_ena = GPIO.PWM(self.ENA, 1000)
                self.pwm_enb = GPIO.PWM(self.ENB, 1000)
                self.pwm_ena.start(self.speed)
                self.pwm_enb.start(self.speed)

            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    def _start_software_pwm(self):
        self._pwm_running = True
        self._pwm_duty_a = self.speed
        self._pwm_duty_b = self.speed
        self._pwm_thread_a = threading.Thread(target=self._pwm_loop, args=('ENA',), daemon=True)
        self._pwm_thread_b = threading.Thread(target=self._pwm_loop, args=('ENB',), daemon=True)
        self._pwm_thread_a.start()
        self._pwm_thread_b.start()
        logger.info("Software PWM started")

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

    def test_all_pins(self):
        """Test each pin individually"""
        logger.info("\n" + "="*60)
        logger.info("TESTING EACH PIN INDIVIDUALLY")
        logger.info("="*60)
        for name in ['IN1', 'IN2', 'IN3', 'IN4', 'ENA', 'ENB']:
            logger.info(f"\nTesting {name} (GPIO {getattr(self, name)})...")
            self.lines[name].set_value(1)
            logger.info(f"  {name} = HIGH (check with multimeter NOW)")
            time.sleep(2)
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


if __name__ == '__main__':
    print("="*60)
    print("MOTOR TEST WITH ALTERNATE PINS")
    print("Pins: IN1=5, IN2=6, IN3=13, IN4=19, ENA=26, ENB=16")
    print("="*60)

    motor = MotorController()
    if not motor.initialize():
        print("Failed to initialize!")
        exit(1)

    # Test each pin
    motor.test_all_pins()

    # Test movements
    print("\n" + "="*60)
    print("TESTING MOVEMENTS")
    print("="*60)

    print("\nForward for 2 seconds...")
    motor.forward()
    time.sleep(2)

    print("Stop for 1 second...")
    motor.stop()
    time.sleep(1)

    print("Backward for 2 seconds...")
    motor.backward()
    time.sleep(2)

    print("Stop for 1 second...")
    motor.stop()
    time.sleep(1)

    print("Left for 2 seconds...")
    motor.left()
    time.sleep(2)

    print("Stop for 1 second...")
    motor.stop()
    time.sleep(1)

    print("Right for 2 seconds...")
    motor.right()
    time.sleep(2)

    print("Stop...")
    motor.stop()

    motor.cleanup()
    print("\nTest complete!")
