# Minimal SPIKE Prime RC receiver code
# For SPIKE Prime v3.4.3
# This version is highly simplified to ensure compatibility

import hub
import bluetooth
import struct
import time

# Basic BLE setup
ble = bluetooth.BLE()
ble.active(True)
ble.config(gap_name="SPIKE_RC")

# Set up advertising
def advertise():
    payload = bytearray()
    payload += b'\x02\x01\x06'
    payload += b'\x08\x09' + b'SPIKE_RC'
    ble.gap_advertise(100, payload)
    print("Advertising as SPIKE_RC")

# UART UUIDs
_UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_TX = bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_RX = bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')

# UART service
_UART_SERVICE = (
    _UART_UUID,
    (
        (_UART_TX, bluetooth.FLAG_NOTIFY),
        (_UART_RX, bluetooth.FLAG_WRITE),
    ),
)

# Register services
services = (_UART_SERVICE,)
((tx_handle, rx_handle),) = ble.gatts_register_services(services)

# Variables
connected = False
drive_power = 0
steer_power = 0

# BLE event handler
def ble_irq(event, data):
    global connected, drive_power, steer_power
    
    if event == 1:  # Connect
        connected = True
        hub.display.show(hub.Image.HAPPY)
        print("Connected")
        
    elif event == 2:  # Disconnect
        connected = False
        hub.display.show(hub.Image.SAD)
        print("Disconnected")
        # Stop motors
        hub.port.A.motor.stop()
        hub.port.B.motor.stop()
        # Restart advertising
        advertise()
        
    elif event == 3:  # Write
        # Read control data
        buffer = ble.gatts_read(rx_handle)
        if len(buffer) == 3:
            drive_power, steer_power, _ = struct.unpack("bbB", buffer)
            print("Drive:", drive_power, "Steer:", steer_power)

# Register handler and start advertising
ble.irq(ble_irq)
advertise()

# Display waiting message
hub.display.show(hub.Image.DIAMOND)
print("RC Car ready. Waiting for connection...")

# Main control loop
while True:
    if connected:
        # Control motors
        try:
            # Drive motor (B)
            hub.port.B.motor.run(drive_power)
            
            # Steering motor (A)
            hub.port.A.motor.run(steer_power)
        except:
            print("Motor control error")
    
    # Small delay
    time.sleep(0.05)