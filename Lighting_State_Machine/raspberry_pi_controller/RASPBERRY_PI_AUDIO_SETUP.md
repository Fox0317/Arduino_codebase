# Raspberry Pi Audio Setup Guide

This guide covers setting up microphone input on Raspberry Pi for the LED controller audio capture system.

## Hardware Setup

### USB Microphone (Recommended)
- Connect USB microphone to Raspberry Pi USB port
- Most USB microphones are plug-and-play
- No additional hardware configuration needed

### Built-in Audio (3.5mm Jack)
- Connect microphone to 3.5mm audio input jack
- May require additional configuration
- Quality varies by Pi model

### I2S Microphone Modules
- Connect I2S microphone breakout boards
- Requires enabling I2S interface
- Higher quality audio capture

## Software Setup

### 1. Update System Packages
```bash
sudo apt update
sudo apt upgrade
```

### 2. Install Audio Dependencies
```bash
# Install ALSA utilities and development libraries
sudo apt install alsa-utils alsa-tools alsa-tools-gui

# Install PulseAudio (if not already installed)
sudo apt install pulseaudio pulseaudio-utils

# Install Python audio libraries dependencies
sudo apt install portaudio19-dev python3-pyaudio
```

### 3. Install Python Packages
```bash
# Install required Python packages
pip3 install pyaudio numpy

# Or use the requirements file
pip3 install -r requirements.txt
```

## Audio Configuration

### 1. Check Audio Devices
```bash
# List all audio devices
arecord -l

# List PulseAudio devices
pactl list sources short

# Test microphone recording
arecord -f cd -d 5 test.wav
aplay test.wav
```

### 2. Configure ALSA (if needed)
```bash
# Edit ALSA configuration
sudo nano /etc/asound.conf

# Add configuration for default input device
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
```

### 3. Set Default Audio Input Device
```bash
# Set default input device (replace with your device)
pactl set-default-source alsa_input.usb-USB_PnP_Sound_Device_Audio-00.mono-fallback

# Or set via ALSA
sudo nano /etc/asound.conf
```

## User Permissions

### 1. Add User to Audio Group
```bash
# Add current user to audio group
sudo usermod -a -G audio $USER

# Add user to pulse-access group
sudo usermod -a -G pulse-access $USER

# Log out and back in for changes to take effect
```

### 2. Check Permissions
```bash
# Check if user is in audio group
groups $USER

# Should show 'audio' and 'pulse-access' in the list
```

## Testing Audio Setup

### 1. Run Audio Test Script
```bash
# Run the audio test
python3 audio_test.py
```

### 2. Manual Audio Testing
```bash
# Test recording
arecord -f cd -d 10 test_recording.wav

# Play back recording
aplay test_recording.wav

# Monitor audio levels in real-time
arecord -f cd -t wav - | aplay -
```

### 3. Check Audio Levels
```bash
# Monitor audio input levels
alsamixer

# Or use PulseAudio volume control
pavucontrol
```

## Troubleshooting

### Common Issues

#### 1. "No audio input devices found"
```bash
# Check if audio devices are detected
lsusb | grep -i audio
arecord -l

# Restart audio services
sudo systemctl restart pulseaudio
```

#### 2. "Permission denied" errors
```bash
# Ensure user is in audio group
sudo usermod -a -G audio $USER
sudo usermod -a -G pulse-access $USER

# Log out and back in
```

#### 3. "Device busy" errors
```bash
# Kill any processes using audio
sudo pkill -f pulseaudio
sudo pkill -f alsa

# Restart audio services
sudo systemctl restart pulseaudio
```

#### 4. Low audio levels
```bash
# Increase microphone gain
alsamixer

# Or use PulseAudio
pavucontrol
# Go to Input Devices tab and increase volume
```

#### 5. PyAudio installation fails
```bash
# Install system dependencies first
sudo apt install portaudio19-dev python3-pyaudio

# Then install Python package
pip3 install pyaudio
```

### Advanced Configuration

#### 1. Enable I2S Audio (for I2S microphones)
```bash
# Edit boot configuration
sudo nano /boot/config.txt

# Add these lines:
dtparam=i2s=on
dtoverlay=i2s-mmap

# Reboot
sudo reboot
```

#### 2. Configure USB Audio Device
```bash
# Create udev rule for specific USB device
sudo nano /etc/udev/rules.d/99-usb-audio.rules

# Add rule (replace with your device info):
SUBSYSTEM=="sound", ATTRS{idVendor}=="0d8c", ATTRS{idProduct}=="013c", MODE="0666"
```

#### 3. Set Audio Priority
```bash
# Edit PulseAudio configuration
sudo nano /etc/pulse/daemon.conf

# Uncomment and modify:
default-sample-rate = 44100
default-sample-format = s16le
```

## Verification Steps

### 1. Run Audio Test
```bash
python3 audio_test.py
```

### 2. Check Expected Output
- Should show available audio input devices
- Should detect audio input when you make noise
- Should show processing statistics
- Should complete without errors

### 3. Test with LED Controller
```bash
# Once audio test passes, run LED controller
python3 led_controller.py
```

## Performance Optimization

### 1. Reduce Audio Latency
```bash
# Edit PulseAudio configuration
sudo nano /etc/pulse/daemon.conf

# Add/modify these settings:
default-fragments = 2
default-fragment-size-msec = 25
```

### 2. Set Audio Priority
```bash
# Run with higher priority
sudo nice -n -10 python3 led_controller.py
```

### 3. Disable Unnecessary Services
```bash
# Disable Bluetooth audio if not needed
sudo systemctl disable bluetooth
```

## Model-Specific Notes

### Raspberry Pi 4
- USB 3.0 ports provide better audio performance
- Built-in audio jack may have lower quality

### Raspberry Pi 3/3B+
- USB 2.0 ports work fine for audio
- May need additional power for some USB microphones

### Raspberry Pi Zero/Zero W
- Limited USB ports
- May need USB hub for microphone + other devices
- Consider I2S microphone modules

## Final Checklist

- [ ] Audio hardware connected
- [ ] System packages updated
- [ ] Audio dependencies installed
- [ ] Python packages installed
- [ ] User added to audio groups
- [ ] Audio devices detected
- [ ] Audio test script runs successfully
- [ ] Microphone input levels adequate
- [ ] LED controller audio integration working

## Support

If you encounter issues:
1. Run the audio test script first
2. Check system audio configuration
3. Verify hardware connections
4. Check user permissions
5. Review troubleshooting section above
