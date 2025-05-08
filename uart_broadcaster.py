# UART Broadcaster for Pybricks SPIKE Prime
# Broadcasts PS5 controller commands to Pybricks hub over BLE
# For host computer (Windows/Mac/Linux)

import asyncio
import pygame
import sys
import os
import time
import argparse
from bleak import BleakScanner, BleakClient

# Nordic UART Service UUIDs
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Initialize pygame for controller input
pygame.init()
pygame.joystick.init()

class PS5Controller:
    """Simple class for reading PS5/DualSense controller inputs"""
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
    
    def update(self):
        """Update controller states"""
        pygame.event.pump()
    
    def read(self):
        """Read control values for RC car"""
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

class PybricksUARTClient:
    """Client for communicating with Pybricks hub over BLE UART"""
    def __init__(self, hub_name="Pybricks Hub"):
        self.hub_name = hub_name
        self.client = None
        self.device = None
        self.rx_char = None
        self.tx_char = None
        self.connected = False
        self.ready = asyncio.Event()
        self.status_message = "Not connected"
    
    def handle_disconnect(self, client):
        """Handle BLE disconnect event"""
        print("Hub disconnected!")
        self.connected = False
        self.status_message = "Disconnected"
    
    def handle_rx(self, _, data):
        """Handle data received from hub"""
        # Check the event code to determine the type of data
        if len(data) > 0:
            # For UART data, which is usually text from print() on the hub
            message = data.decode('utf-8', errors='replace').strip()
            print(f"Hub says: {message}")
            self.status_message = message
            
            # If hub indicates it's ready, set the event
            if "ready" in message.lower():
                self.ready.set()
    
    async def find_hub(self):
        """Find Pybricks hub via BLE scan"""
        print(f"Scanning for {self.hub_name}...")
        
        try:
            # First look by name
            device = await BleakScanner.find_device_by_name(self.hub_name)
            
            # If not found by name, look through all devices
            if not device:
                print(f"Hub '{self.hub_name}' not found, scanning all devices...")
                devices = await BleakScanner.discover()
                
                # Find a device that might be our hub
                for d in devices:
                    # Check if name contains Pybricks, SPIKE, Hub, or Lego
                    if d.name and any(x in d.name.upper() for x in ["PYBRICKS", "SPIKE", "HUB", "LEGO"]):
                        print(f"Found potential hub: {d.name}")
                        device = d
                        break
            
            if device:
                print(f"Found hub: {device.name} ({device.address})")
                self.device = device
                return True
            else:
                print("No hub found. Make sure your SPIKE Prime is powered on with Pybricks firmware.")
                return False
        
        except Exception as e:
            print(f"Error scanning for hub: {e}")
            return False
    
    async def connect(self):
        """Connect to hub and set up UART service"""
        if not self.device:
            if not await self.find_hub():
                return False
        
        try:
            print(f"Connecting to {self.device.name}...")
            self.client = BleakClient(self.device, disconnected_callback=self.handle_disconnect)
            await self.client.connect()
            print(f"Connected to {self.device.name}")
            
            # Check for UART service
            for service in self.client.services:
                if service.uuid.lower() == UART_SERVICE_UUID.lower():
                    # Found UART service, now get the characteristics
                    for char in service.characteristics:
                        if char.uuid.lower() == UART_RX_CHAR_UUID.lower():
                            self.rx_char = char.uuid
                        elif char.uuid.lower() == UART_TX_CHAR_UUID.lower():
                            self.tx_char = char.uuid
            
            if self.rx_char and self.tx_char:
                # Subscribe to notifications from TX characteristic
                await self.client.start_notify(self.tx_char, self.handle_rx)
                self.connected = True
                self.status_message = "Connected"
                
                # Send a test message
                await self.write("test")
                
                # Wait for ready signal from hub
                try:
                    await asyncio.wait_for(self.ready.wait(), timeout=5.0)
                    return True
                except asyncio.TimeoutError:
                    print("Timed out waiting for hub to respond")
                    return True  # Still return True as we are connected
            else:
                print("UART service not found on hub")
                await self.client.disconnect()
                return False
                
        except Exception as e:
            print(f"Error connecting to hub: {e}")
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            return False
    
    async def write(self, message):
        """Write a message to the hub"""
        if not self.connected or not self.client or not self.rx_char:
            return False
        
        try:
            # Add newline to message to simulate pressing enter
            message = message + '\n'
            await self.client.write_gatt_char(self.rx_char, message.encode())
            return True
        except Exception as e:
            print(f"Error writing to hub: {e}")
            return False
    
    async def send_motor_command(self, drive, steer):
        """Send motor command to hub"""
        drive_int = int(drive * 100)  # Convert to integer -100 to 100
        steer_int = int(steer * 100)  # Convert to integer -100 to 100
        
        # Clamp values
        drive_int = max(-100, min(100, drive_int))
        steer_int = max(-100, min(100, steer_int))
        
        # Create command
        command = f"rc({drive_int},{steer_int})"
        return await self.write(command)
    
    async def send_stop_command(self):
        """Send stop command to hub"""
        return await self.write("stop()")
    
    async def disconnect(self):
        """Disconnect from hub"""
        if self.client and self.client.is_connected:
            # Send stop command before disconnecting
            await self.send_stop_command()
            await asyncio.sleep(0.1)
            
            # Disconnect
            await self.client.disconnect()
            print("Disconnected from hub")
        self.connected = False
        self.device = None
        self.rx_char = None
        self.tx_char = None

async def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UART Broadcaster for Pybricks SPIKE Prime")
    parser.add_argument("--hub", type=str, default="Pybricks Hub", help="Name of the hub to connect to")
    args = parser.parse_args()
    
    # Create PS5 controller
    controller = PS5Controller()
    if not controller.controller:
        print("No controller detected. Exiting...")
        pygame.quit()
        sys.exit(1)
    
    # Create Pybricks UART client
    uart_client = PybricksUARTClient(hub_name=args.hub)
    
    # Connect to hub
    if not await uart_client.connect():
        print("Failed to connect to hub. Exiting...")
        controller.close()
        sys.exit(1)
    
    print("\nRC car control ready:")
    print("- Left stick vertical: Drive (forward/backward)")
    print("- Right stick horizontal: Steering (left/right)")
    print("- Right trigger: Speed boost")
    print("- Right bumper: Emergency stop/disconnect")
    
    try:
        # Main control loop
        deadband = 0.1  # Ignore small stick movements
        update_rate = 0.05  # 50ms update rate = 20Hz
        last_command_time = time.time()
        
        while True:
            # Update controller state
            controller.update()
            
            # Read controller values
            drive, steer, trigger, emergency_stop = controller.read()
            
            # Check for emergency stop
            if emergency_stop:
                print("\nEmergency stop - stopping motors...")
                await uart_client.send_stop_command()
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
                await uart_client.send_motor_command(final_drive, final_steer)
                last_command_time = current_time
                
                # Print status update - use carriage return to overwrite
                print(f"\rDrive: {int(final_drive*100):4d} | Steer: {int(final_steer*100):4d} | Power: {int(power_scale*100):3d}% | Status: {uart_client.status_message}", end="")
            
            # Small delay to prevent CPU overload
            await asyncio.sleep(0.01)
    
    except asyncio.CancelledError:
        # Expected when cancelling the task
        pass
    except KeyboardInterrupt:
        print("\nUser interrupted - stopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Disconnect and clean up
        print("\nDisconnecting from hub...")
        await uart_client.disconnect()
        controller.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()
        sys.exit(1)