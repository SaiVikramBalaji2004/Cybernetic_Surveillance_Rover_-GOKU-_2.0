"""
Home Automation - Direct ESP32 Control via MAC Address
No Arduino Cloud needed - connects directly to ESP32

Requirements:
- ESP32 connected to 5 relays
- ESP32 running web server code (provided below)
- Raspberry Pi 5 on same network
"""

import logging
import time
import requests
import subprocess
import socket
from typing import Optional, Dict

logger = logging.getLogger('GOKU.HomeAutomation')


class ESP32Controller:
    """Direct ESP32 control via MAC address discovery."""

    # ESP32 MAC address - change this to your ESP32's MAC address
    # Found in Arduino Serial Monitor when ESP32 boots up
    ESP32_MAC = "00:70:07:26:0a:38"  # Your ESP32 MAC address

    # Alternative: Known IPs to try if MAC lookup fails
    FALLBACK_IPS = [
        "192.168.1.50", "192.168.1.51", "192.168.1.52",
        "192.168.1.53", "192.168.1.54", "192.168.1.55",
        "192.168.1.56", "192.168.1.57", "192.168.1.58",
        "192.168.1.59", "192.168.1.60", "192.168.1.100",
        "192.168.1.101", "192.168.1.102", "192.168.1.103",
        "192.168.1.104", "192.168.1.105",
    ]

    def __init__(self):
        self.ip = None
        self.port = 80
        self._discovered = False

    def _get_mac_from_arp(self) -> Optional[str]:
        """Get IP address by scanning ARP table."""
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\n'):
                if self.ESP32_MAC.lower() in line.lower():
                    # Format: "192.168.1.100 (b4:e6:2d:ab:cd:ef)"
                    parts = line.split()
                    for part in parts:
                        if part.replace('.', '').isdigit() and part.count('.') == 3:
                            return part
        except Exception as e:
            logger.error(f"ARP scan failed: {e}")
        return None

    def _ping_device(self, ip: str) -> bool:
        """Check if IP is reachable."""
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False

    def _test_esp32(self, ip: str) -> bool:
        """Test if this IP is an ESP32 with relay server."""
        try:
            response = requests.get(f"http://{ip}/", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def discover(self) -> bool:
        """Find ESP32 using MAC address or fallback IPs."""
        logger.info("Discovering ESP32...")

        # Method 1: MAC address lookup
        if self.ESP32_MAC:
            logger.info(f"Looking for MAC: {self.ESP32_MAC}")
            ip = self._get_mac_from_arp()
            if ip:
                logger.info(f"Found via MAC: {ip}")
                if self._test_esp32(ip):
                    self.ip = ip
                    self._discovered = True
                    return True

        # Method 2: Try fallback IPs
        logger.info("Trying fallback IPs...")
        for ip in self.FALLBACK_IPS:
            logger.info(f"Testing {ip}...")
            if self._ping_device(ip) and self._test_esp32(ip):
                logger.info(f"ESP32 found at {ip}")
                self.ip = ip
                self._discovered = True
                return True

        logger.error("ESP32 not found!")
        return False

    def send_command(self, path: str) -> bool:
        """Send HTTP command to ESP32."""
        if not self.ip:
            if not self.discover():
                return False

        try:
            url = f"http://{self.ip}{path}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ESP32 command failed: {e}")
            self._discovered = False
            return False

    def relay_on(self, relay_num: int) -> bool:
        """Turn relay ON."""
        return self.send_command(f"/relay?r={relay_num}&s=1")

    def relay_off(self, relay_num: int) -> bool:
        """Turn relay OFF."""
        return self.send_command(f"/relay?r={relay_num}&s=0")

    def all_off(self) -> bool:
        """Turn all relays OFF."""
        for i in range(1, 6):
            self.send_command(f"/relay?r={i}&s=0")
        return True

    def get_status(self) -> Optional[Dict]:
        """Get relay status from ESP32."""
        if not self.ip:
            return None
        try:
            response = requests.get(f"http://{self.ip}/status", timeout=5)
            return response.json()
        except Exception:
            return None


