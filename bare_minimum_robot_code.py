# Bare minimum SPIKE Prime RC code
# For SPIKE Prime v3.4.3
# Ultra simplified to ensure IDE compatibility

import hub
import bluetooth
import struct
import time

# Basic BLE setup
ble = bluetooth.BLE()
ble.active(True)
ble.config(gap_name="SPIKE")

# Advertising data
adv_data = bytes([
    0x02, 0x01, 0x06,  # General discoverable mode
    0x06, 0x09, 0x53, 0x50, 0x49, 0x4B, 0x45,  # Name "SPIKE"
])
ble.gap_advertise(100, adv_data)

# UART service
svc_uuid = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
rx_uuid = bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
tx_uuid = bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

uart_service = (
    svc_uuid,
    (
        (tx_uuid, bluetooth.FLAG_NOTIFY),
        (rx_uuid, bluetooth.FLAG_WRITE),
    ),
)

# Register service
((tx_handle, rx_handle),) = ble.gatts_register_services((uart_service,))

# Connected flag
connected = False

# Show ready status
hub.display.show(hub.Image.HAPPY)
print("RC Car ready")

# BLE event handler
def on_ble_event(event, data):
    global connected
    
    if event == 1:  # Connect
        connected = True
        hub.display.show(hub.Image.HEART)
        
    elif event == 2:  # Disconnect
        connected = False
        hub.display.show(hub.Image.HAPPY)
        # Stop motors
        hub.port.A.motor.stop()
        hub.port.B.motor.stop()
        # Restart advertising
        ble.gap_advertise(100, adv_data)
        
    elif event == 3:  # Write
        # Read control data
        buffer = ble.gatts_read(rx_handle)
        if len(buffer) == 3:
            drive, steer, _ = struct.unpack("bbB", buffer)
            
            # Apply motor control
            hub.port.B.motor.run(drive)  # Drive motor
            hub.port.A.motor.run(steer)  # Steering motor

# Register event handler
ble.irq(on_ble_event)

# Main loop (keep program running)
while True:
    # Small delay to prevent high CPU usage
    time.sleep(0.1)