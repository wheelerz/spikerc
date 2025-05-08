from inputs import get_gamepad
import time

def main():
    """Just print out controller event codes and states."""
    print("PS5 Controller Debug. Press Ctrl+C to exit.")
    print("Move sticks and press buttons to see their event codes.")
    print("----------------------------------------")
    
    try:
        while True:
            events = get_gamepad()
            for event in events:
                print(f"Event: {event.ev_type}, Code: {event.code}, State: {event.state}")
            time.sleep(0.01)  # Small sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()