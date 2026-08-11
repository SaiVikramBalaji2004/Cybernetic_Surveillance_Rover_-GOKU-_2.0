#!/usr/bin/env python3
"""
ESP32 Discovery Script
Scans network to find ESP32 device
"""

import subprocess
import socket
import time

def scan_network():
    """Scan local network for ESP32."""
    print("=" * 60)
    print("ESP32 Network Scanner")
    print("=" * 60)

    print("\n[1] Scanning ARP table for ESP32...")
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")

    print("\n[2] Scanning common ESP32 IP addresses...")
    common_ips = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",
        "192.168.1.103", "192.168.1.104", "192.168.1.105",
        "192.168.1.106", "192.168.1.107", "192.168.1.108",
        "192.168.1.109", "192.168.1.110"
    ]

    found = []
    for ip in common_ips:
        print(f"  Checking {ip}...", end=" ")
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, timeout=2)
            if result.returncode == 0:
                print("FOUND!")
                found.append(ip)
            else:
                print("no response")
        except Exception:
            print("timeout")

    if found:
        print(f"\n[3] Found {len(found)} active IPs: {found}")
    else:
        print("\n[3] No active IPs found in common range")

    print("\n" + "=" * 60)

def get_local_ip():
    """Get Raspberry Pi's IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to determine"

def get_network_prefix():
    """Get network prefix for scanning."""
    local_ip = get_local_ip()
    if local_ip == "Unable to determine":
        return None
    parts = local_ip.split('.')
    return f"{parts[0]}.{parts[1]}.{parts[2]}"

def full_network_scan():
    """Scan entire local network."""
    prefix = get_network_prefix()
    if not prefix:
        return

    print(f"\n[4] Full network scan (192.168.1.1 - 254)...")
    print("    This may take a while...")

    found = []
    for i in range(1, 255):
        ip = f"{prefix}.{i}"
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, timeout=1)
            if result.returncode == 0:
                print(f"  Found: {ip}")
                found.append(ip)
        except Exception:
            pass

    print(f"\n  Total devices found: {len(found)}")
    return found

if __name__ == '__main__':
    scan_network()

    response = input("\nDo you want to do a full network scan? (y/n): ")
    if response.lower() == 'y':
        full_network_scan()

    print("\n" + "=" * 60)
    print("Check your ESP32's Serial Monitor for MAC address")
    print("Example output:")
    print("  MAC: b4:e6:2d:ab:cd:ef")
    print("  IP:  192.168.1.100")
    print("=" * 60)