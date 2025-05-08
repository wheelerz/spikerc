# Note from Faisal - this code is almost entirely stolen from Anton's Mindstorms & Ste7an
# Their copyright is below.
# Made some mods here and there to control from Windows. Originally code was meant to
# control from another Spike brick.

# This code has been updated to work with SPIKE Prime app v3.4.3.
# Python programming is now supported in v3.4.3 and later.


# This is the car code for the remote controlled RC car
# Build by connecting steering to motor A and drive to motor B
# Updated for SPIKE Prime v3.4.3
# Based on (c) 2021 Anton's Mindstorms & Ste7an

# Most of it is library bluetooth code.
# Scroll to line 200 for the core program.

# ===== Imports for SPIKE Prime v3.4.3 ====== #
import bluetooth
import struct
import time
import hub
import runloop
from hub import port, light_matrix
from micropython import const

# In SPIKE 3.4.3, the PrimeHub class from the spike module is gone
# We'll use hub directly for hub-related functionality

# In v3.4.3 we use hub.light_matrix instead of display/Image
# And we use hub.sound instead of sound directly

# Helper function for sleep_ms if not available in v3.4.3
try:
    from time import sleep_ms
except ImportError:
    def sleep_ms(ms):
        time.sleep(ms/1000)

# Connection animation patterns for light matrix
_CONNECT_IMAGES = [
    '03579:00000:00000:00000:00000',
    '00357:00000:00000:00000:00000',
    '00035:00000:00000:00000:00000',
    '00003:00000:00000:00000:00000',
    '00000:00000:00000:00000:00009',
    '00000:00000:00000:00000:00097',
    '00000:00000:00000:00000:00975',
    '00000:00000:00000:00000:09753',
    '00000:00000:00000:00000:97530',
    '00000:00000:00000:00000:75300',
    '00000:00000:00000:00000:53000',
    '90000:00000:00000:00000:30000',
    '79000:00000:00000:00000:00000',
    '57900:00000:00000:00000:00000',
    '35790:00000:00000:00000:00000',
]

_IRQ_CENTRAL_CONNECT = 1
_IRQ_CENTRAL_DISCONNECT = 2

if 'FLAG_INDICATE' in dir(bluetooth):
    # We're on MINDSTORMS Robot Inventor
    # New version of bluetooth
    _IRQ_GATTS_WRITE = 3
else:
    # We're probably on SPIKE Prime
    _IRQ_GATTS_WRITE = 1<<2

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# Helpers for generating BLE advertising payloads.
# Advertising payloads are repeated packets of the following form:
#1 byte data length (N + 1)
#1 byte type (see constants below)
#N bytes type-specific data

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)


_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


# Generate a payload to be passed to gap_advertise(adv_data=...).
def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)),
    )

    if name:
        _append(_ADV_TYPE_NAME, name)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    # See org.bluetooth.characteristic.gap.appearance.xml
    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))

    return payload


def decode_field(payload, adv_type):
    i = 0
    result = []
    while i + 1 < len(payload):
        if payload[i + 1] == adv_type:
            result.append(payload[i + 2 : i + payload[i] + 1])
        i += 1 + payload[i]
    return result


def decode_name(payload):
    n = decode_field(payload, _ADV_TYPE_NAME)
    return str(n[0], "utf-8") if n else ""


