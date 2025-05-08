# Simple Pybricks BLE monitor for debugging - Fixed version
# Displays the BLE activity on SPIKE Prime hub
# Compatible with Pybricks firmware

from pybricks.hubs import PrimeHub
from pybricks.parameters import Color
from pybricks.tools import wait

# Initialize the hub with BLE channel observation
# We'll monitor channel 1 by default
hub = PrimeHub(observe_channels=[1])
print("BLE Monitor active on channel 1")
print("Displays last data received on BLE channel")

# Use simple counter instead of StopWatch
last_data_time = 0
counter = 0
last_print_time = 0

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
        
        # Reset counters
        last_data_time = counter
    elif counter - last_data_time > 10:  # About 1 second (10 * 100ms)
        # No data for 1 second
        hub.light.on(Color.BLUE)
        hub.display.text("Waiting")
        
        # Only print the waiting message every few seconds
        if counter - last_print_time > 50:  # About 5 seconds
            print("Waiting for data on channel 1...")
            last_print_time = counter
    
    # Increment counter (each loop is about 100ms)
    counter += 1
    
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