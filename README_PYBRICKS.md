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
2. Copy the contents of `pybricks_robot_code.py` into the editor
3. Connect your SPIKE Prime Hub
4. Click "Download" to transfer the program to your hub
5. The program will start automatically

### 4. Connect and Control

1. Run the `pygame_uart_example.py` script on your computer
2. The script will scan for and connect to your SPIKE Prime
3. Your PS5 controller should now be able to control the SPIKE Prime:
   - Left stick vertical: Drive forward/backward
   - Right stick horizontal: Steering left/right
   - Right trigger: Speed boost
   - Right bumper: Emergency stop

## Troubleshooting

- **Connection Issues**: Make sure the SPIKE Prime is showing "Ready" on its display. If not, restart the hub.
- **Motor Direction Wrong**: If motors go in the wrong direction, you can modify the motor initialization in the code:
  ```python
  # Change Direction.CLOCKWISE to Direction.COUNTERCLOCKWISE as needed
  drive_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
  ```
- **Controller Not Detected**: Follow the instructions in README_PS5.md to set up your controller.

## Advantages of Pybricks

- More reliable Bluetooth connection
- No code size limitations
- Direct motor control with better precision
- Proper error handling
- Better battery life
- Ability to save programs permanently on the hub

## Returning to LEGO Firmware

If you want to go back to the official LEGO firmware, follow the instructions on the [Pybricks website](https://pybricks.com/install/reset).