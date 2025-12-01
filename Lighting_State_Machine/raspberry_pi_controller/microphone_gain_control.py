#!/usr/bin/env python3
"""
Microphone Gain Control
Various methods to adjust microphone gain/sensitivity
"""

import subprocess
import time
import threading
import numpy as np
from collections import deque

class MicrophoneGainController:
    """Controls microphone gain using different methods"""
    
    def __init__(self):
        self.current_gain = 50  # Default gain percentage
        self.gain_method = "amixer"  # Default method
        self.volume_history = deque(maxlen=100)
        self.monitoring = False
        
    def set_gain_amixer(self, gain_percent):
        """Set microphone gain using amixer (ALSA)"""
        try:
            # Set capture volume
            cmd = ['amixer', 'set', 'Capture', f'{gain_percent}%']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.current_gain = gain_percent
                print(f"✅ Microphone gain set to {gain_percent}% using amixer")
                return True
            else:
                print(f"❌ Failed to set gain with amixer: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting gain with amixer: {e}")
            return False
    
    def set_gain_pactl(self, gain_percent):
        """Set microphone gain using pactl (PulseAudio)"""
        try:
            # Get default source
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print("❌ PulseAudio not available")
                return False
            
            # Set source volume (0.0 to 1.0)
            volume = gain_percent / 100.0
            cmd = ['pactl', 'set-source-volume', '@DEFAULT_SOURCE@', f'{volume}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.current_gain = gain_percent
                print(f"✅ Microphone gain set to {gain_percent}% using pactl")
                return True
            else:
                print(f"❌ Failed to set gain with pactl: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting gain with pactl: {e}")
            return False
    
    def set_gain_alsamixer(self, gain_percent):
        """Set microphone gain using alsamixer (interactive)"""
        try:
            print(f"🎛️ Opening alsamixer to set gain to {gain_percent}%")
            print("Use arrow keys to adjust 'Capture' volume")
            print("Press 'Esc' when done")
            
            # This opens interactive alsamixer
            subprocess.run(['alsamixer'], timeout=30)
            return True
            
        except subprocess.TimeoutExpired:
            print("✅ alsamixer closed")
            return True
        except Exception as e:
            print(f"❌ Error opening alsamixer: {e}")
            return False
    
    def get_current_gain(self):
        """Get current microphone gain"""
        try:
            # Try amixer first
            result = subprocess.run(['amixer', 'get', 'Capture'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '[' in line and '%' in line:
                        try:
                            percent_str = line.split('[')[1].split('%')[0]
                            gain = float(percent_str)
                            print(f"📊 Current microphone gain: {gain}%")
                            return gain
                        except (ValueError, IndexError):
                            pass
            
            # Try pactl as fallback
            result = subprocess.run(['pactl', 'get-source-volume', '@DEFAULT_SOURCE@'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse volume from pactl output
                volume_str = result.stdout.split()[1]
                volume = float(volume_str)
                gain = volume * 100
                print(f"📊 Current microphone gain: {gain}%")
                return gain
                
        except Exception as e:
            print(f"❌ Error getting current gain: {e}")
        
        return None
    
    def list_audio_devices(self):
        """List available audio devices and their gain controls"""
        print("🔍 Available Audio Devices:")
        print("=" * 40)
        
        # ALSA devices
        try:
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("ALSA Devices:")
                print(result.stdout)
        except Exception as e:
            print(f"Error listing ALSA devices: {e}")
        
        # PulseAudio sources
        try:
            result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("\nPulseAudio Sources:")
                print(result.stdout)
        except Exception as e:
            print(f"Error listing PulseAudio sources: {e}")
        
        # amixer controls
        try:
            result = subprocess.run(['amixer', 'scontrols'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("\namixer Controls:")
                print(result.stdout)
        except Exception as e:
            print(f"Error listing amixer controls: {e}")
    
    def test_gain_levels(self):
        """Test different gain levels and show volume response"""
        print("🧪 Testing Different Gain Levels")
        print("=" * 40)
        
        test_levels = [25, 50, 75, 100]
        
        for level in test_levels:
            print(f"\n🎛️ Testing gain level: {level}%")
            
            # Set gain
            if self.set_gain_amixer(level):
                time.sleep(1)  # Wait for gain to take effect
                
                # Get current gain to verify
                current = self.get_current_gain()
                if current:
                    print(f"✅ Gain set to {current}%")
                else:
                    print("⚠️ Could not verify gain setting")
            else:
                print(f"❌ Failed to set gain to {level}%")
    
    def auto_adjust_gain(self, target_volume=0.1):
        """Automatically adjust gain to achieve target volume level"""
        print(f"🎯 Auto-adjusting gain to target volume: {target_volume}")
        print("Make some noise while this adjusts...")
        
        # Start volume monitoring
        self.start_volume_monitoring()
        
        # Try different gain levels
        for gain in range(25, 101, 25):  # 25%, 50%, 75%, 100%
            print(f"\n🎛️ Trying gain: {gain}%")
            
            if self.set_gain_amixer(gain):
                time.sleep(2)  # Wait for adjustment
                
                # Check average volume
                if len(self.volume_history) > 10:
                    avg_volume = sum(list(self.volume_history)[-10:]) / 10
                    print(f"📊 Average volume: {avg_volume:.4f}")
                    
                    if avg_volume >= target_volume * 0.8 and avg_volume <= target_volume * 1.2:
                        print(f"✅ Optimal gain found: {gain}%")
                        self.stop_volume_monitoring()
                        return gain
                    elif avg_volume < target_volume * 0.5:
                        print(f"📈 Volume too low, trying higher gain...")
                    elif avg_volume > target_volume * 2.0:
                        print(f"📉 Volume too high, trying lower gain...")
        
        self.stop_volume_monitoring()
        print("⚠️ Could not find optimal gain automatically")
        return None
    
    def start_volume_monitoring(self):
        """Start monitoring volume levels"""
        self.monitoring = True
        self.volume_history.clear()
        
        def monitor():
            while self.monitoring:
                try:
                    # Record short audio sample
                    result = subprocess.run([
                        'arecord', '-D', 'default', '-f', 'S16_LE', '-r', '44100', '-c', '1', '-d', '0.1', '/tmp/gain_test.raw'
                    ], capture_output=True, timeout=2)
                    
                    if result.returncode == 0:
                        # Read and process audio
                        with open('/tmp/gain_test.raw', 'rb') as f:
                            data = f.read()
                        
                        if len(data) > 0:
                            audio_array = np.frombuffer(data, dtype=np.int16)
                            volume = np.mean(np.abs(audio_array)) / 32768.0
                            self.volume_history.append(volume)
                        
                        # Clean up
                        subprocess.run(['rm', '/tmp/gain_test.raw'], capture_output=True)
                    
                except Exception as e:
                    pass  # Ignore errors during monitoring
                
                time.sleep(0.1)
        
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_volume_monitoring(self):
        """Stop monitoring volume levels"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1)

def main():
    """Main function for testing gain control"""
    print("🎛️ Microphone Gain Control")
    print("=" * 40)
    
    controller = MicrophoneGainController()
    
    while True:
        print("\nOptions:")
        print("1. List audio devices")
        print("2. Get current gain")
        print("3. Set gain (amixer)")
        print("4. Set gain (pactl)")
        print("5. Open alsamixer")
        print("6. Test different gain levels")
        print("7. Auto-adjust gain")
        print("8. Exit")
        
        try:
            choice = input("\nEnter choice (1-8): ").strip()
            
            if choice == '1':
                controller.list_audio_devices()
            elif choice == '2':
                controller.get_current_gain()
            elif choice == '3':
                gain = int(input("Enter gain percentage (0-100): "))
                controller.set_gain_amixer(gain)
            elif choice == '4':
                gain = int(input("Enter gain percentage (0-100): "))
                controller.set_gain_pactl(gain)
            elif choice == '5':
                controller.set_gain_alsamixer(50)
            elif choice == '6':
                controller.test_gain_levels()
            elif choice == '7':
                target = float(input("Enter target volume level (0.0-1.0): "))
                controller.auto_adjust_gain(target)
            elif choice == '8':
                break
            else:
                print("Invalid choice")
                
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
