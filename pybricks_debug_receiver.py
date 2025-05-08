# Debug version of UART Receiver for Pybricks SPIKE Prime
# This script adds verbose debugging to help troubleshoot connection issues
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

# Variables for debug
command_count = 0
last_command = ""

# Show ready message
hub.display.text("DEBUG")
wait(1000)
hub.display.text("Ready")
print("\n" * 5)  # Clear some space in the console
print("===== SPIKE Prime Debug Receiver =====")
print("Motor B: Drive")
print("Motor A: Steering")
print("Commands: rc(drive,steer), stop(), test")
print("=======================================")
print("READY - Waiting for commands...")

# Function to stop motors safely
def stop():
    drive_motor.stop()
    steering_motor.stop()
    hub.light.on(Color.RED)
    hub.display.text("STOP")
    print("Motors stopped")
    wait(500)
    hub.light.on(Color.GREEN)
    hub.display.text("Ready")
    return "OK: Motors stopped"

# Function to control motors
def rc(drive, steer):
    global command_count, last_command
    
    # Increment command counter
    command_count += 1
    
    # Save last command for debugging
    last_command = f"rc({drive},{steer})"
    
    # Debug output
    print(f"Command #{command_count}: {last_command}")
    
    # Clamp values to safe range
    drive = max(-100, min(100, drive))
    steer = max(-100, min(100, steer))
    
    # Apply to motors
    drive_motor.dc(drive)
    steering_motor.dc(steer)
    
    # Show status
    hub.light.on(Color.BLUE)
    hub.display.text("Run")
    
    return f"OK: D:{drive} S:{steer}"

# Test function to verify connection
def test():
    global command_count
    
    # Increment command counter
    command_count += 1
    
    # Flash lights to show we received the command
    hub.light.on(Color.YELLOW)
    wait(200)
    hub.light.on(Color.GREEN)
    wait(200)
    hub.light.on(Color.BLUE)
    wait(200)
    hub.light.on(Color.GREEN)
    
    # Show test message
    hub.display.text("Test")
    wait(1000)
    hub.display.text("Ready")
    
    print(f"Test #{command_count} successful!")
    return "OK: Test successful"

# Main loop
counter = 0
print("READY - Waiting for commands...")  # Signal that we're ready

while True:
    # Check hub buttons for emergency stop
    if hub.buttons.pressed():
        print("Emergency stop triggered by button")
        print(f"Last command: {last_command}")
        print(f"Total commands received: {command_count}")
        stop()
    
    # Update counter and show status occasionally
    counter += 1
    if counter % 50 == 0:  # Every ~1 second
        # Get motor statuses
        try:
            drive_status = drive_motor.dc()
            steer_status = steering_motor.dc()
            
            if drive_status != 0 or steer_status != 0:
                print(f"Running: D:{drive_status} S:{steer_status}")
            else:
                # Only print this occasionally to avoid spamming
                if counter % 250 == 0:
                    print("Idle - Waiting for commands...")
                    print(f"Total commands received: {command_count}")
        except Exception as e:
            print(f"Error reading motor status: {e}")
    
    # Small delay
    wait(20)