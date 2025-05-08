# REPL-friendly Pybricks RC car code
# For use with Pybricks firmware
# Copy and paste this code directly into the Pybricks REPL

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

print("SPIKE Prime RC Car initialized")
print("Motors connected to Ports A (steering) and B (drive)")
print("Ready to receive drive_motor.dc() and steering_motor.dc() commands")
print("Light will show GREEN when ready, BLUE when running, RED on error")

# Show ready message
hub.display.text("Ready")

# These functions will be called directly from REPL
def stop_motors():
    """Stop both motors safely"""
    drive_motor.stop()
    steering_motor.stop()
    hub.light.on(Color.RED)
    hub.display.text("STOP")
    print("Motors stopped")
    wait(1000)
    hub.light.on(Color.GREEN)
    hub.display.text("Ready")

def set_motors(drive, steer):
    """Set both motors to specified power"""
    drive_motor.dc(drive)
    steering_motor.dc(steer)
    hub.light.on(Color.BLUE)
    hub.display.text(f"D:{drive}")
    wait(500)
    hub.display.text(f"S:{steer}")
    wait(500)
    hub.display.text("Run")
    print(f"Motors set: Drive={drive}, Steer={steer}")

# You can now control via REPL with:
# drive_motor.dc(power)  # -100 to 100
# steering_motor.dc(power)  # -100 to 100
# stop_motors()  # Emergency stop
# set_motors(drive, steer)  # Set both motors at once