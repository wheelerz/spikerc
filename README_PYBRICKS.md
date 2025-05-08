# RC Car Control with Pybricks

This guide explains how to use the SPIKE Prime as an RC car using Pybricks firmware instead of the official LEGO SPIKE app.

## What is Pybricks?

[Pybricks](https://pybricks.com/) is an alternative firmware for LEGO programmable bricks, including the SPIKE Prime. It offers:

- More advanced Python programming
- Better performance
- More direct hardware control
- Fewer limitations than the LEGO SPIKE environment

## Setup Instructions

### 1. Install Pybricks on your SPIKE Prime Hub

Follow the [official Pybricks installation guide](https://pybricks.com/install/):

1. Connect your SPIKE Prime Hub to your computer with a USB cable
2. Install the Pybricks firmware according to the instructions
3. This is non-destructive - you can always go back to the official LEGO firmware

### 2. Connect Motors

- Connect your steering motor to Port A
- Connect your drive motor to Port B

### 3. Upload the RC Code

1. Open the Pybricks IDE at https://code.pybricks.com/
2. Copy the contents of `pybricks_ble_robot.py` into the editor
3. Connect your SPIKE Prime Hub
4. Click "Download" to transfer the program to your hub
5. The program will start automatically

### 4. Controller Setup

The system uses Bluetooth Low Energy (BLE) broadcasting for communication between your computer and the SPIKE Prime hub.

1. Install the required Python packages on your computer:
   ```
   pip install pygame bleak asyncio
   ```

2. Connect your PS5 controller to your computer via Bluetooth:
   - Put your controller in pairing mode by holding the PS button and Share button until the light bar flashes
   - In your computer's Bluetooth settings, find and pair with the controller (usually appears as "Wireless Controller")

3. Run the controller script:
   ```
   python pybricks_controller.py
   ```

4. The script will scan for Pybricks hubs and connect automatically. If multiple hubs are found, you'll be prompted to select one.

5. Your PS5 controller should now control the SPIKE Prime:
   - Left stick vertical: Drive forward/backward
   - Right stick horizontal: Steering left/right
   - Right trigger: Speed boost (increases power from 30% to 100%)
   - Right bumper: Emergency stop

## How It Works

### BLE Broadcasting

Pybricks provides a built-in mechanism for wireless communication using Bluetooth Low Energy (BLE) broadcasting. This is a lightweight form of communication that doesn't require a full connection between devices.

In our implementation:
- The computer packs controller data into a standardized format
- It broadcasts this data on channel 1
- The SPIKE Prime hub listens on channel 1 for control commands
- When commands are received, they're applied to the motors

### Hub Feedback

The SPIKE Prime hub provides feedback about its connection status:
- Blue light: Waiting for connection
- Green light: Connected to controller
- Red light: Emergency stop or error

The hub's display also shows:
- "RC Ready": Waiting for connection
- "Connected": Successfully connected
- "D:[value]" and "S:[value]": Current drive and steering values
- "STOP": Emergency stop activated

## Troubleshooting

### Connection Issues

1. **Hub Not Found**: Make sure your SPIKE Prime hub is turned on and running the Pybricks firmware with our code
2. **Controller Not Detected**: Check your controller is connected to your computer via Bluetooth
3. **Bluetooth Issues**: On Linux, ensure you have proper permissions for Bluetooth:
   ```
   sudo setcap 'cap_net_raw,cap_net_admin+eip' `which python3`
   ```

### Motor Control Issues

1. **Motors Move in Wrong Direction**: Edit the motor initialization in `pybricks_ble_robot.py` to use the correct direction:
   ```python
   # Change to Direction.COUNTERCLOCKWISE if needed
   drive_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
   steering_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
   ```

2. **Motors Too Fast/Slow**: Adjust the power multiplier in the controller script

### Hub Emergency Stop

If something goes wrong, you can always press any button on the SPIKE Prime hub to trigger an emergency stop. This will immediately stop all motors.

## Advanced Features

- **Signal Strength**: You can check the signal strength of the BLE connection using `hub.ble.signal_strength(channel)`
- **Multiple Hubs**: You can control multiple hubs by using different broadcast channels
- **Custom Data**: You can extend the broadcast data format to include additional control information

## Returning to LEGO Firmware

If you want to go back to the official LEGO firmware, follow the instructions on the [Pybricks website](https://pybricks.com/install/reset).