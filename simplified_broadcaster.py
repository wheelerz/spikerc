# Simplified UART Broadcaster for Pybricks SPIKE Prime
# NO THREAD CALLBACKS during scanning - maximum compatibility
# For host computer (Windows/Mac/Linux)

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

async def main():
    # Create controller
    controller = SimpleController()
    if not controller.controller:
        print("No controller detected. Exiting...")
        pygame.quit()
        sys.exit(1)
    
    # Simple manual scan for Pybricks hub - no callbacks
    print("Scanning for Pybricks hub...")
    
    # Use discover() instead of callbacks-based find_device
    devices = await BleakScanner.discover()
    
    # Look for a hub with "Pybricks", "SPIKE", or "Hub" in the name
    hub_device = None
    for device in devices:
        if device.name:
            print(f"Found device: {device.name} ({device.address})")
            if any(keyword in device.name for keyword in ["Pybricks", "SPIKE", "Hub", "LEGO"]):
                hub_device = device
                print(f"Found potential hub: {device.name}")
                # Ask for confirmation
                choice = input(f"Is this your SPIKE Prime hub? (Y/n): ")
                if choice.lower() != "n":
                    break
    
    if not hub_device:
        print("No Pybricks hub found. Make sure it's turned on and running your code.")
        controller.close()
        sys.exit(1)
    
    print(f"Connecting to {hub_device.name}...")
    
    # Use a simple client that doesn't rely on callbacks for disconnect
    client = BleakClient(hub_device)
    
    try:
        # Connect to the hub
        await client.connect()
        print(f"Connected to {hub_device.name}")
        
        # Find UART service characteristics
        rx_char = None
        tx_char = None
        
        for service in client.services:
            if service.uuid.lower() == UART_SERVICE_UUID.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == UART_RX_CHAR_UUID.lower():
                        rx_char = char.uuid
                    elif char.uuid.lower() == UART_TX_CHAR_UUID.lower():
                        tx_char = char.uuid
        
        if not rx_char:
            print("Could not find UART RX characteristic")
            await client.disconnect()
            controller.close()
            sys.exit(1)
        
        print("Found UART service, ready to send commands")
        
        # Send a test command and wait for hub to be ready
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
        
        try:
            while await client.is_connected():
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
                power_scale = 0.3 + (trigger * 0.7)  # Scale from 30% to 100% based on trigger
                final_drive = drive * power_scale
                final_steer = steer * 0.7  # Limit steering to 70% to protect mechanisms
                
                # Only send commands at the specified update rate
                current_time = time.time()
                if current_time - last_command_time >= update_rate:
                    # Create command
                    drive_int = int(final_drive * 100)
                    steer_int = int(final_steer * 100)
                    command = f"rc({drive_int},{steer_int})\n"
                    
                    # Send command to hub
                    await client.write_gatt_char(rx_char, command.encode())
                    last_command_time = current_time
                    
                    # Print status
                    print(f"\rDrive: {drive_int:4d} | Steer: {steer_int:4d} | Power: {int(power_scale*100):3d}%", end="")
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)
                
                # Check connection status every 100ms
                if (time.time() - last_command_time) > 0.1:
                    if not await client.is_connected():
                        print("\nLost connection to hub")
                        break
        
        except Exception as e:
            print(f"\nError in control loop: {e}")
        
        # Send stop command before disconnecting
        try:
            await client.write_gatt_char(rx_char, "stop()\n".encode())
            print("\nSent stop command to hub")
        except:
            pass
        
        # Disconnect from hub
        try:
            if await client.is_connected():
                await client.disconnect()
                print("Disconnected from hub")
        except:
            pass
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Final cleanup
        controller.close()
        print("Controller closed, exiting")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUser interrupted - exiting")
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()