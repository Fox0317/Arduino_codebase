#!/usr/bin/env python3
"""
ALSA Audio Integration for LED Controller
Drop-in replacement for PyAudio using ALSA/arecord
"""

import subprocess
import threading
import time
import numpy as np
from collections import deque

class ALSAAudioProcessor:
    """ALSA-based audio processing (PyAudio alternative)"""
    
    def __init__(self, device="default"):
        self.device = device
        self.process = None
        self.running = False
        
        # Volume tracking (same as original)
        self.volume_history = deque(maxlen=400)  # 400ms history
        self.short_term_samples = 50   # 50ms
        self.long_term_samples = 400  # 400ms
        
        # Current averages
        self.short_term_avg = 0.0
        self.long_term_avg = 0.0
        self.current_volume = 0.0
        
        # Thread lock
        self.lock = threading.Lock()
        
        print(f"ALSA Audio Processor initialized for device: {device}")
    
    def init_audio(self):
        """Initialize ALSA audio capture"""
        try:
            # Test if device exists
            test_cmd = ['arecord', '-D', self.device, '-f', 'S16_LE', '-r', '44100', '-c', '1', '-d', '1', '/dev/null']
            result = subprocess.run(test_cmd, capture_output=True, timeout=5)
            
            if result.returncode != 0:
                print(f"❌ Device {self.device} not available: {result.stderr.decode()}")
                return False
            
            print(f"✅ ALSA device {self.device} is available")
            return True
            
        except Exception as e:
            print(f"❌ ALSA initialization failed: {e}")
            return False
    
    def start_audio_processing(self):
        """Start audio processing"""
        if not self.init_audio():
            return False
        
        try:
            # Start arecord process
            cmd = [
                'arecord',
                '-D', self.device,
                '-f', 'S16_LE',  # 16-bit signed little-endian
                '-r', '44100',   # Sample rate
                '-c', '1',       # Mono
                '-t', 'raw'      # Raw output
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            self.running = True
            
            # Start processing thread
            self.thread = threading.Thread(target=self._process_audio)
            self.thread.daemon = True
            self.thread.start()
            
            print("🎤 ALSA audio processing started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start ALSA audio processing: {e}")
            return False
    
    def stop_audio_processing(self):
        """Stop audio processing"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("🎤 ALSA audio processing stopped")
    
    def _process_audio(self):
        """Process audio data from arecord"""
        chunk_size = 1024 * 2  # 1024 samples * 2 bytes per sample
        
        while self.running:
            try:
                # Read raw audio data
                data = self.process.stdout.read(chunk_size)
                if len(data) == chunk_size:
                    # Convert to numpy array
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate volume using simple average (absolute values)
                    if len(audio_data) > 0:
                        volume = np.mean(np.abs(audio_data)) / 32768.0
                        
                        # Add to history
                        with self.lock:
                            self.volume_history.append(volume)
                            self.current_volume = volume
                            
                            # Update averages
                            if len(self.volume_history) >= self.short_term_samples:
                                recent = list(self.volume_history)[-self.short_term_samples:]
                                self.short_term_avg = sum(recent) / self.short_term_samples
                            
                            if len(self.volume_history) >= self.long_term_samples:
                                recent = list(self.volume_history)[-self.long_term_samples:]
                                self.long_term_avg = sum(recent) / self.long_term_samples
                
                time.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                print(f"⚠️ Error processing ALSA audio: {e}")
                break
    
    def get_volume_data(self):
        """Get volume data (same interface as original)"""
        with self.lock:
            return {
                'current_volume': self.current_volume,
                'short_term_avg': self.short_term_avg,
                'long_term_avg': self.long_term_avg,
                'sample_count': len(self.volume_history)
            }
    
    def cleanup(self):
        """Cleanup"""
        self.stop_audio_processing()

# Test function
def test_alsa_audio():
    """Test ALSA audio processing"""
    print("🧪 Testing ALSA Audio Processing")
    print("=" * 40)
    
    processor = ALSAAudioProcessor(device="default")
    
    if processor.start_audio_processing():
        print("✅ ALSA audio processing started successfully")
        print("🎧 Make some noise to test volume detection...")
        
        try:
            for i in range(30):  # Run for 30 seconds
                time.sleep(1)
                data = processor.get_volume_data()
                print(f"Volume: {data['current_volume']:.4f}, "
                      f"Short: {data['short_term_avg']:.4f}, "
                      f"Long: {data['long_term_avg']:.4f}")
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted")
        
        processor.cleanup()
        print("✅ Test completed")
    else:
        print("❌ Failed to start ALSA audio processing")

if __name__ == "__main__":
    test_alsa_audio()
