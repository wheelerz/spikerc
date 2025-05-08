# PS5 Controller Support for SPIKE RC

This document provides instructions for getting your PS5 DualSense controller working with the SPIKE Prime RC system.

## Controller Detection Issue

If you're seeing the error `inputs.UnpluggedError("No gamepad found.")` even though your PS5 DualSense controller is connected via Bluetooth, the issue is with the `inputs` library not recognizing the PS5 controller properly.

## Solution: Using Pygame

We've created alternative versions of the control scripts that use the `pygame` library instead, which has better support for PS5 DualSense controllers.

## Setup Instructions

1. Install the required packages:

```bash
pip install pygame bleak asyncio
```

2. Connect your PS5 DualSense controller to your PC via Bluetooth:
   - Put your controller in pairing mode by holding the PS button and Share button until the light bar flashes
   - In Windows, go to Settings → Bluetooth & devices → Add device
   - Select your controller (usually appears as "Wireless Controller")

3. Run the controller detection script to verify your controller is recognized:

```bash
python controller_detect.py
```

4. Test the controller with the pygame_controller.py script:

```bash
python pygame_controller.py
```

5. Connect to your SPIKE Prime and control it:

```bash
python pygame_uart_example.py
```

## Troubleshooting

If you're still having issues with controller detection:

1. Make sure your controller is charged and properly paired with your PC.
2. Try reconnecting the controller by turning it off and on.
3. Check Windows Bluetooth settings to verify the controller is connected.
4. Look for the controller in Device Manager and check for any warning symbols.
5. Try updating the controller firmware using Sony's official tools.

## Control Mappings

For the RC car:
- Left stick vertical (up/down): Controls drive motor (forward/backward)
- Right stick horizontal (left/right): Controls steering
- Right trigger (R2): Speed boost (increases power from 30% to 100%)
- Right bumper (R1): Emergency stop/disconnect

## Files

- `controller_detect.py` - Helps identify which controller libraries are available and detects connected controllers
- `pygame_controller.py` - Test script for your PS5 controller using pygame
- `pygame_uart_example.py` - Main script to control your SPIKE Prime with a PS5 controller using pygame

## Notes

- The PS5 DualSense controller's LED color will not change when connected to PC via Bluetooth
- If the controller disconnects frequently, try using a USB cable instead
- The original `gamepad.py` and `uart_example.py` files have been updated but may still not work with PS5 controllers