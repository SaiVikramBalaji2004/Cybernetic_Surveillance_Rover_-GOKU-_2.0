"""
Keypad Controller for GOKU Rover
WASD keys for motor navigation, runs alongside voice control
"""
import sys
import time
import logging
import threading
import termios
import tty
import select

logger = logging.getLogger('GOKU.Keypad')

class KeypadController:
    def __init__(self, motor_controller):
        self.motor = motor_controller
        self.running = False
        self._thread = None
        self._current_key = None
        self._lock = threading.Lock()
        self._active = True

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="keypad")
        self._thread.start()
        logger.info("Keypad controller started")
        return True

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._stop_motor()
        logger.info("Keypad controller stopped")

    def _stop_motor(self):
        try:
            self.motor.stop()
        except Exception:
            pass

    def _handle_key(self, key):
        with self._lock:
            self._current_key = key

        if key == 'w':
            logger.info("Key: W - Forward")
            self.motor.forward()
        elif key == 's':
            logger.info("Key: S - Backward")
            self.motor.backward()
        elif key == 'a':
            logger.info("Key: A - Left")
            self.motor.left()
        elif key == 'd':
            logger.info("Key: D - Right")
            self.motor.right()
        elif key == ' ':
            logger.info("Key: Space - Stop")
            self._stop_motor()
        elif key == 'q':
            logger.info("Key: Q - Quit keypad mode")
            self.running = False

    def _get_key(self, timeout=0.1):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            r, _, _ = select.select([fd], [], [], timeout)
            if r:
                return sys.stdin.read(1)
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _run(self):
        while self.running:
            key = self._get_key(timeout=0.15)
            if key:
                key = key.lower()
                if key in ('w', 'a', 's', 'd', ' ', 'q'):
                    self._handle_key(key)
                elif key == '\x03':
                    raise KeyboardInterrupt
            else:
                if self._current_key in ('w', 'a', 's', 'd'):
                    with self._lock:
                        self._current_key = None
                    self._stop_motor()

keypad_controller = None
