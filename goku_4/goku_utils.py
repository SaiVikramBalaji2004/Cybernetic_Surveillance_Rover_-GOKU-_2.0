import logging
import time
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GOKU')

def log(message: str, level: str = 'info'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"[{timestamp}] {message}"
    if level == 'error':
        logger.error(msg)
    elif level == 'warning':
        logger.warning(msg)
    elif level == 'debug':
        logger.debug(msg)
    else:
        logger.info(msg)

def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))

def parse_command(text: str) -> dict:
    text = text.lower().strip()
    return {
        'raw': text,
        'action': None,
        'target': None,
        'value': None
    }

def calculate_distance(ir_value: int) -> float:
    if ir_value == 0:
        return 0.0
    return 100.0

class PerformanceTimer:
    def __init__(self, name: str = 'Operation'):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        log(f"{self.name} took {format_duration(elapsed)}")

class CircularBuffer:
    def __init__(self, size: int):
        self.size = size
        self.buffer = []

    def append(self, item):
        self.buffer.append(item)
        if len(self.buffer) > self.size:
            self.buffer.pop(0)

    def get_all(self):
        return self.buffer.copy()

    def get_average(self) -> float:
        if not self.buffer:
            return 0.0
        return sum(self.buffer) / len(self.buffer)

def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    log(f"Attempt {attempt + 1} failed: {e}", 'warning')
                    time.sleep(delay)
        return wrapper
    return decorator
