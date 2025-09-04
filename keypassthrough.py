#!/usr/bin/env python3
from evdev import InputDevice, UInput, ecodes as e
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} /dev/input/eventX")
    sys.exit(1)

device_path = sys.argv[1]

# Open the real keyboard
real_kbd = InputDevice(device_path)

# Grab it so no events leak directly to the system
real_kbd.grab()

# Copy its capabilities (so UInput device looks the same)
caps = real_kbd.capabilities(absinfo=False)

# Create the virtual device
virt_kbd = UInput(
    # caps, name=f"Proxy for {real_kbd.name}"
)

print(f"Grabbing {device_path} ({real_kbd.name}) and forwarding all events...")

# Forward loop
for event in real_kbd.read_loop():
    virt_kbd.write_event(event)
    virt_kbd.syn()
