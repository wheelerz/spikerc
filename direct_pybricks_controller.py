# Direct Pybricks Controller - No threading
# Simplified version for directly connecting to SPIKE Prime
# Designed for maximum compatibility across platforms

import asyncio
import pygame
import sys
import time
import argparse

# Initialize pygame for controller input
pygame.init()

class SimpleController:
    def __init__(self):
        pygame.joystick.init()
        
        # Check if any joysticks/controllers are connected
        if pygame.joystick.get_count() == 0:
            print("No controllers found. Please connect a controller and try again.")
            self.controller = None
            return
            
        # Initialize the first joystick
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        
        # Print controller info
        self.controller_name = self.controller.get_name()
        print(f"Controller connected: {self.controller_name}")
        print(f"Number of axes: {self.controller.get_numaxes()}")
        print(f"Number of buttons: {self.controller.get_numbuttons()}")
    
    def read(self):
        """Read current controller state"""
        # Process pygame events
        pygame.event.pump()
        
        if not self.controller:
            return 0, 0, 0, 0
        
        # Read stick values
        left_y = -self.controller.get_axis(1)  # Invert Y so up is positive
        right_x = self.controller.get_axis(2) if "dualsense" in self.controller_name.lower() else self.controller.get_axis(3)
        
        # Read trigger and bumper
        right_trigger = (self.controller.get_axis(5) + 1) / 2.0 if self.controller.get_numaxes() > 5 else 0  # 0 to 1
        right_bumper = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else 0
        
        return left_y, right_x, right_trigger, right_bumper
    
    def close(self):
        """Clean up pygame resources"""
        pygame.joystick.quit()
        pygame.quit()

async def main():
    # Create print function for the REPL
    def print_pybricks_command(drive_value, steer_value):
        """Print command in format for Pybricks REPL"""
        # Scale values to the -100 to 100 range
        drive_power = max(-100, min(100, int(drive_value * 100)))
        steer_power = max(-100, min(100, int(steer_value * 100)))
        
        # Format command to be directly pasted into REPL
        print(f"\rCommands: drive_motor.dc({drive_power}); steering_motor.dc({steer_power})       ", end="")
    
    # Create controller
    controller = SimpleController()
    if not controller.controller:
        print("No controller connected. Exiting...")
        sys.exit(1)
    
    print("\n=== Direct Pybricks Controller ===")
    print("This controller outputs commands to be directly copy-pasted into the Pybricks REPL")
    print("Connect to your SPIKE Prime's REPL and paste these commands:")
    print("\nFirst, copy-paste this to set up the motors:")
    print("from pybricks.pupdevices import Motor")
    print("from pybricks.parameters import Port")
    print("drive_motor = Motor(Port.B)")
    print("steering_motor = Motor(Port.A)")
    print("\nThen paste the continuously updated commands below to control the motors.")
    print("Press right bumper (R1) or Ctrl+C to exit.")
    
    try:
        deadband = 0.1  # Ignore small stick movements
        
        while True:
            # Read controller values
            drive, steer, trigger, emergency_stop = controller.read()
            
            # Check for emergency stop
            if emergency_stop:
                print("\nEmergency stop - Exiting...")
                print("drive_motor.stop(); steering_motor.stop()")
                break
            
            # Apply deadband
            if abs(drive) < deadband:
                drive = 0
            if abs(steer) < deadband:
                steer = 0
            
            # Apply power scaling
            power_scale = 0.3 + (trigger * 0.7)  # Scale from 30% to 100% based on trigger
            final_drive = drive * power_scale
            final_steer = steer * 0.7  # Limit steering to 70% to protect mechanisms
            
            # Output REPL command
            print_pybricks_command(final_drive, final_steer)
            
            # Small delay
            await asyncio.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nUser interrupted - Exiting...")
        print("drive_motor.stop(); steering_motor.stop()")
    finally:
        # Clean up
        controller.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()
        sys.exit(1)