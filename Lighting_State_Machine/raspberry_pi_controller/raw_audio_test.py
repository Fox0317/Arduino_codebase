#!/usr/bin/env python3
"""
Raw Audio Test Script
Shows raw audio values in real-time for debugging
"""

import pyaudio
import numpy as np
import time
import signal
import sys

# Audio Configuration
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
AUDIO_DEVICE_INDEX = 2  # Device 2 (USB Audio Device)

class RawAudioTester:
    """Raw audio value testing"""
    
    def __init__(self):
        self.audio = None
        self.stream = None
        self.running = False
        self.packet_count = 0
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Stopping raw audio test...")
        self.stop()
        sys.exit(0)
    
    def init_audio(self):
        """Initialize PyAudio"""
        try:
            self.audio = pyaudio.PyAudio()
            
            print("🔍 Available audio devices:")
            input_devices = []
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(i)
                    print(f"   Device {i}: {device_info['name']}")
            
            # Verify device exists
            if AUDIO_DEVICE_INDEX not in input_devices:
                print(f"❌ Device {AUDIO_DEVICE_INDEX} not found!")
                print("Available input devices:", input_devices)
                return False
            
            # Open stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=AUDIO_DEVICE_INDEX,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.audio_callback
            )
            
            print(f"✅ Audio initialized with device {AUDIO_DEVICE_INDEX}")
            return True
            
        except Exception as e:
            print(f"❌ Audio init failed: {e}")
            return False
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback with detailed raw value output"""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        self.packet_count += 1
        
        # Convert to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        if len(audio_data) > 0:
            # Show detailed raw audio information
            print(f"\n📊 Packet #{self.packet_count}")
            print(f"   Data length: {len(in_data)} bytes")
            print(f"   Array length: {len(audio_data)} samples")
            print(f"   Min value: {np.min(audio_data)}")
            print(f"   Max value: {np.max(audio_data)}")
            print(f"   Mean value: {np.mean(audio_data):.2f}")
            print(f"   Std dev: {np.std(audio_data):.2f}")
            
            # Show first 20 values
            print(f"   First 20 values: {audio_data[:20].tolist()}")
            
            # Show last 20 values
            print(f"   Last 20 values: {audio_data[-20:].tolist()}")
            
            # Calculate different volume metrics
            rms_volume = np.sqrt(np.mean(audio_data**2)) / 32768.0
            avg_volume = np.mean(np.abs(audio_data)) / 32768.0
            peak_volume = np.max(np.abs(audio_data)) / 32768.0
            
            print(f"   RMS volume: {rms_volume:.6f}")
            print(f"   Avg volume: {avg_volume:.6f}")
            print(f"   Peak volume: {peak_volume:.6f}")
            
            # Check for unusual values
            if np.all(audio_data == 0):
                print("   ⚠️ All values are zero!")
            elif np.all(audio_data == audio_data[0]):
                print(f"   ⚠️ All values are the same: {audio_data[0]}")
            elif np.any(np.isnan(audio_data)):
                print("   ⚠️ Contains NaN values!")
            elif np.any(np.isinf(audio_data)):
                print("   ⚠️ Contains infinite values!")
            
        else:
            print(f"\n📊 Packet #{self.packet_count} - Empty data!")
        
        return (in_data, pyaudio.paContinue)
    
    def start(self):
        """Start raw audio testing"""
        if not self.init_audio():
            return False
        
        if self.stream:
            self.running = True
            self.stream.start_stream()
            print("\n🎤 Raw audio testing started")
            print("📊 Press Ctrl+C to stop")
            print("🔊 Make some noise to see raw values change")
            return True
        return False
    
    def stop(self):
        """Stop raw audio testing"""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        print("🎤 Raw audio testing stopped")
    
    def run(self, duration=30):
        """Run raw audio test"""
        if not self.start():
            return False
        
        try:
            start_time = time.time()
            while self.running and (time.time() - start_time) < duration:
                time.sleep(0.1)
            
            print(f"\n🏁 Test completed after {duration} seconds")
            print(f"📊 Total packets processed: {self.packet_count}")
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        
        finally:
            self.stop()
        
        return True

def main():
    """Main function"""
    print("🔊 Raw Audio Value Test")
    print("=" * 40)
    print("This will show detailed raw audio values")
    print("Useful for debugging audio capture issues")
    print()
    
    tester = RawAudioTester()
    
    # Run for 30 seconds or until interrupted
    success = tester.run(duration=30)
    
    if success:
        print("\n✅ Raw audio test completed")
    else:
        print("\n❌ Raw audio test failed")

if __name__ == "__main__":
    main()
