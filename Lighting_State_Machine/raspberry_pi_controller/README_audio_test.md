# Raspberry Pi Audio Test

This script tests and verifies audio capture functionality for the LED controller system.

## Purpose

- Verify audio input devices are working
- Test audio capture performance
- Validate volume level detection
- Ensure audio system is ready for LED controller

## Installation

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install pyaudio numpy
```

## Usage

```bash
# Run the audio test
python3 audio_test.py
```

## What the Test Does

1. **Device Discovery**: Lists all available audio input devices
2. **Stream Initialization**: Opens audio stream with default device
3. **Volume Monitoring**: Tracks audio levels in real-time
4. **Statistics**: Shows processing performance and audio levels
5. **Analysis**: Determines if audio capture is working properly

## Test Output

The test will show:
- Available audio input devices
- Real-time volume levels
- Processing statistics (packets/sec, averages)
- Final analysis of audio capture quality

## Expected Results

- **✅ Working**: Audio levels detected above 0.01
- **⚠️ Low**: Audio levels between 0.001-0.01
- **❌ No Audio**: Levels below 0.001

## Troubleshooting

### No Audio Input Detected
- Check microphone connection
- Verify audio input is enabled in system settings
- Test with different audio input devices
- Check audio input levels/volume

### PyAudio Installation Issues
```bash
# On Raspberry Pi, you may need:
sudo apt-get install portaudio19-dev python3-pyaudio

# Then install Python packages
pip install pyaudio numpy
```

### Permission Issues
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

## Integration

This test uses the same audio configuration as the main LED controller:
- Sample rate: 44.1 kHz
- Chunk size: 1024 samples
- Short-term average: 50ms
- Long-term average: 400ms

Run this test before starting the LED controller to ensure audio is working properly.
