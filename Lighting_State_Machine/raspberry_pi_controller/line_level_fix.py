#!/usr/bin/env python3
"""
Line Level Input Fix
Configure Raspberry Pi audio input for line level instead of mic level
"""

import subprocess
import time
import os

class LineLevelConfigurator:
    """Configure audio input for line level signals"""
    
    def __init__(self):
        self.device_name = None
        self.current_config = {}
        
    def detect_audio_device(self):
        """Detect the audio input device"""
        try:
            # Try to get default device info
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("🔍 Available audio devices:")
                print(result.stdout)
            
            # Try to get PulseAudio sources
            result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("\n🔍 PulseAudio sources:")
                print(result.stdout)
            
            return True
            
        except Exception as e:
            print(f"❌ Error detecting audio devices: {e}")
            return False
    
    def configure_alsa_for_line_level(self):
        """Configure ALSA for line level input"""
        print("🔧 Configuring ALSA for line level input...")
        
        try:
            # Method 1: Set capture source to line-in
            print("📝 Setting capture source to line-in...")
            result = subprocess.run(['amixer', 'set', 'Capture', 'line'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Capture source set to line-in")
            else:
                print(f"⚠️ Could not set capture source: {result.stderr}")
            
            # Method 2: Reduce capture volume (line level is higher than mic level)
            print("📝 Reducing capture volume for line level...")
            result = subprocess.run(['amixer', 'set', 'Capture', '25%'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Capture volume reduced to 25%")
            else:
                print(f"⚠️ Could not set capture volume: {result.stderr}")
            
            # Method 3: Disable capture boost if available
            print("📝 Disabling capture boost...")
            result = subprocess.run(['amixer', 'set', 'Capture', 'nocap'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Capture boost disabled")
            else:
                print("ℹ️ Capture boost control not available")
            
            # Method 4: Set capture switch to off then on (resets some settings)
            print("📝 Resetting capture switch...")
            subprocess.run(['amixer', 'set', 'Capture', 'off'], capture_output=True, timeout=5)
            time.sleep(0.5)
            subprocess.run(['amixer', 'set', 'Capture', 'on'], capture_output=True, timeout=5)
            print("✅ Capture switch reset")
            
            return True
            
        except Exception as e:
            print(f"❌ Error configuring ALSA: {e}")
            return False
    
    def configure_pulseaudio_for_line_level(self):
        """Configure PulseAudio for line level input"""
        print("🔧 Configuring PulseAudio for line level input...")
        
        try:
            # Get default source
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print("⚠️ PulseAudio not available")
                return False
            
            # Set source volume to lower level (line level is higher)
            print("📝 Setting PulseAudio source volume to 30%...")
            result = subprocess.run(['pactl', 'set-source-volume', '@DEFAULT_SOURCE@', '0.3'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ PulseAudio source volume set to 30%")
            else:
                print(f"⚠️ Could not set PulseAudio volume: {result.stderr}")
            
            # Disable automatic gain control if available
            print("📝 Disabling automatic gain control...")
            result = subprocess.run(['pactl', 'set-source-automatic-gain', '@DEFAULT_SOURCE@', '0'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Automatic gain control disabled")
            else:
                print("ℹ️ Automatic gain control not available")
            
            return True
            
        except Exception as e:
            print(f"❌ Error configuring PulseAudio: {e}")
            return False
    
    def create_alsa_config(self):
        """Create ALSA configuration file for line level"""
        print("📝 Creating ALSA configuration for line level...")
        
        config_content = """# ALSA configuration for line level input
# This file should be placed in /etc/asound.conf or ~/.asoundrc

pcm.!default {
    type pulse
}

ctl.!default {
    type pulse
}

# Line level input configuration
pcm.line_input {
    type hw
    card 0
    device 0
    format S16_LE
    rate 44100
    channels 1
}

# Capture configuration for line level
pcm.capture_line {
    type hw
    card 0
    device 0
    format S16_LE
    rate 44100
    channels 1
    capture {
        format S16_LE
        rate 44100
        channels 1
    }
}
"""
        
        try:
            # Write to user's home directory
            home_dir = os.path.expanduser("~")
            config_file = os.path.join(home_dir, ".asoundrc")
            
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            print(f"✅ ALSA config written to {config_file}")
            print("ℹ️ You may need to restart audio services for changes to take effect")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating ALSA config: {e}")
            return False
    
    def test_line_level_configuration(self):
        """Test the line level configuration"""
        print("🧪 Testing line level configuration...")
        
        try:
            # Record a short test
            print("📝 Recording 3-second test...")
            result = subprocess.run([
                'arecord', '-D', 'default', '-f', 'S16_LE', '-r', '44100', '-c', '1', '-d', '3', '/tmp/line_test.wav'
            ], capture_output=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Test recording completed")
                
                # Check file size
                if os.path.exists('/tmp/line_test.wav'):
                    file_size = os.path.getsize('/tmp/line_test.wav')
                    print(f"📊 Test file size: {file_size} bytes")
                    
                    if file_size > 1000:  # Should be several KB for 3 seconds
                        print("✅ Audio data captured successfully")
                        
                        # Play back test
                        print("🔊 Playing back test recording...")
                        subprocess.run(['aplay', '/tmp/line_test.wav'], capture_output=True, timeout=5)
                        
                        # Clean up
                        os.remove('/tmp/line_test.wav')
                        return True
                    else:
                        print("⚠️ Test file too small - may indicate no audio input")
                        return False
                else:
                    print("❌ Test file not created")
                    return False
            else:
                print(f"❌ Test recording failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing configuration: {e}")
            return False
    
    def show_current_settings(self):
        """Show current audio settings"""
        print("📊 Current Audio Settings:")
        print("=" * 40)
        
        # ALSA settings
        try:
            print("ALSA Capture Settings:")
            result = subprocess.run(['amixer', 'get', 'Capture'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(result.stdout)
        except Exception as e:
            print(f"Error getting ALSA settings: {e}")
        
        # PulseAudio settings
        try:
            print("\nPulseAudio Source Settings:")
            result = subprocess.run(['pactl', 'get-source-volume', '@DEFAULT_SOURCE@'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(result.stdout)
        except Exception as e:
            print(f"Error getting PulseAudio settings: {e}")
    
    def apply_line_level_fix(self):
        """Apply complete line level configuration"""
        print("🔧 Applying Line Level Configuration")
        print("=" * 50)
        
        # Detect devices
        if not self.detect_audio_device():
            return False
        
        # Configure ALSA
        if not self.configure_alsa_for_line_level():
            print("⚠️ ALSA configuration had issues")
        
        # Configure PulseAudio
        if not self.configure_pulseaudio_for_line_level():
            print("⚠️ PulseAudio configuration had issues")
        
        # Create config file
        self.create_alsa_config()
        
        # Show current settings
        self.show_current_settings()
        
        # Test configuration
        print("\n🧪 Testing configuration...")
        if self.test_line_level_configuration():
            print("\n✅ Line level configuration applied successfully!")
            print("🎯 Your audio input should now work properly with line level signals")
            return True
        else:
            print("\n⚠️ Configuration applied but test failed")
            print("🔧 You may need to manually adjust settings")
            return False

def main():
    """Main function"""
    print("🎛️ Line Level Input Configuration")
    print("=" * 50)
    print("This will configure your Raspberry Pi audio input")
    print("to work properly with line level signals instead of mic level")
    print()
    
    configurator = LineLevelConfigurator()
    
    while True:
        print("\nOptions:")
        print("1. Detect audio devices")
        print("2. Apply line level configuration")
        print("3. Show current settings")
        print("4. Test configuration")
        print("5. Exit")
        
        try:
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                configurator.detect_audio_device()
            elif choice == '2':
                configurator.apply_line_level_fix()
            elif choice == '3':
                configurator.show_current_settings()
            elif choice == '4':
                configurator.test_line_level_configuration()
            elif choice == '5':
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
