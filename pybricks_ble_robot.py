# Pybricks BLE RC receiver code for LEGO SPIKE Prime
# Uses Pybricks firmware (https://pybricks.com/)
# Communicates using Pybricks BLE API

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color
from pybricks.tools import wait, StopWatch

# Initialize the hub with BLE observation on channel 1
hub = PrimeHub(observe_channels=[1])

# Initialize the motors
drive_motor = Motor(Port.B)
steering_motor = Motor(Port.A)

# Create status display timer
status_timer = StopWatch()

# Set up variables for motor control
drive_power = 0
steer_power = 0
connected = False
last_receive_time = 0

# Function to stop motors safely
def stop_motors():
    drive_motor.dc(0)
    steering_motor.dc(0)
    drive_motor.stop()
    steering_motor.stop()

# Display startup message
hub.display.text("RC Ready")
hub.light.on(Color.BLUE)
print("SPIKE Prime RC Car Ready!")
print("Listening for controller on BLE channel 1")
print("Connect using pygame_uart_example.py with BlueZ BLE")

# Main control loop
while True:
    # Try to receive control data from BLE channel 1
    data = hub.ble.observe(1)
    
    if data is not None:
        # We received control data
        if not connected:
            # First connection - show status
            connected = True
            hub.light.on(Color.GREEN)
            hub.display.text("Connected")
            print("Controller connected!")
            hub.speaker.beep(frequency=440, duration=100)
        
        # Process the received data - should be a tuple of (drive_value, steering_value, _)
        if isinstance(data, tuple) and len(data) >= 2:
            drive_power = data[0]  # -100 to 100
            steer_power = data[1]  # -100 to 100
            
            # Apply motor controls
            try:
                drive_motor.dc(drive_power)
                steering_motor.dc(steer_power)
                
                # Update connection time
                last_receive_time = status_timer.time()
                
                # Print debug info but not too often
                if status_timer.time() % 500 < 50:  # Print approximately every 500ms
                    print(f"Drive: {drive_power}, Steer: {steer_power}")
            except Exception as e:
                print(f"Motor control error: {e}")
                hub.light.blink(Color.RED, [500, 500])
    
    # Check for connection timeout (no data for 2 seconds)
    elif connected and (status_timer.time() - last_receive_time) > 2000:
        connected = False
        hub.light.on(Color.BLUE)
        hub.display.text("Disconnected")
        print("Controller disconnected - timeout")
        hub.speaker.beep(frequency=220, duration=100)
        stop_motors()
    
    # Show status on display periodically
    if status_timer.time() > 5000:
        if connected:
            # Show current values
            hub.display.text(f"D:{drive_power}")
            wait(1000)
            hub.display.text(f"S:{steer_power}")
            wait(1000)
            hub.display.text("Connected")
        else:
            # Show waiting message
            hub.display.text("Waiting")
            wait(1000)
            hub.display.text("RC Ready")
            
        # Reset timer
        status_timer.reset()
    
    # Check hub buttons for emergency stop
    if hub.buttons.pressed():
        print("Emergency stop!")
        hub.light.on(Color.RED)
        hub.display.text("STOP")
        stop_motors()
        hub.speaker.beep(frequency=880, duration=300)
        wait(1000)
        hub.light.on(Color.BLUE if not connected else Color.GREEN)
        hub.display.text("RC Ready" if not connected else "Connected")
    
    # Small delay to save power
    wait(20)