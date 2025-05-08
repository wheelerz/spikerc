# Simplified SPIKE Prime RC receiver code
# For use with SPIKE Prime v3.4.3 or later
# This version removes unnecessary code and simplifies the BLE implementation

import hub
import bluetooth
import struct
import time

# Light patterns for connection animation
_CONNECT_IMAGES = [
    '03579:00000:00000:00000:00000',
    '00357:00000:00000:00000:00000',
    '00035:00000:00000:00000:00000',
    '00003:00000:00000:00000:00000',
    '00000:00000:00000:00000:00009',
    '00000:00000:00000:00000:00097',
    '00000:00000:00000:00000:00975',
    '00000:00000:00000:00000:09753',
    '00000:00000:00000:00000:97530',
    '00000:00000:00000:00000:75300',
    '00000:00000:00000:00000:53000',
    '90000:00000:00000:00000:30000',
    '79000:00000:00000:00000:00000',
    '57900:00000:00000:00000:00000',
    '35790:00000:00000:00000:00000',
]

# Simple helper function for sleep_ms
def sleep_ms(ms):
    time.sleep(ms/1000)

# Basic BLE service setup for SPIKE Prime
ble = bluetooth.BLE()
name = "SPIKE_RC"
ble.active(True)
ble.config(gap_name=name)

# Set up BLE advertising
def advertise():
    payload = bytearray()
    # Add flags
    payload += b'\x02\x01\x06'
    # Add name
    name_bytes = name.encode()
    payload += bytes([len(name_bytes) + 1, 0x09]) + name_bytes
    # Set advertising data
    ble.gap_advertise(100, payload)
    print("Advertising as", name)

advertise()

# BLE UART service setup
_UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_TX = bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_RX = bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')

_UART_SERVICE = (
    _UART_UUID,
    (
        (_UART_TX, bluetooth.FLAG_NOTIFY),
        (_UART_RX, bluetooth.FLAG_WRITE),
    ),
)

# Register GATT services
services = (_UART_SERVICE,)
((tx_handle, rx_handle),) = ble.gatts_register_services(services)

# Connection state
connected = False
l_stick_ver, r_stick_hor = 0, 0

# BLE event handler
def ble_irq(event, data):
    global connected, l_stick_ver, r_stick_hor
    
    if event == 1: # Connect
        connected = True
        print("Connected")
        hub.light_matrix.show('00000:09990:09090:09990:00000')  # Show connected symbol
        hub.sound.beep(440, 100)  # Connection beep
        
    elif event == 2: # Disconnect
        connected = False
        print("Disconnected")
        hub.light_matrix.show('00000:00000:09990:00000:00000')  # Show disconnected symbol
        hub.sound.beep(220, 100)  # Disconnection beep
        # Stop motors when disconnected
        hub.port.A.motor.stop()
        hub.port.B.motor.stop()
        # Restart advertising
        advertise()
        
    elif event == 3: # Write
        # Get control data from message
        buffer = ble.gatts_read(rx_handle)
        if len(buffer) == 3:
            l_stick_ver, r_stick_hor, _ = struct.unpack("bbB", buffer)
            print("Drive:", l_stick_ver, "Steer:", r_stick_hor)

# Register IRQ handler
ble.irq(ble_irq)

# Show waiting for connection pattern
current_img = 0
last_update = time.time()

# Main control loop
print("RC Car ready. Waiting for Bluetooth connection...")

while True:
    # Animation while waiting for connection
    if not connected:
        # Update animation every 100ms
        now = time.time()
        if now - last_update > 0.1:
            hub.light_matrix.show(_CONNECT_IMAGES[current_img])
            current_img = (current_img + 1) % len(_CONNECT_IMAGES)
            last_update = now
    else:
        # When connected, control the motors
        # Motor A: Steering (left/right)
        # Motor B: Drive (forward/backward)
        
        # Apply motor controls with proper error handling
        try:
            # Steering motor (A)
            hub.port.A.motor.run(r_stick_hor)
            
            # Drive motor (B)
            hub.port.B.motor.run(l_stick_ver)
        except Exception as e:
            print("Motor error:", e)
    
    # Small delay to prevent high CPU usage
    sleep_ms(20)