from inputs import get_gamepad
import math
import threading
import time

class PS5Controller(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        # Initialize state variables
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.Triangle = 0  # Y equivalent
        self.Circle = 0    # B equivalent
        self.Cross = 0     # A equivalent
        self.Square = 0    # X equivalent
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Share = 0     # Back equivalent
        self.Options = 0   # Start equivalent
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0
        self.PS5Button = 0

        # Set up event monitoring
        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self): 
        # Map PS5 controls to the expected format
        x = self.LeftJoystickX
        y = -self.LeftJoystickY  # Invert Y axis to match expected behavior (up is positive)
        x2 = self.RightJoystickX
        y2 = -self.RightJoystickY  # Invert Y axis
        a = self.Cross           # A = Cross
        b = self.Square          # B = Square (for X button compatibility)
        rb = self.RightBumper
        
        # Return all values for debugging
        return [x, y, x2, y2, a, b, rb]

    def _handle_dpad(self, hat_x, hat_y):
        """Process D-Pad values from hat inputs"""
        # D-pad on PS5 is often reported as an "ABS_HAT0X" and "ABS_HAT0Y" event
        if hat_x == -1:
            self.LeftDPad = 1
            self.RightDPad = 0
        elif hat_x == 1:
            self.LeftDPad = 0
            self.RightDPad = 1
        else:
            self.LeftDPad = 0
            self.RightDPad = 0
            
        if hat_y == -1:
            self.UpDPad = 1
            self.DownDPad = 0
        elif hat_y == 1:
            self.UpDPad = 0
            self.DownDPad = 1
        else:
            self.UpDPad = 0
            self.DownDPad = 0

    def _monitor_controller(self):
        # Dictionary for debug purposes - helps identify which events have been caught
        button_states = {}
        
        while True:
            try:
                events = get_gamepad()
                for event in events:
                    # Store all events for debugging
                    button_states[event.code] = event.state
                    
                    # PS5 mappings - these may need adjustment based on debugging
                    # Left and right analog sticks
                    if event.code == 'ABS_X':
                        self.LeftJoystickX = event.state / self.MAX_JOY_VAL
                    elif event.code == 'ABS_Y':
                        self.LeftJoystickY = event.state / self.MAX_JOY_VAL
                    elif event.code == 'ABS_RX':
                        self.RightJoystickX = event.state / self.MAX_JOY_VAL
                    elif event.code == 'ABS_RY':
                        self.RightJoystickY = event.state / self.MAX_JOY_VAL
                    
                    # Triggers - PS5 often uses ABS_Z and ABS_RZ
                    elif event.code == 'ABS_Z':
                        self.LeftTrigger = event.state / self.MAX_TRIG_VAL
                    elif event.code == 'ABS_RZ':
                        self.RightTrigger = event.state / self.MAX_TRIG_VAL
                    
                    # Main buttons
                    elif event.code == 'BTN_SOUTH' or event.code == 'BTN_CROSS':
                        self.Cross = event.state
                    elif event.code == 'BTN_EAST' or event.code == 'BTN_CIRCLE':
                        self.Circle = event.state
                    elif event.code == 'BTN_NORTH' or event.code == 'BTN_TRIANGLE':
                        self.Triangle = event.state
                    elif event.code == 'BTN_WEST' or event.code == 'BTN_SQUARE':
                        self.Square = event.state
                    
                    # Shoulder buttons
                    elif event.code == 'BTN_TL':
                        self.LeftBumper = event.state
                    elif event.code == 'BTN_TR':
                        self.RightBumper = event.state
                    
                    # Thumbstick buttons
                    elif event.code == 'BTN_THUMBL':
                        self.LeftThumb = event.state
                    elif event.code == 'BTN_THUMBR':
                        self.RightThumb = event.state
                    
                    # Menu buttons
                    elif event.code == 'BTN_SELECT' or event.code == 'BTN_SHARE':
                        self.Share = event.state
                    elif event.code == 'BTN_START' or event.code == 'BTN_OPTIONS':
                        self.Options = event.state
                    elif event.code == 'BTN_MODE' or event.code == 'BTN_PLAYSTATION':
                        self.PS5Button = event.state
                    
                    # D-Pad handling - PS5 often uses HAT0X and HAT0Y
                    elif event.code == 'ABS_HAT0X':
                        self._handle_dpad(event.state, button_states.get('ABS_HAT0Y', 0))
                    elif event.code == 'ABS_HAT0Y':
                        self._handle_dpad(button_states.get('ABS_HAT0X', 0), event.state)
                    
                    # Additional handling for buttons that might have different codes
                    elif event.code.startswith('BTN_TRIGGER_HAPPY1'):
                        self.LeftDPad = event.state
                    elif event.code.startswith('BTN_TRIGGER_HAPPY2'):
                        self.RightDPad = event.state
                    elif event.code.startswith('BTN_TRIGGER_HAPPY3'):
                        self.UpDPad = event.state
                    elif event.code.startswith('BTN_TRIGGER_HAPPY4'):
                        self.DownDPad = event.state
            except Exception as e:
                # Print any errors but continue execution
                print(f"Controller error: {e}")
                time.sleep(0.1)


# For backward compatibility, keep XboxController
class XboxController(PS5Controller):
    """For backward compatibility - maps PS5Controller to XboxController interface"""
    def __init__(self):
        super().__init__()
        # Add Xbox-specific property mappings
        self.A = 0
        self.B = 0
        self.X = 0
        self.Y = 0
        self.Back = 0
        self.Start = 0
    
    def read(self):
        # Keep original read behavior
        x = self.LeftJoystickX
        y = -self.LeftJoystickY
        x2 = self.RightJoystickX
        y2 = -self.RightJoystickY
        
        # Map PS5 buttons to Xbox buttons
        self.A = self.Cross
        self.B = self.Circle
        self.X = self.Square
        self.Y = self.Triangle
        self.Back = self.Share
        self.Start = self.Options
        
        a = self.A
        b = self.X  # Original mapping had b=X
        rb = self.RightBumper
        
        return [x, y, x2, y2, a, b, rb]


if __name__ == '__main__':
    print("PS5/Xbox Controller Test - Press Ctrl+C to exit")
    print("Moving sticks and buttons will display values")
    joy = PS5Controller()
    try:
        while True:
            values = joy.read()
            # Format output nicely
            print(f"Left: ({values[0]:.2f}, {values[1]:.2f}) Right: ({values[2]:.2f}, {values[3]:.2f}) Buttons: A:{values[4]} X:{values[5]} RB:{values[6]}", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")