import subprocess
import time
import threading
import logging
import re
import json
from typing import Optional
from config import BLUETOOTH_FOLLOW

logger = logging.getLogger('GOKU.BTFollower')

class BluetoothFollower:
    def __init__(self, motor_controller):
        self.motor = motor_controller
        self.target_mac = BLUETOOTH_FOLLOW.get('target_mac', '').upper() or None
        self._following = False
        self._stop_event = threading.Event()
        self._thread = None
        self._last_rssi = None
        self._lock = threading.Lock()

        self.RSSI_CLOSE = -55
        self.RSSI_OPTIMAL = -70
        self.RSSI_FAR = -85
        self.SCAN_INTERVAL = 1.0

        if self.target_mac:
            logger.info(f"Loaded saved target MAC: {self.target_mac}")

    def set_target(self, mac_address: str):
        with self._lock:
            self.target_mac = mac_address.upper()
            logger.info(f"Target MAC set: {self.target_mac}")
            self._save_target_mac(self.target_mac)

    def _save_target_mac(self, mac: str):
        try:
            config_path = __import__('config').BASE_DIR / 'config.py'
            with open(config_path, 'r') as f:
                content = f.read()

            old = re.search(r"'target_mac':\s*'[^']*'", content)
            if old:
                new_content = content[:old.start()] + f"'target_mac': '{mac}'" + content[old.end():]
                with open(config_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Saved target MAC to config: {mac}")
        except Exception as e:
            logger.warning(f"Failed to save MAC to config: {e}")

    def get_target(self) -> Optional[str]:
        with self._lock:
            return self.target_mac

    def is_following(self) -> bool:
        return self._following

    def _get_rssi(self, mac: str, timeout: int = 3) -> Optional[int]:
        try:
            proc = subprocess.run(
                ['bluetoothctl', '--timeout', str(timeout), 'info', mac],
                capture_output=True, text=True, timeout=timeout + 2
            )
            if proc.returncode == 0:
                m = re.search(r'RSSI:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.warning(f"RSSI scan error: {e}")

        try:
            proc = subprocess.run(
                ['hcitool', 'rssi', mac],
                capture_output=True, text=True, timeout=timeout + 2
            )
            if proc.returncode == 0:
                m = re.search(r'RSSI return value:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except:
            pass

        try:
            proc = subprocess.run(
                ['bluetoothctl', '--timeout', '5', 'scan', 'on'],
                capture_output=True, text=True, timeout=7
            )
            proc = subprocess.run(
                ['bluetoothctl', 'info', mac],
                capture_output=True, text=True, timeout=3
            )
            if proc.returncode == 0:
                m = re.search(r'RSSI:\s*(-?\d+)', proc.stdout)
                if m:
                    return int(m.group(1))
        except:
            pass

        return None

    def _follow_loop(self, tts_callback=None, display_callback=None):
        logger.info(f"Follow loop started for MAC: {self.target_mac}")
        consecutive_lost = 0
        max_lost = 5

        while not self._stop_event.is_set():
            rssi = self._get_rssi(self.target_mac)

            if rssi is None:
                consecutive_lost += 1
                logger.warning(f"Target lost ({consecutive_lost}/{max_lost})")

                if consecutive_lost >= max_lost:
                    if tts_callback:
                        tts_callback("Lost target. Searching...")
                    self.motor.right()
                    time.sleep(2)
                    self.motor.stop()
                    time.sleep(1)
                    consecutive_lost = 0

                time.sleep(self.SCAN_INTERVAL)
                continue

            consecutive_lost = 0
            self._last_rssi = rssi

            if rssi >= self.RSSI_CLOSE:
                logger.info(f"RSSI: {rssi} - Too close, stopping")
                self.motor.stop()
                if display_callback:
                    display_callback("Follow: Too Close", 'neutral')
                time.sleep(2)

            elif self.RSSI_CLOSE > rssi >= self.RSSI_OPTIMAL:
                logger.info(f"RSSI: {rssi} - Optimal distance")
                self.motor.stop()
                if display_callback:
                    display_callback("Follow: Optimal", 'neutral')

            elif self.RSSI_OPTIMAL > rssi >= self.RSSI_FAR:
                logger.info(f"RSSI: {rssi} - Following")
                self.motor.forward()
                if display_callback:
                    display_callback("Follow: Following", 'neutral')

            elif rssi < self.RSSI_FAR:
                logger.info(f"RSSI: {rssi} - Far, moving fast")
                self.motor.forward(speed=90)
                if display_callback:
                    display_callback("Follow: Far Away", 'neutral')

            time.sleep(self.SCAN_INTERVAL)

        self.motor.stop()
        logger.info("Follow loop ended")

    def start_following(self, tts_callback=None, display_callback=None):
        if not self.target_mac:
            logger.error("No target MAC set")
            return False

        if self._following:
            self.stop_following()
            time.sleep(0.5)

        self._stop_event.clear()
        self._following = True

        self._thread = threading.Thread(
            target=self._follow_loop,
            args=(tts_callback, display_callback),
            daemon=True
        )
        self._thread.start()
        logger.info(f"Following started for MAC: {self.target_mac}")
        return True

    def stop_following(self):
        self._following = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.motor.stop()
        logger.info("Following stopped")

    def get_last_rssi(self) -> Optional[int]:
        return self._last_rssi

    def parse_mac_from_command(self, command: str) -> Optional[str]:
        cl = command.lower().strip()
        m = re.search(r'([0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2}[:\-][0-9a-f]{2})', cl)
        if m:
            return m.group(1).replace('-', ':').upper()

        keywords = ['follow me', 'follow this', 'track device', 'track my']
        for kw in keywords:
            if kw in cl:
                return None

        return None

    def is_save_mac_command(self, command: str) -> bool:
        cl = command.lower().strip()
        save_patterns = [
            'save my device', 'save my mac', 'save my phone',
            'set my device', 'set my mac', 'set target',
            'save this device', 'save this as my',
            'set my phone', 'save phone mac',
        ]
        return any(p in cl for p in save_patterns)

    def get_saved_mac(self) -> Optional[str]:
        return self.target_mac

bluetooth_follower = None

def init_follower(motor_controller):
    global bluetooth_follower
    bluetooth_follower = BluetoothFollower(motor_controller)
    return bluetooth_follower
