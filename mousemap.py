#!/usr/bin/env python3
import asyncio
from evdev import InputDevice, categorize, ecodes, UInput, AbsInfo, list_devices
# from evdev import keys

def find_device_path_evdev(name_hint):
    for path in list_devices():
        dev = InputDevice(path)
        if name_hint.lower() in dev.name.lower():
            return path
    return None

TOUCHPAD = find_device_path_evdev('touchpad') or "/dev/input/event6"
KEYBOARD = find_device_path_evdev('Asus Keyboard') or "/dev/input/event7"

# Virtual device to emit events
uiKey = UInput()
ui = UInput({
    ecodes.EV_KEY: [
        ecodes.BTN_LEFT,
        ecodes.BTN_MIDDLE,
        ecodes.BTN_RIGHT
    ],
    ecodes.EV_REL: [
        ecodes.REL_X,
        ecodes.REL_Y,
        ecodes.REL_WHEEL
    ]
})

finger_down = False
keyDev = InputDevice(KEYBOARD)

async def touchpad_monitor():
    global finger_down
    global keyDev
    dev = InputDevice(TOUCHPAD)
    grabbed = False
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            finger_down = event.value == 1
            if finger_down and not grabbed:
                keyDev.grab()
                grabbed = True
            elif not finger_down and grabbed:
                keyDev.ungrab()
                grabbed = False

async def keyboard_monitor():
    global finger_down
    global keyDev
    async for event in keyDev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.value in (1, 0):  # press/release
            if finger_down and event.code in (ecodes.KEY_J, ecodes.KEY_K, ecodes.KEY_L, ecodes.KEY_I, ecodes.KEY_O):
                # Block J/K/L and map to mouse buttons
                if event.code == ecodes.KEY_J:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                elif event.code == ecodes.KEY_K:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_MIDDLE, event.value)
                elif event.code == ecodes.KEY_L:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, event.value)
                elif event.code == ecodes.KEY_I and event.value == 1:  # scroll down on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, -1)
                elif event.code == ecodes.KEY_O and event.value == 1:  # scroll up on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, 1)
                ui.syn()
                continue  # Do not forward J/K/L/I/O key events
            elif finger_down:
                # Forward all other keys
                uiKey.write_event(event)
                uiKey.syn()

async def main():
    await asyncio.gather(
        touchpad_monitor(),
        keyboard_monitor()
    )

if __name__ == "__main__":
    asyncio.run(main())
