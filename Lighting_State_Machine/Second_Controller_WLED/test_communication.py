#!/usr/bin/env python3
"""
Test script to verify communication between main controller and WLED controller
"""

import requests
import json
import time

# Configuration
WLED_IP = "192.168.1.100"  # Change to your WLED controller's IP
WLED_PORT = 80

def test_wled_connection():
    """Test basic connection to WLED controller"""
    try:
        url = f"http://{WLED_IP}/json/state"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ WLED controller is online and responding")
            return True
        else:
            print(f"❌ WLED controller responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to WLED controller: {e}")
        return False

def test_wled_control():
    """Test sending commands to WLED controller with multi-strip support"""
    if not test_wled_connection():
        return False
    
    # Test different effects
    effects = [
        {"name": "Solid Red", "effect": "solid", "hue": 0, "saturation": 255, "brightness": 255},
        {"name": "Rainbow", "effect": "rainbow", "hue": 0, "saturation": 255, "brightness": 255},
        {"name": "Fire", "effect": "fire", "hue": 0, "saturation": 255, "brightness": 255},
        {"name": "Twinkle", "effect": "twinkle", "hue": 0, "saturation": 255, "brightness": 255},
    ]
    
    for effect in effects:
        print(f"\n🎨 Testing {effect['name']}...")
        
        # Create JSON payload similar to what the main controller sends (multi-strip)
        payload = {
            "on": True,
            "bri": effect["brightness"],
            "seg": [
                {
                    "id": 0,
                    "on": True,
                    "bri": effect["brightness"],
                    "start": 0,
                    "stop": 1000,
                    "fx": get_effect_id(effect["effect"]),
                    "col": [[effect["hue"], effect["saturation"], 255]]
                },
                {
                    "id": 1,
                    "on": True,
                    "bri": effect["brightness"],
                    "start": 1000,
                    "stop": 2000,
                    "fx": get_effect_id(effect["effect"]),
                    "col": [[effect["hue"], effect["saturation"], 255]]
                }
            ]
        }
        
        try:
            url = f"http://{WLED_IP}/json/state"
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ {effect['name']} command sent successfully")
                time.sleep(2)  # Let the effect run for 2 seconds
            else:
                print(f"  ❌ Failed to send {effect['name']} command. Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error sending {effect['name']} command: {e}")
    
    return True

def get_effect_id(effect_name):
    """Map effect names to WLED effect IDs"""
    effect_map = {
        "solid": 0,
        "rainbow": 1,
        "fire": 12,
        "twinkle": 3,
        "wave": 2,
        "chase": 4,
        "breathing": 5
    }
    return effect_map.get(effect_name, 0)

def test_brightness_control():
    """Test brightness control"""
    if not test_wled_connection():
        return False
    
    print("\n💡 Testing brightness control...")
    
    brightness_levels = [50, 100, 150, 200, 255]
    
    for brightness in brightness_levels:
        payload = {
            "on": True,
            "bri": brightness,
            "seg": [{
                "on": True,
                "bri": brightness,
                "start": 0,
                "stop": 1000,
                "fx": 0,  # Solid effect
                "col": [[0, 255, 255]]  # Red
            }]
        }
        
        try:
            url = f"http://{WLED_IP}/json/state"
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ Brightness set to {brightness}")
                time.sleep(1)
            else:
                print(f"  ❌ Failed to set brightness to {brightness}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error setting brightness: {e}")
    
    return True

def main():
    """Main test function"""
    print("🚀 WLED Controller Communication Test")
    print("=" * 40)
    
    print(f"Target WLED IP: {WLED_IP}")
    print(f"Target WLED Port: {WLED_PORT}")
    
    # Test basic connection
    if not test_wled_connection():
        print("\n❌ Basic connection test failed. Please check:")
        print("  1. WLED controller is powered on")
        print("  2. WLED controller is connected to WiFi")
        print("  3. IP address is correct")
        print("  4. Both devices are on the same network")
        return
    
    # Test effect control
    if not test_wled_control():
        print("\n❌ Effect control test failed")
        return
    
    # Test brightness control
    if not test_brightness_control():
        print("\n❌ Brightness control test failed")
        return
    
    print("\n🎉 All tests passed! WLED controller is working correctly.")
    print("\nNext steps:")
    print("1. Update the main controller with the correct WLED IP address")
    print("2. Test the main controller's communication with WLED")
    print("3. Enjoy faster LED animations! 🎨✨")

if __name__ == "__main__":
    main()
