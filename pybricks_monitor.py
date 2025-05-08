# Simple Pybricks BLE monitor for debugging
# Displays the BLE activity on SPIKE Prime hub
# Compatible with Pybricks firmware

from pybricks.hubs import PrimeHub
from pybricks.parameters import Color
from pybricks.tools import wait, StopWatch

# Initialize the hub with BLE channel observation
# We'll monitor channel 1 by default
hub = PrimeHub(observe_channels=[1])
print("BLE Monitor active on channel 1")
print("Displays last data received on BLE channel")

# Create a timer for display updates
timer = StopWatch()

# Main loop
while True:
    # Check for BLE broadcasts on channel 1
    data = hub.ble.observe(1)
    
    if data is not None:
        # We received data - show on display and console
        hub.light.on(Color.GREEN)
        print("Data received:", data)
        
        # Show data type and content on display
        hub.display.text(f"Data: {data}")
        
        # Reset the timer
        timer.reset()
    elif timer.time() > 1000:
        # No data for 1 second
        hub.light.on(Color.BLUE)
        hub.display.text("Waiting")
        
        # Only print the waiting message every few seconds
        if timer.time() > 5000:
            print("Waiting for data on channel 1...")
            timer.reset()
    
    # Check if a button was pressed to stop monitoring
    if hub.buttons.pressed():
        hub.light.on(Color.RED)
        hub.display.text("Exit?")
        wait(1000)
        
        # Check if still pressed to confirm exit
        if hub.buttons.pressed():
            hub.light.on(Color.ORANGE)
            hub.display.text("Bye!")
            print("Monitoring stopped by button press")
            break
        
        # If not still pressed, continue monitoring
        hub.light.on(Color.BLUE)
    
    # Small delay
    wait(100)