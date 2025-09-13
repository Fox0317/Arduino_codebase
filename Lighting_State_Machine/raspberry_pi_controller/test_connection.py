#!/usr/bin/env python3
"""
Test script to verify connection to ESP32 controllers
"""

import socket
import time
import sys

# ESP32 IPs (update these)
ESP32_IPS = [
    "192.168.68.137",  # ESP32 #1
    "192.168.1.102",  # ESP32 #2  
    "192.168.1.103",  # ESP32 #3
]

UDP_PORT = 8888

def test_esp32_connection(ip, strip_id):
    """Test connection to a specific ESP32"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        
        # Create test packet: [strip_id][brightness][test_data...]
        packet = bytearray()
        packet.append(strip_id)
        packet.append(255)  # Full brightness
        
        # Send test pattern: red, green, blue, white
        test_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 255) # White
        ]
        
        # Send test pattern for first 4 LEDs
        for r, g, b in test_colors:
            packet.extend([r, g, b])
        
        # Fill rest with black
        for _ in range(1000 - 4):
            packet.extend([0, 0, 0])
        
        # Send packet
        sock.sendto(packet, (ip, UDP_PORT))
        print(f"✓ Test packet sent to ESP32 #{strip_id + 1} at {ip}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"✗ Failed to connect to ESP32 #{strip_id + 1} at {ip}: {e}")
        return False

def main():
    """Test all ESP32 connections"""
    print("Testing ESP32 connections...")
    print("=" * 40)
    
    success_count = 0
    
    for i, ip in enumerate(ESP32_IPS):
        print(f"Testing ESP32 #{i + 1} at {ip}...")
        if test_esp32_connection(ip, i):
            success_count += 1
        time.sleep(0.5)
    
    print("=" * 40)
    print(f"Connection test complete: {success_count}/{len(ESP32_IPS)} ESP32s responding")
    
    if success_count == len(ESP32_IPS):
        print("✓ All ESP32s are connected and ready!")
        return 0
    else:
        print("✗ Some ESP32s are not responding. Check:")
        print("  - WiFi connections")
        print("  - IP addresses")
        print("  - ESP32 code uploaded")
        print("  - Network configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
