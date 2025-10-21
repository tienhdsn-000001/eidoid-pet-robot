#!/usr/bin/env python3
# test_rpi5_setup.py
# Test script to verify Raspberry Pi 5 setup for Eidoid Pet Robot

import sys
import os
import platform
import subprocess
import importlib.util

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.9+")
        return False

def test_platform():
    """Test if running on Raspberry Pi"""
    print("Testing platform...")
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo:
                print("✓ Running on Raspberry Pi")
                return True
            else:
                print("⚠ Not running on Raspberry Pi (may still work)")
                return True
    except:
        print("⚠ Cannot determine platform")
        return True

def test_required_packages():
    """Test if required Python packages are installed"""
    print("Testing required packages...")
    required_packages = [
        'pyaudio', 'numpy', 'google.genai', 'websockets', 
        'openwakeword', 'onnxruntime', 'serial', 'RPi.GPIO'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'google.genai':
                import google.genai
            elif package == 'serial':
                import serial
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - Missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def test_audio_devices():
    """Test audio device detection"""
    print("Testing audio devices...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        input_devices = []
        output_devices = []
        
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                input_devices.append((i, device_info.get('name')))
            if device_info.get('maxOutputChannels') > 0:
                output_devices.append((i, device_info.get('name')))
        
        print(f"✓ Found {len(input_devices)} input devices")
        print(f"✓ Found {len(output_devices)} output devices")
        
        # Check for USB devices
        usb_inputs = [d for d in input_devices if any(kw in d[1].lower() for kw in ['usb', 'audio'])]
        usb_outputs = [d for d in output_devices if any(kw in d[1].lower() for kw in ['usb', 'audio'])]
        
        if usb_inputs:
            print(f"✓ Found USB microphone: {usb_inputs[0][1]}")
        else:
            print("⚠ No USB microphone detected")
            
        if usb_outputs:
            print(f"✓ Found USB speaker: {usb_outputs[0][1]}")
        else:
            print("⚠ No USB speaker detected")
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"✗ Audio test failed: {e}")
        return False

def test_serial_devices():
    """Test serial device detection"""
    print("Testing serial devices...")
    try:
        import glob
        usb_devices = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        if usb_devices:
            print(f"✓ Found USB serial devices: {usb_devices}")
            return True
        else:
            print("⚠ No USB serial devices found (Pico may not be connected)")
            return True
    except Exception as e:
        print(f"✗ Serial test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variables"""
    print("Testing environment variables...")
    required_vars = ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is not set")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def test_file_permissions():
    """Test file permissions"""
    print("Testing file permissions...")
    try:
        # Test if we can write to the current directory
        test_file = 'test_write_permission.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✓ Write permissions OK")
        return True
    except Exception as e:
        print(f"✗ Write permission test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Eidoid Pet Robot - Raspberry Pi 5 Setup Test ===\n")
    
    tests = [
        test_python_version,
        test_platform,
        test_required_packages,
        test_audio_devices,
        test_serial_devices,
        test_environment_variables,
        test_file_permissions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
        print()
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Your Raspberry Pi 5 is ready for Eidoid Pet Robot.")
        print("\nNext steps:")
        print("1. Run 'python main.py' to start the robot")
        print("2. Say 'Hey Jarvis' to activate")
    else:
        print("⚠ Some tests failed. Please check the setup instructions.")
        print("\nCommon fixes:")
        print("- Run './setup_rpi5.sh' to install dependencies")
        print("- Set up your .env file with API keys")
        print("- Connect USB microphone and speaker")
        print("- Check USB connections")

if __name__ == "__main__":
    main()