# Ultra Simple Pybricks RC for SPIKE Prime
# Most basic implementation to ensure compatibility
# For Pybricks firmware

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Color
from pybricks.tools import wait

# Initialize the hub - no BLE options to avoid errors
hub = PrimeHub()

# Initialize the motors
drive_motor = Motor(Port.B)
steering_motor = Motor(Port.A)

# Set up controller variables
drive_power = 0
steer_power = 0

# Show ready message
hub.light.on(Color.GREEN)
hub.display.text("RC Ready")
print("RC Car ready. Press any button to exit.")

# Variables for button control
is_manual_mode = False
counter = 0

# Main control loop
while True:
    # Check if buttons are pressed to exit
    buttons = hub.buttons.pressed()
    if buttons:
        # If center button, exit program
        if buttons == [0]:  # Center button
            hub.light.on(Color.RED)
            hub.display.text("Exit")
            print("Exiting program...")
            break
        
        # Left button - decrease steering
        if 1 in buttons:  # Left button
            steer_power = max(-100, steer_power - 10)
            is_manual_mode = True
            
        # Right button - increase steering
        if 3 in buttons:  # Right button
            steer_power = min(100, steer_power + 10)
            is_manual_mode = True
            
        # Up button - increase forward speed
        if 4 in buttons:  # Up button
            drive_power = min(100, drive_power + 10)
            is_manual_mode = True
            
        # Down button - increase reverse speed
        if 2 in buttons:  # Down button
            drive_power = max(-100, drive_power - 10)
            is_manual_mode = True
        
        # Show current values
        hub.light.on(Color.YELLOW)
        hub.display.text(f"D:{drive_power}")
        wait(500)
        hub.display.text(f"S:{steer_power}")
        wait(500)
    
    # Apply motor controls
    try:
        drive_motor.dc(drive_power)
        steering_motor.dc(steer_power)
    except Exception as e:
        # Show error
        hub.light.on(Color.RED)
        hub.display.text("Error")
        print("Motor error:", e)
        wait(1000)
        hub.light.on(Color.GREEN)
    
    # Display status periodically
    if counter % 50 == 0:  # Every 5 seconds (50 * 100ms)
        if is_manual_mode:
            hub.display.text("Manual")
            hub.light.on(Color.YELLOW)
        else:
            hub.display.text("Ready")
            hub.light.on(Color.GREEN)
    
    # Increment counter
    counter += 1
    
    # Small delay
    wait(100)