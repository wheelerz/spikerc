# Debug UART Connection Script
# For diagnosing connection issues between computer and SPIKE Prime hub
# Use this to test communication before running the main controller

import sys
import asyncio
from bleak import BleakScanner, BleakClient

# Nordic UART Service UUIDs
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write to this characteristic
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Read from this characteristic

# Set threading model to MTA before importing bleak
sys.coinit_flags = 0

def notification_handler(sender, data):
    """Handle incoming data notifications from the hub"""
    try:
        print(f"[RECEIVED]: {data.decode('utf-8').strip()}")
    except:
        print(f"[RECEIVED RAW]: {data}")

async def main():
    # Scan for devices
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
    
    # Create client with debug enabled
    client = BleakClient(selected_device)
    
    try:
        # Connect with retry logic
        for attempt in range(3):
            try:
                await client.connect()
                print(f"Connected to {selected_device.name}")
                break
            except Exception as e:
                print(f"Connection attempt {attempt+1} failed: {e}")
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(1)
        
        if not client.is_connected:
            print("Failed to connect. Exiting...")
            return
        
        # List all services and characteristics
        print("\n== Services and Characteristics ==")
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Characteristic: {char.uuid}")
                print(f"    Properties: {', '.join(char.properties)}")
        
        # Check if UART service is available
        rx_char = None
        tx_char = None
        
        for service in client.services:
            if UART_SERVICE_UUID.lower() in service.uuid.lower():
                print(f"\nFound UART service: {service.uuid}")
                for char in service.characteristics:
                    if UART_RX_CHAR_UUID.lower() in char.uuid.lower():
                        rx_char = char.uuid
                        print(f"Found RX characteristic: {rx_char}")
                    elif UART_TX_CHAR_UUID.lower() in char.uuid.lower():
                        tx_char = char.uuid
                        print(f"Found TX characteristic: {tx_char}")
        
        if not rx_char:
            print("Could not find UART RX characteristic!")
            return
            
        if tx_char:
            # Try to subscribe to notifications to receive data from the hub
            print("Subscribing to notifications...")
            await client.start_notify(tx_char, notification_handler)
            print("Notifications active. You should see responses from the hub.")
        else:
            print("Warning: TX characteristic not found. Cannot receive responses from hub.")
        
        # Interactive command mode
        print("\n== Debug Command Mode ==")
        print("Enter commands to send to the hub. Type 'exit' to quit.")
        print("Common commands:")
        print("  test     - Send a test message")
        print("  rc(0,0)  - Stop motors")
        print("  rc(50,0) - Drive forward at 50% power")
        print("  stop()   - Emergency stop")
        
        while client.is_connected:
            command = input("\nCommand> ")
            
            if command.lower() == 'exit':
                break
            
            # Send command to the hub
            print(f"[SENDING]: {command}")
            try:
                # Add newline to simulate pressing enter
                await client.write_gatt_char(rx_char, f"{command}\n".encode())
                # Give hub time to respond
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error sending command: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up
        if client.is_connected:
            # Unsubscribe from notifications if we were subscribed
            if tx_char:
                try:
                    await client.stop_notify(tx_char)
                except:
                    pass
            
            # Send stop command before disconnecting
            if rx_char:
                try:
                    await client.write_gatt_char(rx_char, "stop()\n".encode())
                    print("Sent stop command")
                except:
                    pass
            
            # Disconnect
            await client.disconnect()
            print("Disconnected from hub")

if __name__ == "__main__":
    try:
        # For Windows compatibility
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