class HomeAutomation:
    """Home automation controller using ESP32."""

    DEVICES = {
        1: {'name': 'Light 1', 'state': False},
        2: {'name': 'Fan', 'state': False},
        3: {'name': 'Pump Motor', 'state': False},
        4: {'name': 'AC', 'state': False},
        5: {'name': 'Light 2', 'state': False},
    }

    def __init__(self):
        self.esp32 = ESP32Controller()
        self._states = {i: False for i in range(1, 6)}
        self._initialized = False

    def set_esp32_mac(self, mac: str):
        """Set ESP32 MAC address for discovery."""
        self.esp32.ESP32_MAC = mac
        logger.info(f"ESP32 MAC set to: {mac}")

    def set_esp32_ip(self, ip: str):
        """Set ESP32 IP directly (skip discovery)."""
        self.esp32.ip = ip
        self.esp32._discovered = True
        logger.info(f"ESP32 IP set to: {ip}")

    def initialize(self) -> bool:
        """Initialize and discover ESP32."""
        logger.info("Initializing home automation...")

        if self.esp32.ip:
            logger.info(f"Using fixed IP: {self.esp32.ip}")
            self._initialized = True
            return True

        if self.esp32.discover():
            self._initialized = True
            return True

        logger.warning("ESP32 not found, will retry on command")
        self._initialized = True
        return True

    def control_relay(self, relay_num: int, state: bool) -> bool:
        """Control a relay."""
        if relay_num not in self.DEVICES:
            return False

        name = self.DEVICES[relay_num]['name']
        self._states[relay_num] = state

        if state:
            success = self.esp32.relay_on(relay_num)
        else:
            success = self.esp32.relay_off(relay_num)

        status = "ON" if state else "OFF"
        logger.info(f"{name}: {status}")
        return success

    def on(self, relay_num: int) -> bool:
        return self.control_relay(relay_num, True)

    def off(self, relay_num: int) -> bool:
        return self.control_relay(relay_num, False)

    def all_off(self):
        for i in range(1, 6):
            self.control_relay(i, False)

    def process_command(self, command: str) -> Optional[str]:
        """Process voice command."""
        cmd = command.lower().strip()

        light_on = ['light on', 'lights on', 'turn on light', 'light 1 on']
        light_off = ['light off', 'lights off', 'turn off light', 'light 1 off']
        light2_on = ['light 2 on', 'second light on']
        light2_off = ['light 2 off', 'second light off']
        fan_on = ['fan on', 'turn on fan']
        fan_off = ['fan off', 'turn off fan']
        pump_on = ['pump on', 'motor on', 'water pump on']
        pump_off = ['pump off', 'motor off', 'water pump off']
        ac_on = ['ac on', 'air condition on', 'turn on ac']
        ac_off = ['ac off', 'air condition off', 'turn off ac']
        all_off = ['all off', 'everything off', 'shutdown']

        if any(p in cmd for p in all_off):
            self.all_off()
            return "All devices turned off"

        if any(p in cmd for p in light_on):
            self.on(1)
            return "Light 1 turned on"

        if any(p in cmd for p in light_off):
            self.off(1)
            return "Light 1 turned off"

        if any(p in cmd for p in light2_on):
            self.on(5)
            return "Light 2 turned on"

        if any(p in cmd for p in light2_off):
            self.off(5)
            return "Light 2 turned off"

        if any(p in cmd for p in fan_on):
            self.on(2)
            return "Fan turned on"

        if any(p in cmd for p in fan_off):
            self.off(2)
            return "Fan turned off"

        if any(p in cmd for p in pump_on):
            self.on(3)
            return "Pump motor turned on"

        if any(p in cmd for p in pump_off):
            self.off(3)
            return "Pump motor turned off"

        if any(p in cmd for p in ac_on):
            self.on(4)
            return "Air conditioning turned on"

        if any(p in cmd for p in ac_off):
            self.off(4)
            return "Air conditioning turned off"

        return None

    def print_status(self):
        print("\n=== Home Automation Status ===")
        for i in range(1, 6):
            state = "ON" if self._states[i] else "OFF"
            esp_ip = self.esp32.ip or "Not connected"
            print(f"Relay {i}: {self.DEVICES[i]['name']:12} [{state:3}] ESP32: {esp_ip}")


# Global instance
home_automation = HomeAutomation()