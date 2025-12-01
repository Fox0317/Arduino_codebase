#!/usr/bin/env python3
"""
Audio Debug Script
Quick diagnostic tool to identify audio issues
"""

import pyaudio
import numpy as np
import time

def test_audio_devices():
    """Test all audio input devices"""
    print("🔍 Testing Audio Devices")
    print("=" * 40)
    
    try:
        audio = pyaudio.PyAudio()
        
        print(f"Total devices: {audio.get_device_count()}")
        print("\nInput devices:")
        
        input_devices = []
        for i in range(audio.get_device_count()):
            try:
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(i)
                    print(f"  Device {i}: {device_info['name']}")
                    print(f"    Channels: {device_info['maxInputChannels']}")
                    print(f"    Sample Rate: {device_info['defaultSampleRate']}")
                    print(f"    Host API: {device_info['hostApi']}")
                    print()
            except Exception as e:
                print(f"  Device {i}: Error reading info - {e}")
        
        if not input_devices:
            print("❌ No input devices found!")
            return False
        
        # Test each input device
        print("🧪 Testing each input device...")
        for device_id in input_devices:
            print(f"\nTesting Device {device_id}:")
            test_device(audio, device_id)
        
        audio.terminate()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing audio: {e}")
        return False

def test_device(audio, device_id):
    """Test a specific audio device"""
    try:
        # Get device info
        device_info = audio.get_device_info_by_index(device_id)
        print(f"  Name: {device_info['name']}")
        
        # Try to open stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=1024
        )
        
        print("  ✅ Stream opened successfully")
        
        # Test reading data
        try:
            data = stream.read(1024, exception_on_overflow=False)
            if len(data) > 0:
                audio_array = np.frombuffer(data, dtype=np.int16)
                if len(audio_array) > 0:
                    volume = np.sqrt(np.mean(audio_array**2)) / 32768.0
                    if not np.isnan(volume) and not np.isinf(volume):
                        print(f"  ✅ Data read successfully, volume: {volume:.4f}")
                    else:
                        print(f"  ⚠️ Invalid volume calculated: {volume}")
                else:
                    print("  ⚠️ Empty audio array")
            else:
                print("  ⚠️ No data read")
                
        except Exception as e:
            print(f"  ❌ Error reading data: {e}")
        
        stream.close()
        
    except Exception as e:
        print(f"  ❌ Error testing device: {e}")

def test_system_audio():
    """Test system audio commands"""
    print("\n🔧 Testing System Audio Commands")
    print("=" * 40)
    
    import subprocess
    
    try:
        # Test arecord
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ arecord command works")
            print("Available devices:")
            print(result.stdout)
        else:
            print("❌ arecord command failed")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running arecord: {e}")
    
    try:
        # Test pactl
        result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("\n✅ pactl command works")
            print("PulseAudio sources:")
            print(result.stdout)
        else:
            print("\n❌ pactl command failed")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running pactl: {e}")

def main():
    """Main diagnostic function"""
    print("🚀 Audio Debug Diagnostic Tool")
    print("=" * 50)
    
    # Test PyAudio devices
    if not test_audio_devices():
        print("\n❌ PyAudio device test failed")
        return
    
    # Test system audio
    test_system_audio()
    
    print("\n🎯 Recommendations:")
    print("1. If device 2 shows errors, try a different device")
    print("2. Check microphone permissions and connections")
    print("3. Verify audio levels with: alsamixer")
    print("4. Test with: arecord -f cd -d 5 test.wav")

if __name__ == "__main__":
    main()
