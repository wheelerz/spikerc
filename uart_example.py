import asyncio
import sys
import struct
from threading import Thread
from inputs import get_gamepad
import math

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# This code has been updated to work with SPIKE Prime v3.4.3

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# Improved device discovery for SPIKE Prime v3.4.3
async def uart_terminal():
    print("Scanning for SPIKE Prime devices...")
    
    # First try to find by specific address if you know it
    # Replace with your SPIKE Prime's MAC address if known
    spike_address = "E0:FF:F1:4F:05:C8"
    
    try:
        device = await BleakScanner.find_device_by_address(spike_address)
        if device:
            print(f"Found SPIKE Prime device at address: {spike_address}")
        else:
            # If specific address not found, try to find by service UUID
            print(f"Device with address {spike_address} not found. Scanning for any SPIKE Prime...")
            devices = await BleakScanner.discover()
            for d in devices:
                print(f"Found device: {d.name} ({d.address})")
                # If you know your SPIKE Prime shows up with a specific name, you can filter by that
                if d.name and ("SPIKE" in d.name.upper() or "LEGO" in d.name.upper()):
                    device = d
                    print(f"Found SPIKE Prime device: {d.name} ({d.address})")
                    break
    except Exception as e:
        print(f"Error during device scanning: {e}")
        device = None

    if device is None:
        print("No SPIKE Prime device found. Please check that:")
        print("1. Your SPIKE Prime hub is powered on")
        print("2. Bluetooth is enabled on both devices")
        print("3. You've loaded the robot_python_code.py on the SPIKE Prime")
        print("4. If you know your SPIKE Prime's MAC address, edit it in this file")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print("received:", data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected...")

        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        joy = XboxController()
        deadband = 0.1

        # RC Car control logic
        # - Left stick vertical: Drive motor control (forward/backward)
        # - Right stick horizontal: Steering control (left/right)
        # - Right trigger: Speed multiplier
        # - Right bumper: Emergency stop
        print("RC Car control ready:")
        print("- Left stick vertical: Drive (forward/backward)")
        print("- Right stick horizontal: Steering (left/right)")
        print("- Right trigger: Speed boost")
        print("- Right bumper: Emergency stop/disconnect")
        
        while True:
            # Get controller inputs
            l_stick_ver, r_stick_hor, r_trigger, disconnect = joy.read()
            
            if disconnect:
                print("Emergency stop - Disconnecting...")
                for task in asyncio.all_tasks():
                    task.cancel()
                break
            else:
                # Apply deadband to remove jitter when sticks are near center
                if deadband >= l_stick_ver >= -deadband:
                    l_stick_ver = 0
                if deadband >= r_stick_hor >= -deadband:
                    r_stick_hor = 0
                
                # Set power multiplier based on right trigger
                # Base power is 30% when trigger is not pressed
                # Full trigger press gives 100% power
                if r_trigger < 0.1:  # Almost not pressed
                    power_multiplier = 30  # Base power 30%
                else:
                    # Scale from 30% to 100% based on trigger position
                    power_multiplier = 30 + (r_trigger * 70)

                # Calculate drive power from left stick vertical position
                drive_power = l_stick_ver * (power_multiplier / 100)
                
                # Calculate steering power from right stick horizontal
                # The steering motor usually needs less power, so we scale it to 70%
                # This prevents damaging the steering mechanism
                steering_power = r_stick_hor * 0.7
                
                # Scale values to SPIKE motor power range (-100 to 100)
                drive_motor_power = int(drive_power * 100)
                steering_motor_power = int(steering_power * 100)

                # Pack data to send to SPIKE Prime
                controller_state = struct.pack("bbB",
                                             drive_motor_power,    # Drive motor (B)
                                             steering_motor_power, # Steering motor (A)
                                             0)                    # Unused parameter

                await client.write_gatt_char(rx_char, controller_state)
                await asyncio.sleep(0.02)


# Stolen from https://stackoverflow.com/a/66867816/3105668
class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self):
        # For RC car control:
        # - Left stick vertical (y): Controls drive motor (forward/backward)
        # - Right stick horizontal (rx): Controls steering (left/right)
        # - Right trigger (z): Speed multiplier
        # - Right bumper (rb): Emergency stop/disconnect
        
        y = self.LeftJoystickY    # Drive control (forward/backward)
        rx = self.RightJoystickX  # Steering control (left/right)
        z = self.RightTrigger     # Speed multiplier
        rb = self.RightBumper     # Emergency stop
        
        return [y, rx, z, rb]

    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL  # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL  # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.Y = event.state  # previously switched with X
                elif event.code == 'BTN_WEST':
                    self.X = event.state  # previously switched with Y
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        pass
