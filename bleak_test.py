import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    
    if not devices:
        print("No BLE devices found.")
        return

    print("\nFound BLE devices:")
    for idx, device in enumerate(devices, 1):
        name = device.name or "Unknown"
        print(f"{idx}. {name} [{device.address}]")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())

