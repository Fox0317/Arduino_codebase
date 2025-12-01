#!/usr/bin/env python3
"""
Raspberry Pi Audio Capture Test
Tests and verifies audio capture functionality for LED controller
"""

import pyaudio
import numpy as np
import time
import threading
from collections import deque
import signal
import sys

# Audio Configuration (matching LED controller)
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
SHORT_TERM_MS = 50    # Short-term average window (50ms)
LONG_TERM_MS = 400    # Long-term average window (400ms)

class AudioTester:
    """Audio capture testing and verification"""
    
    def __init__(self):
        self.audio = None
        self.stream = None
        self.running = False
        
        # Volume tracking
        self.volume_history = deque(maxlen=400)  # 400ms history
        self.short_term_samples = 50   # 50ms
        self.long_term_samples = 400  # 400ms
        
        # Current averages
        self.short_term_avg = 0.0
        self.long_term_avg = 0.0
        self.current_volume = 0.0
        
        # Statistics
        self.packet_count = 0
        self.start_time = time.time()
        
        # Thread lock
        self.lock = threading.Lock()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down audio test...")
        self.stop()
        sys.exit(0)
    
    def init_audio(self):
        """Initialize PyAudio and show available devices"""
        try:
            self.audio = pyaudio.PyAudio()
            
            print("🔍 Available audio input devices:")
            input_devices = []
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append((i, device_info['name']))
                    print(f"   Device {i}: {device_info['name']}")
            
            if not input_devices:
                print("❌ No audio input devices found!")
                return False
            
            # Try to open stream with default device
            try:
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self.audio_callback
                )
                print("✅ Audio stream opened with default input device")
                return True
                
            except Exception as e:
                print(f"❌ Failed to open audio stream: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Audio initialization failed: {e}")
            return False
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback function"""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        # Debug: Check if we're getting data
        if len(in_data) == 0:
            print("⚠️ Empty audio data received")
            return (in_data, pyaudio.paContinue)
        
        # Convert to numpy array
        try:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Debug: Check audio data
            if len(audio_data) == 0:
                print("⚠️ Empty audio array after conversion")
                return (in_data, pyaudio.paContinue)
            
            # Calculate volume using simple average (absolute values)
            if len(audio_data) > 0 and not np.all(np.isnan(audio_data)):
                # Debug: Print raw audio values
                print(f"🔊 Raw audio sample: min={np.min(audio_data)}, max={np.max(audio_data)}, mean={np.mean(audio_data):.2f}")
                print(f"🔊 First 10 values: {audio_data[:10].tolist()}")
                
                # Use absolute values and simple average
                volume = np.mean(np.abs(audio_data)) / 32768.0
                print(f"🔊 Calculated volume: {volume:.6f}")
                
                # Check for invalid volume values
                if np.isnan(volume) or np.isinf(volume):
                    print(f"⚠️ Invalid volume calculated: {volume}")
                    volume = 0.0
            else:
                print("⚠️ Invalid audio data detected")
                volume = 0.0
                
        except Exception as e:
            print(f"⚠️ Error processing audio data: {e}")
            volume = 0.0
        
        # Add to history and update statistics
        with self.lock:
            self.volume_history.append(volume)
            self.current_volume = volume
            self.packet_count += 1
            
            # Update averages
            if len(self.volume_history) >= self.short_term_samples:
                recent = list(self.volume_history)[-self.short_term_samples:]
                self.short_term_avg = sum(recent) / self.short_term_samples
            
            if len(self.volume_history) >= self.long_term_samples:
                recent = list(self.volume_history)[-self.long_term_samples:]
                self.long_term_avg = sum(recent) / self.long_term_samples
        
        return (in_data, pyaudio.paContinue)
    
    def start(self):
        """Start audio processing"""
        if not self.init_audio():
            return False
        
        if self.stream and not self.running:
            self.running = True
            self.stream.start_stream()
            print("🎤 Audio processing started")
            return True
        else:
            print("⚠️ Cannot start audio processing")
            return False
    
    def stop(self):
        """Stop audio processing"""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        print("🎤 Audio processing stopped")
    
    def get_volume_data(self):
        """Get current volume data"""
        with self.lock:
            return {
                'current_volume': self.current_volume,
                'short_term_avg': self.short_term_avg,
                'long_term_avg': self.long_term_avg,
                'packet_count': self.packet_count,
                'sample_count': len(self.volume_history)
            }
    
    def print_statistics(self):
        """Print audio statistics"""
        data = self.get_volume_data()
        elapsed = time.time() - self.start_time
        
        # Handle NaN values in display
        def safe_format(value, decimals=4):
            if np.isnan(value) or np.isinf(value):
                return "N/A"
            return f"{value:.{decimals}f}"
        
        print(f"\n📊 Audio Statistics:")
        print(f"   Runtime: {elapsed:.1f}s")
        print(f"   Packets processed: {data['packet_count']}")
        print(f"   Packets/sec: {data['packet_count']/elapsed:.1f}")
        print(f"   Current volume: {safe_format(data['current_volume'])}")
        print(f"   Short-term avg: {safe_format(data['short_term_avg'])}")
        print(f"   Long-term avg: {safe_format(data['long_term_avg'])}")
        print(f"   Samples in buffer: {data['sample_count']}")
        
        # Additional debug info
        if data['sample_count'] > 0:
            recent_samples = list(self.volume_history)[-10:]  # Last 10 samples
            valid_samples = [s for s in recent_samples if not np.isnan(s) and not np.isinf(s)]
            print(f"   Recent valid samples: {len(valid_samples)}/10")
            if valid_samples:
                print(f"   Recent volume range: {min(valid_samples):.4f} - {max(valid_samples):.4f}")
    
    def run_test(self, duration=30):
        """Run audio test for specified duration"""
        print("🎵 Raspberry Pi Audio Capture Test")
        print("=" * 50)
        
        if not self.start():
            print("❌ Failed to start audio processing")
            return False
        
        print(f"\n🎧 Listening for audio input for {duration} seconds...")
        print("💡 Make some noise to test audio capture!")
        print("📊 Statistics will be printed every 5 seconds")
        print("⏹️ Press Ctrl+C to stop early\n")
        
        try:
            start_time = time.time()
            last_stats_time = start_time
            
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Print statistics every 5 seconds
                if current_time - last_stats_time >= 5.0:
                    self.print_statistics()
                    last_stats_time = current_time
                
                time.sleep(0.1)
            
            # Final statistics
            print("\n" + "=" * 50)
            print("🏁 Test completed!")
            self.print_statistics()
            
            # Volume level analysis
            data = self.get_volume_data()
            if data['long_term_avg'] > 0.01:
                print("✅ Audio capture is working - detected audio input")
            elif data['long_term_avg'] > 0.001:
                print("⚠️ Audio capture working but very low levels detected")
            else:
                print("❌ No significant audio input detected")
                print("   Check microphone connection and audio levels")
            
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
            return True
        finally:
            self.stop()

def main():
    """Main function"""
    print("🚀 Starting Raspberry Pi Audio Test...")
    
    # Check if required libraries are available
    try:
        import pyaudio
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing required library: {e}")
        print("Install with: pip install pyaudio numpy")
        return
    
    # Create and run audio tester
    tester = AudioTester()
    
    # Run test for 30 seconds
    success = tester.run_test(duration=30)
    
    if success:
        print("\n✅ Audio test completed successfully!")
        print("🎯 Your audio system is ready for the LED controller")
    else:
        print("\n❌ Audio test failed!")
        print("🔧 Please check your audio configuration")

if __name__ == "__main__":
    main()
