# Minimal Pybricks RC receiver code for LEGO SPIKE Prime
# For use with Pybricks firmware (https://pybricks.com/)

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop, Color
from pybricks.tools import wait
from pybricks.bluetooth import ble

# Initialize the hub
hub = PrimeHub()
hub.light.on(Color.BLUE)

# Set up the motors - direction can be changed if needed
drive_motor = Motor(Port.B)
steering_motor = Motor(Port.A)

print("RC Car ready!")
hub.display.text("Ready")

# Simple flags for tracking connection state
is_connected = False
was_connected = False

# Define BLE characteristics for UART service
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# Variables to store control values
drive_power = 0
steer_power = 0

def on_rx(data):
    """Callback for received data"""
    global drive_power, steer_power
    
    # Expecting 3 bytes: drive, steer, unused
    if len(data) == 3:
        drive_power = data[0]  # -100 to 100
        steer_power = data[1]  # -100 to 100
        
        # Print debug info
        print("Drive:", drive_power, "Steer:", steer_power)

# Set up BLE UART service
uart = ble.Service(UART_SERVICE_UUID)
uart_rx = uart.characteristic(UART_RX_CHAR_UUID, ble.WRITE)
uart_tx = uart.characteristic(UART_TX_CHAR_UUID, ble.READ | ble.NOTIFY)

# Register callback for data reception
uart_rx.on_write(on_rx)

# Start BLE advertising as "SPIKE_RC"
ble.advertise("SPIKE_RC", [uart])

# Main control loop
while True:
    # Check if BLE connection status changed
    is_connected = bool(ble.connected())
    
    if is_connected and not was_connected:
        # Just connected
        hub.light.on(Color.GREEN)
        hub.display.text("Connected")
        hub.speaker.beep(440, 100)  # Connection beep
    
    elif not is_connected and was_connected:
        # Just disconnected
        hub.light.on(Color.BLUE)
        hub.display.text("Ready")
        hub.speaker.beep(220, 100)  # Disconnection beep
        
        # Stop motors on disconnect
        drive_motor.stop()
        steering_motor.stop()
        
        # Reset control values
        drive_power = 0
        steer_power = 0
    
    # Update the was_connected flag
    was_connected = is_connected
    
    # Apply motor control if connected
    if is_connected:
        try:
            # Set drive motor speed
            drive_motor.dc(drive_power)
            
            # Set steering motor speed
            steering_motor.dc(steer_power)
        except Exception as e:
            print("Motor error:", e)
            hub.light.on(Color.RED)  # Indicate error
    
    # Small delay to prevent high CPU usage
    wait(20)  # 20ms = ~50Hz update rate