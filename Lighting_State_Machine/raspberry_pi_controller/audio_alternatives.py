#!/usr/bin/env python3
"""
Alternative Audio Volume Detection Methods
Various approaches to get audio volume levels without PyAudio
"""

import subprocess
import time
import threading
import os
import numpy as np
from collections import deque

class AudioVolumeDetector:
    """Base class for audio volume detection"""
    
    def __init__(self):
        self.running = False
        self.volume_history = deque(maxlen=400)
        self.current_volume = 0.0
        self.short_term_avg = 0.0
        self.long_term_avg = 0.0
        self.lock = threading.Lock()
    
    def start(self):
        """Start volume detection"""
        pass
    
    def stop(self):
        """Stop volume detection"""
        pass
    
    def get_volume(self):
        """Get current volume level (0.0 to 1.0)"""
        return 0.0

class ALSAVolumeDetector(AudioVolumeDetector):
    """Volume detection using ALSA/arecord"""
    
    def __init__(self, device="default"):
        super().__init__()
        self.device = device
        self.process = None
        self.running = False
    
    def start(self):
        """Start ALSA recording process"""
        try:
            # Start arecord process that outputs raw audio data
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
            
            print(f"✅ ALSA volume detection started on device: {self.device}")
            return True
            
        except Exception as e:
            print(f"❌ ALSA volume detection failed: {e}")
            return False
    
    def stop(self):
        """Stop ALSA recording"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    def _process_audio(self):
        """Process audio data from arecord"""
        chunk_size = 1024 * 2  # 1024 samples * 2 bytes per sample
        
        while self.running:
            try:
                # Read raw audio data
                data = self.process.stdout.read(chunk_size)
                if len(data) == chunk_size:
                    # Convert to numpy array
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate volume using simple average (absolute values)
                    if len(audio_array) > 0:
                        volume = np.mean(np.abs(audio_array)) / 32768.0
                        
                        with self.lock:
                            self.volume_history.append(volume)
                            self.current_volume = volume
                            
                            # Update averages
                            if len(self.volume_history) >= 50:
                                recent = list(self.volume_history)[-50:]
                                self.short_term_avg = sum(recent) / len(recent)
                            
                            if len(self.volume_history) >= 400:
                                recent = list(self.volume_history)[-400:]
                                self.long_term_avg = sum(recent) / len(recent)
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"⚠️ Error processing ALSA audio: {e}")
                break

class PulseAudioVolumeDetector(AudioVolumeDetector):
    """Volume detection using PulseAudio"""
    
    def __init__(self, source="default"):
        super().__init__()
        self.source = source
        self.process = None
        self.running = False
    
    def start(self):
        """Start PulseAudio recording"""
        try:
            # Use parec to record from PulseAudio
            cmd = [
                'parec',
                '--device', self.source,
                '--format', 's16le',
                '--rate', '44100',
                '--channels', '1'
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
            
            print(f"✅ PulseAudio volume detection started on source: {self.source}")
            return True
            
        except Exception as e:
            print(f"❌ PulseAudio volume detection failed: {e}")
            return False
    
    def stop(self):
        """Stop PulseAudio recording"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    def _process_audio(self):
        """Process audio data from parec"""
        chunk_size = 1024 * 2  # 1024 samples * 2 bytes per sample
        
        while self.running:
            try:
                # Read raw audio data
                data = self.process.stdout.read(chunk_size)
                if len(data) == chunk_size:
                    # Convert to numpy array
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate volume using simple average (absolute values)
                    if len(audio_array) > 0:
                        volume = np.mean(np.abs(audio_array)) / 32768.0
                        
                        with self.lock:
                            self.volume_history.append(volume)
                            self.current_volume = volume
                            
                            # Update averages
                            if len(self.volume_history) >= 50:
                                recent = list(self.volume_history)[-50:]
                                self.short_term_avg = sum(recent) / len(recent)
                            
                            if len(self.volume_history) >= 400:
                                recent = list(self.volume_history)[-400:]
                                self.long_term_avg = sum(recent) / len(recent)
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"⚠️ Error processing PulseAudio audio: {e}")
                break