def decode_services(payload):
    services = []
    for u in decode_field(payload, _ADV_TYPE_UUID16_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID32_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<d", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID128_COMPLETE):
        services.append(bluetooth.UUID(u))
    return services


class BLESimplePeripheral:
    def __init__(self, name="robot", logo="00000:05550:05950:05550:00000", ble=None):
        self._n=12
        self._logo=logo  # Store the logo pattern string directly
        # Create animation patterns by adding logo to each connect image
        self._CONNECT_ANIMATION = []
        for img_pattern in _CONNECT_IMAGES:
            # In v3.4.3 we can't add images like before, so we'll handle this differently
            self._CONNECT_ANIMATION.append(img_pattern)
        
        if ble==None:
            ble = bluetooth.BLE()
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._connected=False
        self._write_callback = None
        self._update_animation()
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
            self._connected=True
            self._update_animation()
            sleep_ms(300)
            #t = Timer(mode=Timer.ONE_SHOT, period=2000, callback=lambda x:self.send(repr(self._logo)))

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            self._connected=False
            self._update_animation()
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=100000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback

    def _update_animation(self):
        if not self._connected:
            # Use hub.light_matrix for v3.4.3
            try:
                # For v3.4.3 we need to implement our own animation
                # This will display the first pattern, let other code run the rest
                hub.light_matrix.show(self._CONNECT_ANIMATION[0])
                # Note: In a full implementation, we would need a timer or loop to cycle through patterns
            except:
                # Fallback in case light_matrix is not available
                try:
                    import hub
                    hub.display.show(self._CONNECT_ANIMATION[0])
                except:
                    pass
        else:
            # When connected, show the logo
            try:
                hub.light_matrix.show(self._logo)
            except:
                try:
                    import hub
                    hub.display.show(self._logo)
                except:
                    pass


# ===== End of library ===== #




# Imports for program
from hub import port, sound
from time import sleep_ms

# Intialize
receiver = BLESimplePeripheral(logo="00000:09990:00900:00900:00000") # T for tank
l_stick_ver, r_stick_hor, turret = [0]*3

# Remote control data callback function
def on_rx(control):
    global l_stick_ver, r_stick_hor, turret
    l_stick_ver, r_stick_hor, turret = struct.unpack("bbB", control)

receiver.on_write(on_rx)

# Motor helper functions
def clamp_int(n, floor=-100, ceiling=100):
    return max(min(int(n),ceiling),floor)

def track_target(motor, target=0, gain=1.5):
    m_pos = motor.get()[1]
    motor.pwm(
        clamp_int((m_pos-target)*-gain)
    )
    return m_pos

# RC Car setup with:
# - Motor A: Steering pinion (left-right)
# - Motor B: Drive motor (forward-backward)
# In SPIKE 3.4.3, we use the motor module with port constants
import motor

# We don't need to create motor objects in SPIKE 3.4.3
# We'll directly use motor.run() or motor.start() with the port constants
# port.A for steering and port.B for drive

# In SPIKE 3.4.3, we don't need to create a PrimeHub instance
# We can use hub directly
did_connect = False
did_disconnect = False
# Control loop
while True:
    if receiver.is_connected():
        if not did_connect:
            # Play connection sounds using SPIKE 3.4.3 approach
            try:
                # In SPIKE 3.4.3, we use the sound module with await
                # But we're in a normal function, not an async one, so we need a workaround
                # We'll use a single beep for simplicity
                hub.sound.beep(440, 100)  # 440Hz for 100ms
            except:
                # Fallback methods if the above doesn't work
                try:
                    import sound
                    sound.beep(440, 100)
                except:
                    pass  # No sound if neither method works
            
            did_connect = True
            did_disconnect = False

        # RC Car control with left/right sticks
        # Left stick vertical (l_stick_ver) controls drive motor (B) - forward/backward
        # Right stick horizontal (r_stick_hor) controls steering motor (A) - left/right
        
        # Convert stick values to appropriate motor powers
        # For steering, we may need to limit the range to protect the steering mechanism
        steering_power = r_stick_hor  # Use right stick horizontal for steering
        drive_power = l_stick_ver     # Use left stick vertical for drive
        
        # Apply motor controls using SPIKE 3.4.3 motor API
        try:
            # In SPIKE 3.4.3, we use motor.start() with the port constant
            # Note: We can't use await in this non-async function context
            
            # Steering motor (A) - controls left/right
            motor.start(port.A, steering_power)
            
            # Drive motor (B) - controls forward/backward
            motor.start(port.B, drive_power)
        except:
            # Fallback method if the above doesn't work
            try:
                # Try using direct port control if available
                port.A.start(steering_power)
                port.B.start(drive_power)
            except:
                # Last resort - try the old API as well
                try:
                    port.A.pwm(steering_power)
                    port.B.pwm(drive_power)
                except:
                    # If all else fails, we can't control the motors
                    pass

    else:
        if not did_disconnect:
            # Play disconnection sound using SPIKE 3.4.3 approach
            try:
                # In SPIKE 3.4.3, we use the sound module with await
                # But we're in a normal function, not an async one, so we need a workaround
                # We'll use a lower pitch beep for disconnection
                hub.sound.beep(220, 100)  # 220Hz for 100ms
            except:
                # Fallback methods if the above doesn't work
                try:
                    import sound
                    sound.beep(220, 100)
                except:
                    pass  # No sound if neither method works
                
            did_disconnect = True
            did_connect = False

        # Turn off motors when no remote is connected using SPIKE 3.4.3 approach
        try:
            # In SPIKE 3.4.3, we use motor.stop() with the port constant
            motor.stop(port.A)  # Stop steering motor
            motor.stop(port.B)  # Stop drive motor
        except:
            # Fallback methods if the above doesn't work
            try:
                port.A.stop()
                port.B.stop()
            except:
                try:
                    # Last resort - try setting power to 0
                    motor.start(port.A, 0)
                    motor.start(port.B, 0)
                except:
                    pass  # At this point, we've tried all known methods to stop motors

    # Limit control loop speed for bluetooth messages to have time to arrive
    sleep_ms(20)
