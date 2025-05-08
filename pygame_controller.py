import pygame
import os
import sys
import math
import time
import threading
import struct

# Initialize pygame
pygame.init()

class PS5Controller:
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
        print(f"Number of hats: {self.controller.get_numhats()}")
        
        # Initialize state values
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0
        
        self.cross = 0  # A/Cross
        self.circle = 0  # B/Circle
        self.square = 0  # X/Square
        self.triangle = 0  # Y/Triangle
        
        self.left_bumper = 0
        self.right_bumper = 0
        
        self.dpad_up = 0
        self.dpad_down = 0
        self.dpad_left = 0
        self.dpad_right = 0
        
        # Thread for controller updates
        self.running = True
        self.thread = threading.Thread(target=self._controller_update)
        self.thread.daemon = True
        self.thread.start()
    
    def _controller_update(self):
        """Thread method that updates controller values"""
        while self.running:
            # Process events to get controller updates
            pygame.event.pump()
            
            if self.controller:
                # Map axes based on controller name
                # DualSense PS5 controller mappings may vary by platform
                
                # Common mapping for left stick
                self.left_stick_x = self.controller.get_axis(0)
                self.left_stick_y = self.controller.get_axis(1)
                
                # For PS5 DualSense on Windows, right stick is usually axes 2 and 3
                # For other controllers, it might be 3 and 4
                if "dualsense" in self.controller_name.lower() or "dual sense" in self.controller_name.lower():
                    self.right_stick_x = self.controller.get_axis(2)
                    self.right_stick_y = self.controller.get_axis(3)
                    
                    # PS5 triggers are usually axes 4 and 5 on Windows
                    if self.controller.get_numaxes() > 5:
                        self.left_trigger = (self.controller.get_axis(4) + 1) / 2.0  # Convert from -1..1 to 0..1
                        self.right_trigger = (self.controller.get_axis(5) + 1) / 2.0
                else:
                    # Generic mapping for other controllers
                    self.right_stick_x = self.controller.get_axis(3) if self.controller.get_numaxes() > 3 else 0
                    self.right_stick_y = self.controller.get_axis(4) if self.controller.get_numaxes() > 4 else 0
                    
                    # Triggers
                    if self.controller.get_numaxes() > 5:
                        self.left_trigger = (self.controller.get_axis(2) + 1) / 2.0
                        self.right_trigger = (self.controller.get_axis(5) + 1) / 2.0
                
                # Handle button mappings - these may need adjustment
                if self.controller.get_numbuttons() > 0:
                    # Common button mapping for PlayStation controllers
                    self.cross = self.controller.get_button(0)     # A/Cross
                    self.circle = self.controller.get_button(1)    # B/Circle
                    self.square = self.controller.get_button(2)    # X/Square
                    self.triangle = self.controller.get_button(3)  # Y/Triangle
                    
                    # Bumpers
                    if self.controller.get_numbuttons() > 5:
                        self.left_bumper = self.controller.get_button(4)
                        self.right_bumper = self.controller.get_button(5)
                
                # D-pad handling - can be buttons or hat
                if self.controller.get_numhats() > 0:
                    hat = self.controller.get_hat(0)
                    self.dpad_left = 1 if hat[0] == -1 else 0
                    self.dpad_right = 1 if hat[0] == 1 else 0
                    self.dpad_up = 1 if hat[1] == 1 else 0
                    self.dpad_down = 1 if hat[1] == -1 else 0
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
    
    def read(self):
        """Return current controller state"""
        # Invert Y axes so up is positive (like most games expect)
        y = -self.left_stick_y
        x = self.left_stick_x
        rx = self.right_stick_x
        ry = -self.right_stick_y
        
        # Buttons - using the standard order
        a = self.cross
        b = self.circle
        x = self.square
        y = self.triangle
        
        # Return the values
        return [x, y, rx, ry, a, b, self.right_bumper]
    
    def get_rc_controls(self):
        """Return control values formatted for RC car control"""
        # Invert Y axis so pushing up drives forward
        y = -self.left_stick_y  
        rx = self.right_stick_x
        rt = self.right_trigger
        rb = self.right_bumper
        
        return [y, rx, rt, rb]
    
    def close(self):
        """Clean up resources"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.controller:
            self.controller.quit()
        pygame.joystick.quit()


if __name__ == "__main__":
    print("PS5/DualSense Controller Test - Press Ctrl+C to exit")
    
    # Create controller
    controller = PS5Controller()
    
    if not controller.controller:
        print("No controller detected. Exiting...")
        pygame.quit()
        sys.exit()
    
    try:
        while True:
            # Get controller values
            values = controller.read()
            rc_values = controller.get_rc_controls()
            
            # Display values
            print("\033[H\033[J", end="")  # Clear screen
            print(f"Controller: {controller.controller_name}")
            print("\nStick Values:")
            print(f"  Left Stick:  X: {values[0]:>6.3f}  Y: {values[1]:>6.3f}")
            print(f"  Right Stick: X: {values[2]:>6.3f}  Y: {values[3]:>6.3f}")
            print("\nButton Values:")
            print(f"  Cross/A: {values[4]}  Circle/B: {controller.circle}  Square/X: {controller.square}  Triangle/Y: {controller.triangle}")
            print(f"  L1/LB: {controller.left_bumper}  R1/RB: {controller.right_bumper}")
            print(f"  L2/LT: {controller.left_trigger:.2f}  R2/RT: {controller.right_trigger:.2f}")
            print("\nD-Pad:")
            print(f"  Up: {controller.dpad_up}  Down: {controller.dpad_down}  Left: {controller.dpad_left}  Right: {controller.dpad_right}")
            
            print("\nRC Control Values:")
            print(f"  Drive: {rc_values[0]:.2f}  Steer: {rc_values[1]:.2f}  Boost: {rc_values[2]:.2f}  Stop: {rc_values[3]}")
            
            # Sleep to reduce update rate
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        controller.close()
        pygame.quit()