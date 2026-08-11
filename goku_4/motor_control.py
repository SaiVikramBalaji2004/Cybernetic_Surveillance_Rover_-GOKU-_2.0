"""
GOKU Motor Controller - Fixed and Rewritten
Keeps same pins from config.py: IN1=5, IN2=6, IN3=13, IN4=19, ENA=26, ENB=16

Fixes:
- PWM must start BEFORE setting direction
- Both motors need ENA/ENB to be active
- Proper timing for pin changes
"""

import time
import logging
import subprocess
import threading
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict

GPIO_AVAILABLE = False
GPIO_LIB = None

try:
    import gpiod
    from gpiod import LineSettings
    from gpiod.line import Value
    GpioDirection = gpiod.line.Direction
    GpioDrive = gpiod.line.Drive
    GPIO_AVAILABLE = True
    GPIO_LIB = 'gpiod'
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        GPIO_LIB = 'RPi'
    except ImportError:
        pass

logger = logging.getLogger('GOKU.Motor')


class MotorDir(Enum):
    STOP = auto()
    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    SCAN_LEFT = auto()
    SCAN_RIGHT = auto()


@dataclass
class MotorState:
    direction: MotorDir = MotorDir.STOP
    speed: int = 0


class PWMController:
    def __init__(self, pin_offset: int, request, frequency: int = 1000):
        self.pin_offset = pin_offset
        self.request = request
        self.frequency = frequency
        self.duty_cycle = 0
        self._running = False
        self._started = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"PWM-{self.pin_offset}")
        self._thread.start()
        self._started = True
        logger.debug(f"PWM started on GPIO {self.pin_offset}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._started = False

    def set_duty(self, duty: int):
        with self._lock:
            self.duty_cycle = max(0, min(100, duty))

    def is_running(self) -> bool:
        return self._started and self._running

    def _run(self):
        period = 1.0 / self.frequency
        while self._running:
            with self._lock:
                duty = self.duty_cycle

            if duty <= 0:
                self.request.set_value(self.pin_offset, Value.INACTIVE)
                time.sleep(period)
                continue

            if duty >= 100:
                self.request.set_value(self.pin_offset, Value.ACTIVE)
                time.sleep(period)
                continue

            on_time = period * (duty / 100.0)
            off_time = period - on_time

            self.request.set_value(self.pin_offset, Value.ACTIVE)
            time.sleep(on_time)
            self.request.set_value(self.pin_offset, Value.INACTIVE)
            time.sleep(off_time)


class MotorController:
    DIR_MAP = {
        MotorDir.FORWARD: (1, 0, 1, 0),   # IN1, IN2, IN3, IN4
        MotorDir.BACKWARD: (0, 1, 0, 1),
        MotorDir.LEFT: (0, 1, 1, 0),      # Motor A back, Motor B forward
        MotorDir.RIGHT: (1, 0, 0, 1),      # Motor A forward, Motor B back
        MotorDir.STOP: (0, 0, 0, 0),
        MotorDir.SCAN_LEFT: (0, 0, 1, 0),
        MotorDir.SCAN_RIGHT: (1, 0, 0, 0),
    }

    def __init__(self):
        self._initialized = False
        self._chip = None
        self._request = None
        self._pwm_a: Optional[PWMController] = None
        self._pwm_b: Optional[PWMController] = None
        self._state = MotorState()
        self._state_lock = threading.RLock()
        self._pins: Dict[str, int] = {}
        self._speed = 70
        self._turn_speed = 60

    def initialize(self, pins: Optional[Dict[str, int]] = None) -> bool:
        """Initialize motor controller with given pins."""
        if not GPIO_AVAILABLE:
            logger.error("No GPIO library available")
            return False

        if self._initialized:
            logger.warning("Already initialized")
            return True

        from config import MOTOR_PINS, MOTOR_SPEED, TURN_SPEED
        self._pins = pins or MOTOR_PINS
        self._speed = MOTOR_SPEED
        self._turn_speed = TURN_SPEED

        try:
            self._cleanup()
            self._init_gpio()
            self._init_pwm()

            # Set all direction pins to 0 initially
            self._request.set_value(self._pins['IN1'], Value.INACTIVE)
            self._request.set_value(self._pins['IN2'], Value.INACTIVE)
            self._request.set_value(self._pins['IN3'], Value.INACTIVE)
            self._request.set_value(self._pins['IN4'], Value.INACTIVE)

            # Start PWM for both motors (full speed initially)
            self._pwm_a.set_duty(self._speed)
            self._pwm_b.set_duty(self._speed)

            self._initialized = True
            logger.info(f"Motor controller initialized:")
            logger.info(f"  IN1={self._pins['IN1']}, IN2={self._pins['IN2']}")
            logger.info(f"  IN3={self._pins['IN3']}, IN4={self._pins['IN4']}")
            logger.info(f"  ENA={self._pins['ENA']}, ENB={self._pins['ENB']}")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self._cleanup()
            return False

    def _init_gpio(self):
        if GPIO_LIB == 'gpiod':
            self._chip = gpiod.Chip('/dev/gpiochip0')

            # Request all pins
            line_config = {
                (pin,): LineSettings(direction=GpioDirection.OUTPUT, drive=GpioDrive.PUSH_PULL)
                for pin in [self._pins['IN1'], self._pins['IN2'],
                            self._pins['IN3'], self._pins['IN4'],
                            self._pins['ENA'], self._pins['ENB']]
            }

            self._request = self._chip.request_lines(line_config, consumer="goku_motor")
            logger.info("GPIO initialized with gpiod v2.x")

        elif GPIO_LIB == 'RPi':
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            for pin in [self._pins['IN1'], self._pins['IN2'],
                        self._pins['IN3'], self._pins['IN4'],
                        self._pins['ENA'], self._pins['ENB']]:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            self._pwm_ena = GPIO.PWM(self._pins['ENA'], 1000)
            self._pwm_enb = GPIO.PWM(self._pins['ENB'], 1000)
            self._pwm_ena.start(0)
            self._pwm_enb.start(0)
            logger.info("GPIO initialized with RPi.GPIO")

    def _init_pwm(self):
        if GPIO_LIB == 'gpiod':
            self._pwm_a = PWMController(self._pins['ENA'], self._request)
            self._pwm_b = PWMController(self._pins['ENB'], self._request)
            self._pwm_a.start()
            self._pwm_b.start()
            logger.info("Software PWM started")

    def _set_pin(self, pin_offset: int, value: int):
        """Set a pin value. Accepts 0/1 or converts Value enum."""
        if GPIO_LIB == 'gpiod' and self._request:
            if isinstance(value, int):
                value = Value.ACTIVE if value else Value.INACTIVE
            self._request.set_value(pin_offset, value)
        elif GPIO_LIB == 'RPi':
            import RPi.GPIO as GPIO
            GPIO.output(pin_offset, value)

    def _set_speed(self, speed: int):
        """Set motor speed via PWM."""
        if GPIO_LIB == 'gpiod':
            if self._pwm_a and self._pwm_b:
                self._pwm_a.set_duty(speed)
                self._pwm_b.set_duty(speed)
        elif GPIO_LIB == 'RPi':
            if hasattr(self, '_pwm_ena'):
                self._pwm_ena.ChangeDutyCycle(speed)
            if hasattr(self, '_pwm_enb'):
                self._pwm_enb.ChangeDutyCycle(speed)

    def _update_direction(self, direction: MotorDir, speed: int):
        """Update motor pins based on direction."""
        if direction not in self.DIR_MAP:
            return

        in1, in2, in3, in4 = self.DIR_MAP[direction]

        self._set_pin(self._pins['IN1'], Value.ACTIVE if in1 else Value.INACTIVE)
        time.sleep(0.002)
        self._set_pin(self._pins['IN2'], Value.ACTIVE if in2 else Value.INACTIVE)
        time.sleep(0.002)
        self._set_pin(self._pins['IN3'], Value.ACTIVE if in3 else Value.INACTIVE)
        time.sleep(0.002)
        self._set_pin(self._pins['IN4'], Value.ACTIVE if in4 else Value.INACTIVE)

        self._set_speed(speed)

        with self._state_lock:
            self._state.direction = direction
            self._state.speed = speed

    @property
    def state(self) -> MotorState:
        with self._state_lock:
            return MotorState(
                direction=self._state.direction,
                speed=self._state.speed
            )

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def move(self, direction: MotorDir, speed: int = None):
        """Generic move method."""
        if not self._initialized:
            logger.warning("Motors not initialized")
            return

        if speed is None:
            if direction in (MotorDir.LEFT, MotorDir.RIGHT):
                speed = self._turn_speed
            elif direction in (MotorDir.SCAN_LEFT, MotorDir.SCAN_RIGHT):
                speed = 40
            else:
                speed = self._speed

        self._update_direction(direction, speed)
        logger.info(f"{direction.name} at {speed}%")

    def forward(self, speed: int = None):
        self.move(MotorDir.FORWARD, speed)

    def backward(self, speed: int = None):
        self.move(MotorDir.BACKWARD, speed)

    def left(self, speed: int = None):
        self.move(MotorDir.LEFT, speed)

    def right(self, speed: int = None):
        self.move(MotorDir.RIGHT, speed)

    def stop(self):
        self.move(MotorDir.STOP, 0)
        if GPIO_LIB == 'gpiod':
            if self._pwm_a:
                self._pwm_a.set_duty(0)
            if self._pwm_b:
                self._pwm_b.set_duty(0)

    def scan_left(self):
        self.move(MotorDir.SCAN_LEFT)

    def scan_right(self):
        self.move(MotorDir.SCAN_RIGHT)

    def set_speed(self, speed: int):
        """Update speed for current direction."""
        with self._state_lock:
            if self._state.direction != MotorDir.STOP:
                self._update_direction(self._state.direction, speed)

    def test_motor_a(self, duration: float = 2.0):
        """Test Motor A (IN1, IN2, ENA)"""
        if not self._initialized:
            logger.error("Not initialized")
            return
        logger.info("Testing Motor A (IN1, IN2, ENA)...")
        self._pwm_a.set_duty(70)
        self._set_pin(self._pins['IN1'], 1)
        self._set_pin(self._pins['IN2'], 0)
        time.sleep(duration)
        self._set_pin(self._pins['IN1'], 0)
        self._set_pin(self._pins['IN2'], 0)
        self._pwm_a.set_duty(0)

    def test_motor_b(self, duration: float = 2.0):
        """Test Motor B (IN3, IN4, ENB)"""
        if not self._initialized:
            logger.error("Not initialized")
            return
        logger.info("Testing Motor B (IN3, IN4, ENB)...")
        self._pwm_b.set_duty(70)
        self._set_pin(self._pins['IN3'], 1)
        self._set_pin(self._pins['IN4'], 0)
        time.sleep(duration)
        self._set_pin(self._pins['IN3'], 0)
        self._set_pin(self._pins['IN4'], 0)
        self._pwm_b.set_duty(0)

    def _cleanup(self):
        try:
            subprocess.run(['sudo', 'killall', 'pigpiod'], capture_output=True, timeout=3)
        except Exception:
            pass

        if self._pwm_a:
            self._pwm_a.stop()
            self._pwm_a = None
        if self._pwm_b:
            self._pwm_b.stop()
            self._pwm_b = None

        if self._request:
            try:
                self._request.release()
            except Exception:
                pass
            self._request = None

        if self._chip:
            try:
                self._chip.close()
            except Exception:
                pass
            self._chip = None

        if GPIO_LIB == 'RPi':
            try:
                import RPi.GPIO as GPIO
                if hasattr(self, '_pwm_ena'):
                    self._pwm_ena.stop()
                if hasattr(self, '_pwm_enb'):
                    self._pwm_enb.stop()
                GPIO.cleanup()
            except Exception:
                pass

    def cleanup(self):
        """Public cleanup method."""
        self._cleanup()
        self._initialized = False
        logger.info("Motor controller cleaned up")

    def test_all_pins(self, duration: float = 1.0):
        """Test each pin individually."""
        if not self._initialized:
            logger.error("Not initialized")
            return

        logger.info("Testing all pins...")
        pin_names = ['IN1', 'IN2', 'IN3', 'IN4', 'ENA', 'ENB']

        for name in pin_names:
            pin = self._pins[name]
            logger.info(f"Testing {name} (GPIO {pin})...")
            self._set_pin(pin, Value.ACTIVE)
            time.sleep(duration)
            self._set_pin(pin, Value.INACTIVE)
            time.sleep(0.2)

        self.stop()
        logger.info("Pin test complete")


motor_controller = MotorController()