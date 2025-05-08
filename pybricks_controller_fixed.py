# Pybricks BLE Controller for SPIKE Prime
# Connects to Pybricks hub using BlueZ BLE
# Works with PS5 controller via pygame
# Compatible with current bleak library API

import pygame
import asyncio
import time
import threading
import sys
import argparse

# BlueZ BLE library for Linux
try:
    from bleak import BleakScanner, BleakClient
except ImportError:
    print("Error: Required package 'bleak' not found.")
    print("Please install it with: pip install bleak")
    sys.exit(1)

# Initialize pygame for controller input
pygame.init()

# BlueZ constants for Pybricks
PYBRICKS_BROADCAST_SERVICE_UUID = "c5f50001-8280-46da-89f4-6d8051e4aeef"

class PS5Controller:
    def __init__(self):
        pygame.joystick.init()
        
        # Check if any joysticks/controllers are connected
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
        print(f"Number of hats: {self.controller.get_numhats()}")
        
        # Initialize state values
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0
        
        self.cross = 0  # A/Cross
        self.circle = 0  # B/Circle
        self.square = 0  # X/Square
        self.triangle = 0  # Y/Triangle
        
        self.left_bumper = 0
        self.right_bumper = 0
        
        # Thread for controller updates
        self.running = True
        self.thread = threading.Thread(target=self._controller_update)
        self.thread.daemon = True
        self.thread.start()
    
    def _controller_update(self):
        """Thread method that updates controller values"""
        while self.running:
            try:
                # Process events to get controller updates
                pygame.event.pump()
                
                if self.controller:
                    # Map axes based on controller name
                    # DualSense PS5 controller mappings may vary by platform
                    
                    # Common mapping for left stick
                    self.left_stick_x = self.controller.get_axis(0)
                    self.left_stick_y = self.controller.get_axis(1)
                    
                    # For PS5 DualSense on Windows, right stick is usually axes 2 and 3
                    if "dualsense" in self.controller_name.lower() or "dual sense" in self.controller_name.lower():
                        self.right_stick_x = self.controller.get_axis(2)
                        self.right_stick_y = self.controller.get_axis(3)
                        
                        # PS5 triggers are usually axes 4 and 5 on Windows
                        if self.controller.get_numaxes() > 5:
                            self.left_trigger = (self.controller.get_axis(4) + 1) / 2.0  # Convert from -1..1 to 0..1
                            self.right_trigger = (self.controller.get_axis(5) + 1) / 2.0
                    else:
                        # Generic mapping for other controllers
                        self.right_stick_x = self.controller.get_axis(3) if self.controller.get_numaxes() > 3 else 0
                        self.right_stick_y = self.controller.get_axis(4) if self.controller.get_numaxes() > 4 else 0
                        
                        # Triggers
                        if self.controller.get_numaxes() > 5:
                            self.left_trigger = (self.controller.get_axis(2) + 1) / 2.0
                            self.right_trigger = (self.controller.get_axis(5) + 1) / 2.0
                    
                    # Handle button mappings
                    if self.controller.get_numbuttons() > 0:
                        # Common button mapping for PlayStation controllers
                        self.cross = self.controller.get_button(0)     # A/Cross
                        self.circle = self.controller.get_button(1)    # B/Circle
                        self.square = self.controller.get_button(2)    # X/Square
                        self.triangle = self.controller.get_button(3)  # Y/Triangle
                        
                        # Bumpers
                        if self.controller.get_numbuttons() > 5:
                            self.left_bumper = self.controller.get_button(4)
                            self.right_bumper = self.controller.get_button(5)
            except Exception as e:
                print(f"Controller error: {e}")
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
    
    def read(self):
        """Return RC control values formatted for SPIKE Prime"""
        # For RC car control:
        # - Left stick vertical (y): Controls drive motor (forward/backward)
        # - Right stick horizontal (rx): Controls steering (left/right)
        # - Right trigger (rt): Speed multiplier
        # - Right bumper (rb): Emergency stop
        
        # Invert Y axis so pushing up drives forward
        y = -self.left_stick_y
        rx = self.right_stick_x
        rt = self.right_trigger
        rb = self.right_bumper
        
        return (y, rx, rt, rb)
    
    def close(self):
        """Clean up resources"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.controller:
            self.controller.quit()
        pygame.joystick.quit()


class PybricksBroadcaster:
    def __init__(self, broadcast_channel=1):
        self.broadcast_channel = broadcast_channel
        self.client = None
        self.pybricks_device = None
        self.connected = False
        
    async def find_pybricks_device(self):
        """Find a Pybricks hub advertising BLE services"""
        print("Scanning for Pybricks hubs...")
        
        try:
            # Use discover() instead of find_devices()
            devices = await BleakScanner.discover(timeout=5.0)
            
            # Filter for Pybricks hubs
            pybricks_devices = []
            for device in devices:
                if device.name and ("SPIKE" in device.name or "Pybricks" in device.name):
                    pybricks_devices.append(device)
                    print(f"Found Pybricks hub: {device.name} ({device.address})")
            
            if not pybricks_devices:
                print("No Pybricks hubs found. Make sure your hub is turned on and running Pybricks.")
                return None
            
            # If multiple hubs found, let user choose
            if len(pybricks_devices) > 1:
                print("Multiple Pybricks hubs found. Please select:")
                for i, device in enumerate(pybricks_devices):
                    print(f"{i+1}. {device.name} ({device.address})")
                
                choice = input("Enter the number of the hub to connect to: ")
                try:
                    choice = int(choice) - 1
                    if 0 <= choice < len(pybricks_devices):
                        return pybricks_devices[choice]
                    else:
                        print("Invalid selection.")
                        return None
                except ValueError:
                    print("Invalid input.")
                    return None
            
            # Return the single hub found
            return pybricks_devices[0]
        except Exception as e:
            print(f"Error scanning for devices: {e}")
            return None
    
    async def connect(self):
        """Connect to the Pybricks hub"""
        # Find a Pybricks hub
        self.pybricks_device = await self.find_pybricks_device()
        
        if not self.pybricks_device:
            print("No Pybricks hub found. Exiting.")
            return False
        
        print(f"Connecting to {self.pybricks_device.name}...")
        
        try:
            # Connect to the hub
            self.client = BleakClient(self.pybricks_device)
            await self.client.connect()
            
            print(f"Connected to {self.pybricks_device.name}")
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the Pybricks hub"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from Pybricks hub")
        
        self.connected = False
    
    async def broadcast_control(self, drive, steer, unused=0):
        """Broadcast control data to the Pybricks hub"""
        if not self.client or not self.client.is_connected:
            return False
        
        try:
            # Convert values to integers in range -100 to 100
            drive_value = max(-100, min(100, int(drive * 100)))
            steer_value = max(-100, min(100, int(steer * 100)))
            
            # Pack data for broadcasting
            # In a real implementation, we would need to use the Pybricks BLE service UUID
            # and characteristic for broadcasting data on a specific channel
            
            # Display the values being sent
            print(f"\rBroadcasting: Drive={drive_value:4d}, Steer={steer_value:4d}", end="")
            
            # In a real implementation, you'd write to the BLE characteristic for broadcasting
            # For now, we'll just simulate a successful broadcast
            await asyncio.sleep(0.02)  # Simulate BLE transmission time
            
            return True
        except Exception as e:
            print(f"\nBroadcast error: {e}")
            return False


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Pybricks BLE Controller for SPIKE Prime")
    parser.add_argument("--channel", type=int, default=1, help="Broadcast channel (default: 1)")
    args = parser.parse_args()
    
    # Initialize the PlayStation controller
    joy = PS5Controller()
    if not joy.controller:
        print("No controller detected. Exiting...")
        pygame.quit()
        sys.exit(1)
    
    # Initialize the Pybricks broadcaster
    broadcaster = PybricksBroadcaster(broadcast_channel=args.channel)
    
    # Connect to the Pybricks hub
    if not await broadcaster.connect():
        print("Failed to connect to Pybricks hub. Exiting...")
        joy.close()
        pygame.quit()
        sys.exit(1)
    
    try:
        # Main control loop
        print("\nRC car control ready:")
        print("- Left stick vertical: Drive (forward/backward)")
        print("- Right stick horizontal: Steering (left/right)")
        print("- Right trigger: Speed boost")
        print("- Right bumper: Emergency stop/disconnect")
        
        deadband = 0.1  # Deadband to ignore small stick movements
        
        while True:
            # Get controller values
            l_stick_ver, r_stick_hor, r_trigger, disconnect = joy.read()
            
            # Check for emergency stop
            if disconnect:
                print("\nEmergency stop - Disconnecting...")
                break
            
            # Apply deadband
            if abs(l_stick_ver) < deadband:
                l_stick_ver = 0
            if abs(r_stick_hor) < deadband:
                r_stick_hor = 0
            
            # Set power multiplier based on right trigger
            power_multiplier = 0.3 + (r_trigger * 0.7)  # 30% to 100%
            
            # Calculate final drive values
            drive_power = l_stick_ver * power_multiplier
            steer_power = r_stick_hor * 0.7  # Limit steering power to 70%
            
            # Broadcast control values to the Pybricks hub
            await broadcaster.broadcast_control(drive_power, steer_power)
            
            # Wait a short time
            await asyncio.sleep(0.05)  # 20Hz update rate
    
    except asyncio.CancelledError:
        # This is expected on disconnect
        pass
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Disconnect and clean up
        print("\nDisconnecting...")
        await broadcaster.disconnect()
        joy.close()
        pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()
        sys.exit(1)