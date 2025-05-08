# Fixed controller for Pybricks SPIKE Prime 
# Fixes "Thread is configured for Windows GUI but callbacks are not working" error
# Works by setting the correct threading model before imports

import sys
# Set threading model to MTA before importing pygame or bleak
# This prevents the "Thread is configured for Windows GUI but callbacks are not working" error
sys.coinit_flags = 0  # Use Multi-Threaded Apartment (MTA) model instead of STA

# Now we can safely import pygame and bleak
import asyncio
import pygame
from bleak import BleakScanner, BleakClient

# Nordic UART Service UUIDs
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write to this characteristic

# Initialize pygame for controller
pygame.init()
pygame.joystick.init()

async def main():
    # Initialize controller
    if pygame.joystick.get_count() == 0:
        print("No controllers found. Please connect a controller and try again.")
        return
        
    controller = pygame.joystick.Joystick(0)
    controller.init()
    print(f"Controller connected: {controller.get_name()}")
    
    # Scan for devices - using the method that works for you
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    
    if not devices:
        print("No BLE devices found.")
        return

    # Print devices and let user select
    pybricks_devices = []
    print("\nFound BLE devices:")
    for idx, device in enumerate(devices, 1):
        name = device.name or "Unknown"
        print(f"{idx}. {name} [{device.address}]")
        
        # Identify potential Pybricks devices
        if name and any(keyword.lower() in name.lower() for keyword in ["pybricks", "spike", "hub", "lego"]):
            pybricks_devices.append((idx, device))
    
    # Help user identify Pybricks devices
    if pybricks_devices:
        print("\nPotential SPIKE/Pybricks hubs:")
        for idx, device in pybricks_devices:
            print(f"{idx}. {device.name} [{device.address}]")
    
    # Let user select device
    selection = input("\nEnter device number to connect to: ")
    try:
        selected_idx = int(selection) - 1
        if selected_idx < 0 or selected_idx >= len(devices):
            print("Invalid selection.")
            return
        selected_device = devices[selected_idx]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    # Connect to selected device
    print(f"Connecting to {selected_device.name}...")
    try:
        async with BleakClient(selected_device) as client:
            print(f"Connected to {selected_device.name}")
            
            # Find UART service and RX characteristic
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
                return
            
            print("UART service found, ready to send commands")
            print("\nRC car control ready:")
            print("- Left stick vertical: Drive (forward/backward)")
            print("- Right stick horizontal: Steering (left/right)")
            print("- Right trigger: Speed boost")
            print("- Right bumper: Emergency stop/disconnect")
            
            # Main control loop
            try:
                while client.is_connected:
                    # Process pygame events
                    pygame.event.pump()
                    
                    # Read controller
                    left_y = -controller.get_axis(1)  # Invert Y
                    right_x = controller.get_axis(2) if "dualsense" in controller.get_name().lower() else controller.get_axis(3)
                    right_trigger = (controller.get_axis(5) + 1) / 2.0
                    right_bumper = controller.get_button(5)
                    
                    # Check emergency stop
                    if right_bumper:
                        print("\nEmergency stop")
                        await client.write_gatt_char(rx_char, "stop()\n".encode())
                        break
                    
                    # Apply deadband
                    if abs(left_y) < 0.1: left_y = 0
                    if abs(right_x) < 0.1: right_x = 0
                    
                    # Calculate motor powers
                    power_scale = 0.3 + (right_trigger * 0.7)
                    drive_power = int(left_y * power_scale * 100)
                    steer_power = int(right_x * 0.7 * 100)
                    
                    # Send command
                    command = f"rc({drive_power},{steer_power})\n"
                    await client.write_gatt_char(rx_char, command.encode())
                    
                    # Print status
                    print(f"\rDrive: {drive_power:4d} | Steer: {steer_power:4d} | Power: {int(power_scale*100):3d}%", end="")
                    
                    # Short delay
                    await asyncio.sleep(0.05)
            except Exception as e:
                print(f"\nError in control loop: {e}")
            
            # Send stop before disconnecting
            try:
                await client.write_gatt_char(rx_char, "stop()\n".encode())
                print("\nMotors stopped")
            except:
                pass
    
    except Exception as e:
        print(f"Connection error: {e}")
    
    finally:
        pygame.quit()
        print("Exiting")

if __name__ == "__main__":
    try:
        # For Windows compatibility, use the correct event loop policy
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Additional STA handling for Windows 
        try:
            from bleak.backends.winrt.util import uninitialize_sta
            uninitialize_sta()  # undo any unwanted STA configuration
        except ImportError:
            pass  # not Windows or older Bleak version
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUser interrupted")
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()