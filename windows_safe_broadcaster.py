# Windows-safe broadcaster for Pybricks SPIKE Prime
# NO THREAD CALLBACKS at all - safe for Windows GUI threads
# For host computer (Windows/Mac/Linux)
# This version uses polling instead of callbacks

import asyncio
import pygame
import sys
import os
import time

# Import bleak but handle errors gracefully
try:
    from bleak import BleakScanner, BleakClient
except ImportError:
    print("The 'bleak' package is required. Please install it with: pip install bleak")
    sys.exit(1)

# Nordic UART Service UUIDs
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write to this characteristic
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notifications come from this characteristic

# Initialize pygame for controller input
pygame.init()
pygame.joystick.init()

class SimpleController:
    """Basic controller class with no threading"""
    def __init__(self):
        if pygame.joystick.get_count() == 0:
            print("No controllers found. Please connect a controller and try again.")
            self.controller = None
            return
            
        # Initialize the first joystick
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        
        # Print controller info
        self.controller_name = self.controller.get_name()
        print(f"Controller connected: {self.controller_name}")
        print(f"Number of axes: {self.controller.get_numaxes()}")
        print(f"Number of buttons: {self.controller.get_numbuttons()}")
    
    def read(self):
        """Read control values for RC car"""
        # Process pygame events
        pygame.event.pump()
        
        if not self.controller:
            return 0, 0, 0, 0
        
        # Read stick values - invert Y so up is positive
        left_y = -self.controller.get_axis(1)
        
        # Handle different controller types
        if "dualsense" in self.controller_name.lower():
            right_x = self.controller.get_axis(2)  # PS5 controller
            right_trigger = (self.controller.get_axis(5) + 1) / 2.0  # 0 to 1
        else:
            right_x = self.controller.get_axis(3)  # Generic/Xbox controller
            right_trigger = (self.controller.get_axis(5) + 1) / 2.0  # 0 to 1
        
        # Read bumper for emergency stop
        right_bumper = 1 if self.controller.get_button(5) else 0
        
        return left_y, right_x, right_trigger, right_bumper
    
    def close(self):
        """Clean up pygame resources"""
        pygame.joystick.quit()
        pygame.quit()

