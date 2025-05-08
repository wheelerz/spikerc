import asyncio
import sys
import struct
import time
import pygame
import threading
import math

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# SPIKE Prime UART service UUIDs
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# Initialize pygame for controller input
pygame.init()

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
        
        return [y, rx, rt, rb]
    
    def close(self):
        """Clean up resources"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.controller:
            self.controller.quit()
        pygame.joystick.quit()


async def uart_terminal():
    print("=== SPIKE Prime RC Controller (Pygame Version) ===")
    print("Scanning for SPIKE Prime devices...")
    
    # First try to find by specific address if you know it
    # Replace with your SPIKE Prime's MAC address if known
    spike_address = "E0:FF:F1:4F:05:C8"  # Update this with your SPIKE Prime MAC address
    
    try:
        device = await BleakScanner.find_device_by_address(spike_address)
        if device:
            print(f"Found SPIKE Prime device at address: {spike_address}")
        else:
            # If specific address not found, try to find by service UUID or name
            print(f"Device with address {spike_address} not found. Scanning for any SPIKE Prime...")
            devices = await BleakScanner.discover()
            for d in devices:
                print(f"Found device: {d.name} ({d.address})")
                # If you know your SPIKE Prime shows up with a specific name, you can filter by that
                if d.name and ("SPIKE" in d.name.upper() or "LEGO" in d.name.upper()):
                    device = d
                    print(f"Found SPIKE Prime device: {d.name} ({d.address})")
                    break
    except Exception as e:
        print(f"Error during device scanning: {e}")
        device = None

    if device is None:
        print("No SPIKE Prime device found. Please check that:")
        print("1. Your SPIKE Prime hub is powered on")
        print("2. Bluetooth is enabled on both devices")
        print("3. You've loaded the robot_python_code.py on the SPIKE Prime")
        print("4. If you know your SPIKE Prime's MAC address, edit it in this file")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device disconnected")
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print("Data received:", data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected to SPIKE Prime. Setting up controller...")
        rx_char = UART_RX_CHAR_UUID

        try:
            # Initialize controller
            joy = PS5Controller()
            if not joy.controller:
                print("No controller detected. Exiting...")
                sys.exit(1)
                
            print(f"Controller ready: {joy.controller_name}")
            print("\nRC Car control:")
            print("- Left stick vertical: Drive (forward/backward)")
            print("- Right stick horizontal: Steering (left/right)")
            print("- Right trigger: Speed boost")
            print("- Right bumper: Emergency stop/disconnect")
            
            # Control loop
            deadband = 0.1  # Deadband to ignore small stick movements
            
            while True:
                # Get controller values
                l_stick_ver, r_stick_hor, r_trigger, disconnect = joy.read()
                
                if disconnect:
                    print("\nEmergency stop - Disconnecting...")
                    break
                else:
                    # Apply deadband to remove jitter when sticks are near center
                    if deadband >= abs(l_stick_ver) >= 0:
                        l_stick_ver = 0
                    if deadband >= abs(r_stick_hor) >= 0:
                        r_stick_hor = 0
                    
                    # Set power multiplier based on right trigger
                    # Base power is 30% when trigger is not pressed
                    # Full trigger press gives 100% power
                    if r_trigger < 0.1:  # Almost not pressed
                        power_multiplier = 30  # Base power 30%
                    else:
                        # Scale from 30% to 100% based on trigger position
                        power_multiplier = 30 + (r_trigger * 70)
                    
                    # Calculate drive power from left stick vertical position
                    drive_power = l_stick_ver * (power_multiplier / 100)
                    
                    # Calculate steering power from right stick horizontal
                    # The steering motor usually needs less power, so we scale it to 70%
                    # This prevents damaging the steering mechanism
                    steering_power = r_stick_hor * 0.7
                    
                    # Scale values to SPIKE motor power range (-100 to 100)
                    drive_motor_power = int(drive_power * 100)
                    steering_motor_power = int(steering_power * 100)
                    
                    # Display the current control values
                    print(f"\rDrive: {drive_motor_power:4d} | Steer: {steering_motor_power:4d} | Power: {power_multiplier:3.0f}% | Stop: {disconnect}", end="")
                    
                    # Pack data to send to SPIKE Prime
                    controller_state = struct.pack("bbB",
                                               drive_motor_power,    # Drive motor (B)
                                               steering_motor_power, # Steering motor (A)
                                               0)                    # Unused parameter
                    
                    # Send data to SPIKE Prime
                    await client.write_gatt_char(rx_char, controller_state)
                    await asyncio.sleep(0.02)  # 50Hz update rate
                    
        except Exception as e:
            print(f"\nController error: {e}")
        finally:
            # Clean up
            if 'joy' in locals():
                joy.close()
            pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        # This is expected on disconnect
        pass
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure pygame is properly quit
        pygame.quit()