class SystemVolumeDetector(AudioVolumeDetector):
    """Volume detection using system audio monitoring"""
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def start(self):
        """Start system volume monitoring"""
        self.running = True
        
        # Start monitoring thread
        self.thread = threading.Thread(target=self._monitor_volume)
        self.thread.daemon = True
        self.thread.start()
        
        print("✅ System volume monitoring started")
        return True
    
    def stop(self):
        """Stop system volume monitoring"""
        self.running = False
    
    def _monitor_volume(self):
        """Monitor system audio levels"""
        while self.running:
            try:
                # Get system audio level using amixer
                result = subprocess.run(
                    ['amixer', 'get', 'Capture'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # Parse volume level from amixer output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '[' in line and '%' in line:
                            # Extract percentage value
                            try:
                                percent_str = line.split('[')[1].split('%')[0]
                                volume = float(percent_str) / 100.0
                                
                                with self.lock:
                                    self.volume_history.append(volume)
                                    self.current_volume = volume
                                    
                                    # Update averages
                                    if len(self.volume_history) >= 50:
                                        recent = list(self.volume_history)[-50:]
                                        self.short_term_avg = sum(recent) / len(recent)
                                    
                                    if len(self.volume_history) >= 400:
                                        recent = list(self.volume_history)[-400:]
                                        self.long_term_avg = sum(recent) / len(recent)
                                
                                break
                            except (ValueError, IndexError):
                                pass
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                print(f"⚠️ Error monitoring system volume: {e}")
                time.sleep(1)

class FileBasedVolumeDetector(AudioVolumeDetector):
    """Volume detection using temporary audio files"""
    
    def __init__(self, device="default", temp_file="/tmp/audio_test.raw"):
        super().__init__()
        self.device = device
        self.temp_file = temp_file
        self.running = False
    
    def start(self):
        """Start file-based volume detection"""
        self.running = True
        
        # Start monitoring thread
        self.thread = threading.Thread(target=self._monitor_file)
        self.thread.daemon = True
        self.thread.start()
        
        print(f"✅ File-based volume detection started")
        return True
    
    def stop(self):
        """Stop file-based volume detection"""
        self.running = False
        # Clean up temp file
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
    
    def _monitor_file(self):
        """Monitor volume by recording short audio files"""
        while self.running:
            try:
                # Record 0.1 seconds of audio
                cmd = [
                    'arecord',
                    '-D', self.device,
                    '-f', 'S16_LE',
                    '-r', '44100',
                    '-c', '1',
                    '-d', '0.1',  # 0.1 seconds
                    self.temp_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                
                if result.returncode == 0 and os.path.exists(self.temp_file):
                    # Read and process the audio file
                    with open(self.temp_file, 'rb') as f:
                        data = f.read()
                    
                    if len(data) > 0:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        if len(audio_array) > 0:
                            volume = np.sqrt(np.mean(audio_array**2)) / 32768.0
                            
                            with self.lock:
                                self.volume_history.append(volume)
                                self.current_volume = volume
                                
                                # Update averages
                                if len(self.volume_history) >= 50:
                                    recent = list(self.volume_history)[-50:]
                                    self.short_term_avg = sum(recent) / len(recent)
                                
                                if len(self.volume_history) >= 400:
                                    recent = list(self.volume_history)[-400:]
                                    self.long_term_avg = sum(recent) / len(recent)
                    
                    # Clean up temp file
                    os.remove(self.temp_file)
                
                time.sleep(0.05)  # 50ms intervals
                
            except Exception as e:
                print(f"⚠️ Error in file-based monitoring: {e}")
                time.sleep(0.1)

def test_all_methods():
    """Test all available audio detection methods"""
    print("🧪 Testing All Audio Detection Methods")
    print("=" * 50)
    
    methods = [
        ("ALSA (arecord)", ALSAVolumeDetector),
        ("PulseAudio (parec)", PulseAudioVolumeDetector),
        ("System Volume", SystemVolumeDetector),
        ("File-based", FileBasedVolumeDetector)
    ]
    
    results = {}
    
    for name, detector_class in methods:
        print(f"\n🔍 Testing {name}...")
        try:
            detector = detector_class()
            if detector.start():
                # Let it run for 3 seconds
                time.sleep(3)
                volume = detector.get_volume()
                detector.stop()
                
                if volume > 0:
                    print(f"✅ {name}: Working (volume: {volume:.4f})")
                    results[name] = True
                else:
                    print(f"⚠️ {name}: No volume detected")
                    results[name] = False
            else:
                print(f"❌ {name}: Failed to start")
                results[name] = False
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results[name] = False
    
    print(f"\n📊 Results Summary:")
    for name, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"   {name}: {status}")
    
    return results

if __name__ == "__main__":
    # Test all methods
    results = test_all_methods()
    
    # Recommend best method
    working_methods = [name for name, success in results.items() if success]
    
    if working_methods:
        print(f"\n🎯 Recommended method: {working_methods[0]}")
        print("This method can be integrated into your LED controller.")
    else:
        print("\n❌ No working audio detection methods found.")
        print("Check your audio setup and permissions.")