async def scan_for_hub():
    """Scan for Pybricks hub without callbacks"""
    print("Scanning for Pybricks hub...")
    try:
        # Use simple discover method
        devices = await BleakScanner.discover()
        
        # Look for a hub with "Pybricks", "SPIKE", or "Hub" in the name
        pybricks_devices = []
        for device in devices:
            if device.name:
                print(f"Found device: {device.name}")
                if any(keyword.lower() in device.name.lower() for keyword in ["Pybricks", "SPIKE", "Hub", "LEGO"]):
                    pybricks_devices.append(device)
                    print(f"Found potential hub: {device.name}")
        
        # If no devices found
        if not pybricks_devices:
            print("No Pybricks hubs found")
            return None
        
        # If only one device found, return it
        if len(pybricks_devices) == 1:
            device = pybricks_devices[0]
            choice = input(f"Use SPIKE Prime hub '{device.name}'? (Y/n): ")
            if choice.lower() != "n":
                return device
            return None
        
        # If multiple devices found, let user choose
        print("\nMultiple potential hubs found. Please choose one:")
        for i, device in enumerate(pybricks_devices):
            print(f"{i+1}. {device.name}")
        
        choice = input("Enter hub number: ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(pybricks_devices):
                return pybricks_devices[index]
        except ValueError:
            pass
        
        return None
    
    except Exception as e:
        print(f"Error scanning for devices: {e}")
        return None

async def main():
    """Main program function"""
    # Create controller
    controller = SimpleController()
    if not controller.controller:
        print("No controller detected. Exiting...")
        pygame.quit()
        sys.exit(1)
    
    # Scan for hub
    hub_device = await scan_for_hub()
    
    if not hub_device:
        print("No hub selected. Exiting...")
        controller.close()
        sys.exit(1)
    
    print(f"Connecting to {hub_device.name}...")
    
    # Connect to hub manually, with no callbacks
    client = None
    try:
        client = BleakClient(hub_device, timeout=10.0)
        
        # Connect with retries
        for attempt in range(3):
            try:
                await client.connect()
                break
            except Exception as e:
                print(f"Connection attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(1)
        
        if not client.is_connected:
            print("Failed to connect. Exiting...")
            controller.close()
            sys.exit(1)
        
        print(f"Connected to {hub_device.name}")
        
        # Find UART service characteristics
        rx_char = None
        for service in client.services:
            for char in service.characteristics:
                if UART_RX_CHAR_UUID.lower() in char.uuid.lower():
                    rx_char = char.uuid
                    break
            if rx_char:
                break
        
        if not rx_char:
            print("Could not find UART RX characteristic")
            await client.disconnect()
            controller.close()
            sys.exit(1)
        
        print("Found UART service, ready to send commands")
        
        # Send a test command
        await client.write_gatt_char(rx_char, "test\n".encode())
        
        # Give hub time to initialize
        print("Waiting for hub to be ready...")
        await asyncio.sleep(2)
        
        # Main control loop
        print("\nRC car control ready:")
        print("- Left stick vertical: Drive (forward/backward)")
        print("- Right stick horizontal: Steering (left/right)")
        print("- Right trigger: Speed boost")
        print("- Right bumper: Emergency stop/disconnect")
        
        deadband = 0.1  # Ignore small stick movements
        last_command_time = time.time()
        update_rate = 0.05  # 50ms = 20Hz
        
        # Initialize last values
        last_drive = 0
        last_steer = 0
        
        while True:
            # Check if still connected - do this without callbacks
            if not client.is_connected:
                print("\nLost connection to hub")
                break
            
            # Read controller values
            drive, steer, trigger, emergency_stop = controller.read()
            
            # Check for emergency stop
            if emergency_stop:
                print("\nEmergency stop - stopping motors...")
                await client.write_gatt_char(rx_char, "stop()\n".encode())
                await asyncio.sleep(0.5)
                break
            
            # Apply deadband
            if abs(drive) < deadband:
                drive = 0
            if abs(steer) < deadband:
                steer = 0
            
            # Apply power scaling
            power_scale = 0.3 + (trigger * 0.7)  # 30% to 100% based on trigger
            final_drive = drive * power_scale
            final_steer = steer * 0.7  # Limit steering to 70%
            
            # Check if values changed significantly or update interval elapsed
            drive_int = int(final_drive * 100)
            steer_int = int(final_steer * 100)
            values_changed = (abs(drive_int - last_drive) > 5 or abs(steer_int - last_steer) > 5)
            time_elapsed = (time.time() - last_command_time) >= update_rate
            
            if values_changed or time_elapsed:
                # Create command
                command = f"rc({drive_int},{steer_int})\n"
                
                # Send command to hub
                try:
                    await client.write_gatt_char(rx_char, command.encode())
                    last_command_time = time.time()
                    last_drive = drive_int
                    last_steer = steer_int
                    
                    # Print status
                    print(f"\rDrive: {drive_int:4d} | Steer: {steer_int:4d} | Power: {int(power_scale*100):3d}%", end="")
                except Exception as e:
                    print(f"\nError sending command: {e}")
                    break
            
            # Small delay to prevent CPU overload
            await asyncio.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nUser interrupted - stopping...")
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        # Final cleanup
        if client and client.is_connected:
            try:
                # Send stop command
                if rx_char:
                    await client.write_gatt_char(rx_char, "stop()\n".encode())
                    print("\nSent stop command")
                
                # Disconnect
                await client.disconnect()
                print("Disconnected from hub")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        controller.close()

if __name__ == "__main__":
    # Set event loop policy for Windows
    if sys.platform == "win32":
        # Use Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()