import os
import sys
import time

# Try multiple controller libraries to see which one works
libraries = []

print("Detecting controller libraries...")

# Try the 'inputs' library
try:
    import inputs
    print("✓ 'inputs' library is installed")
    libraries.append("inputs")
except ImportError:
    print("✗ 'inputs' library is not installed")

# Try pygame
try:
    import pygame
    print("✓ 'pygame' library is installed")
    libraries.append("pygame")
except ImportError:
    print("✗ 'pygame' library is not installed")

# List all connected devices using different methods
print("\n=== Detected Controllers ===\n")

# Try inputs library
if "inputs" in libraries:
    print("Checking with 'inputs' library:")
    try:
        from inputs import devices
        print(f"  All devices: {devices.all_devices}")
        print(f"  Gamepads: {devices.gamepads}")
        
        # Check if any device names contain "dualsense", "dual sense", "ps5", etc.
        ps5_devices = [d for d in devices.all_devices if any(x in d.name.lower() for x in ["dualsense", "dual sense", "ps5", "dualshock", "dual shock"])]
        if ps5_devices:
            print("  PS5 Controller detected in 'all_devices':", ps5_devices)
        else:
            print("  No PS5 Controller found in 'all_devices'")
            
    except Exception as e:
        print(f"  Error checking inputs devices: {e}")

# Try pygame
if "pygame" in libraries:
    print("\nChecking with 'pygame' library:")
    try:
        pygame.init()
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()
        print(f"  Number of joysticks: {joystick_count}")
        
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            try:
                jid = joystick.get_instance_id()
            except AttributeError:
                jid = joystick.get_id()
            name = joystick.get_name()
            guid = pygame.joystick.Joystick(i).get_guid() if hasattr(pygame.joystick.Joystick(i), 'get_guid') else "Unknown"
            
            print(f"  Joystick {i} id: {jid}, name: {name}, guid: {guid}")
            
            try:
                axes = joystick.get_numaxes()
                buttons = joystick.get_numbuttons()
                hats = joystick.get_numhats()
                balls = joystick.get_numballs()
                print(f"    Axes: {axes}, Buttons: {buttons}, Hats: {hats}, Trackballs: {balls}")
            except:
                print("    Could not get controller details")
                
    except Exception as e:
        print(f"  Error checking pygame joysticks: {e}")
    finally:
        pygame.quit()

# Check Windows-specific controller info
if sys.platform.startswith('win'):
    print("\nChecking Windows controller information:")
    try:
        import subprocess
        result = subprocess.run(["powershell", "-Command", "Get-PnpDevice | Where-Object {$_.FriendlyName -like '*controller*'}"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"  Error running PowerShell command: {result.stderr}")
    except Exception as e:
        print(f"  Error checking Windows controllers: {e}")

print("\n=== Recommendation ===")
if "pygame" in libraries:
    print("Based on detected controllers, pygame is recommended for PS5 DualSense support.")
    print("Run the pygame_controller.py script to test your controller.")
elif "inputs" in libraries:
    print("The 'inputs' library is available but may not support your controller.")
    print("Consider installing pygame for better controller support.")
else:
    print("No supported controller libraries detected.")
    print("Please install pygame with: pip install pygame")

print("\nThis file will close in 60 seconds...")
time.sleep(60)