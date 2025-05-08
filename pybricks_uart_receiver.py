# UART Receiver for Pybricks SPIKE Prime
# Receives commands over BLE UART and controls motors
# Upload to SPIKE Prime with Pybricks firmware

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Color
from pybricks.tools import wait

# Initialize the hub
hub = PrimeHub()
hub.light.on(Color.GREEN)

# Initialize the motors
drive_motor = Motor(Port.B)
steering_motor = Motor(Port.A)

# Variables for motor control
drive_power = 0
steer_power = 0
last_command_time = 0
counter = 0

# Show ready message
hub.display.text("Ready")
print("SPIKE Prime RC Car ready")
print("Commands:")
print("- rc(drive,steer): Set motor powers (-100 to 100)")
print("- stop(): Stop all motors")
print("- exit(): Exit program")

# Function to stop motors safely
def stop():
    global drive_power, steer_power
    drive_motor.stop()
    steering_motor.stop()
    drive_power = 0
    steer_power = 0
    hub.light.on(Color.RED)
    hub.display.text("STOP")
    print("Motors stopped")
    wait(500)
    hub.light.on(Color.GREEN)
    hub.display.text("Ready")
    return "OK"

# Function to control motors
def rc(drive, steer):
    global drive_power, steer_power, last_command_time
    
    # Update motor powers
    drive_power = max(-100, min(100, drive))
    steer_power = max(-100, min(100, steer))
    
    # Apply to motors
    drive_motor.dc(drive_power)
    steering_motor.dc(steer_power)
    
    # Update status
    hub.light.on(Color.BLUE)
    hub.display.text("Run")
    
    # Reset command time
    last_command_time = counter
    
    return f"D:{drive_power} S:{steer_power}"

# Function to exit program
def exit():
    global running
    stop()
    hub.display.text("Bye!")
    print("Program exiting")
    running = False
    return "BYE"

# Main loop
running = True
print("ready")  # Signal to computer that we're ready

while running:
    # Check for timeout (no commands for ~3 seconds)
    if counter - last_command_time > 60:  # ~3 seconds at 20ms per loop
        if drive_power != 0 or steer_power != 0:
            print("Command timeout - stopping motors")
            stop()
    
    # Check hub buttons for emergency stop
    if hub.buttons.pressed():
        print("Emergency stop triggered by button")
        stop()
    
    # Update counter and display current values occasionally
    counter += 1
    if counter % 50 == 0:  # Every ~1 second
        if drive_power != 0 or steer_power != 0:
            print(f"Current: D:{drive_power} S:{steer_power}")
    
    # Small delay to prevent CPU overload
    wait(20)