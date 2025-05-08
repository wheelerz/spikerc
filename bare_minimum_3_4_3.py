# Bare minimum SPIKE Prime RC code
# Designed specifically for SPIKE Prime v3.4.3
# Ultra simplified to work in SPIKE IDE

import hub
import bluetooth
import struct
import time
import motor

# Basic BLE setup
ble = bluetooth.BLE()
ble.active(True)
ble.config(gap_name="SPIKE")

# Simple advertising data
adv_data = bytes([
    0x02, 0x01, 0x06,  # General discoverable mode
    0x06, 0x09, 0x53, 0x50, 0x49, 0x4B, 0x45,  # Name "SPIKE"
])
ble.gap_advertise(100, adv_data)

# Set up UART service
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

((tx_handle, rx_handle),) = ble.gatts_register_services((uart_service,))

# Connected flag
connected = False

# Show ready status using 3.4.3 light_matrix API
hub.light_matrix.show("00900:09990:00900:00000:00000")
print("RC Car ready")

# BLE event handler
def on_ble_event(event, data):
    global connected
    
    if event == 1:  # Connect
        connected = True
        hub.light_matrix.show("00000:09990:09090:09990:00000")
        hub.sound.beep(440, 100)  # Connection beep
        
    elif event == 2:  # Disconnect
        connected = False
        hub.light_matrix.show("00000:00000:09990:00000:00000")
        hub.sound.beep(220, 100)  # Disconnection beep
        
        # Stop motors using 3.4.3 API
        try:
            motor.stop(hub.port.A)
            motor.stop(hub.port.B)
        except:
            try:
                # Fallback if the primary method fails
                hub.port.A.motor.stop()
                hub.port.B.motor.stop()
            except:
                pass
        
        # Restart advertising
        ble.gap_advertise(100, adv_data)
        
    elif event == 3:  # Write
        # Read control data
        buffer = ble.gatts_read(rx_handle)
        if len(buffer) == 3:
            drive, steer, _ = struct.unpack("bbB", buffer)
            
            # Apply motor control using 3.4.3 API
            try:
                # New 3.4.3 API
                motor.start(hub.port.B, drive)  # Drive motor
                motor.start(hub.port.A, steer)  # Steering motor
            except:
                try:
                    # Fallback methods if the above doesn't work
                    hub.port.B.motor.run(drive)
                    hub.port.A.motor.run(steer)
                except:
                    pass

# Register event handler
ble.irq(on_ble_event)

# Main loop (keep program running)
while True:
    # Small delay to prevent high CPU usage
    time.sleep(0.1)