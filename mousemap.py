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
keyDev.grab()

# Track pressed state for mapped keys
pressed_keys = {
    ecodes.KEY_J: False,
    ecodes.KEY_K: False,
    ecodes.KEY_L: False,
    ecodes.KEY_I: False,
    ecodes.KEY_O: False,
}
pressed_mouse = {
    ecodes.BTN_LEFT: False,
    ecodes.BTN_MIDDLE: False,
    ecodes.BTN_RIGHT: False,
}

async def touchpad_monitor():
    global finger_down
    dev = InputDevice(TOUCHPAD)
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            # If finger_down changed from True to False, release all mapped keys/buttons
            onPress = not finger_down and event.value == 1
            onRelease = finger_down and event.value != 1
            if onPress:
                # Release mapped keys
                for key, pressed in pressed_keys.items():
                    if pressed:
                        uiKey.write(ecodes.EV_KEY, key, 0)  # Release
                        uiKey.syn()
                        pressed_keys[key] = False
                        print("release", key)
                        # Only send keyup for J/K/L/I/O if finger_down was True (remapped)
            elif onRelease:
                # Release mouse buttons
                for btn, pressed in pressed_mouse.items():
                    if pressed:
                        ui.write(ecodes.EV_KEY, btn, 0)  # Release
                        ui.syn()
                        pressed_mouse[btn] = False
            finger_down = event.value == 1

async def keyboard_monitor():
    global finger_down
    global keyDev
    async for event in keyDev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.value in (1, 0):  # press/release
            if finger_down and event.code in (ecodes.KEY_J, ecodes.KEY_K, ecodes.KEY_L, ecodes.KEY_I, ecodes.KEY_O):
                print("press", event.value, event.code)
                # Block J/K/L and map to mouse buttons
                if event.code == ecodes.KEY_J:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                    pressed_mouse[ecodes.BTN_LEFT] = event.value == 1
                elif event.code == ecodes.KEY_K:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_MIDDLE, event.value)
                    pressed_mouse[ecodes.BTN_MIDDLE] = event.value == 1
                elif event.code == ecodes.KEY_L:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, event.value)
                    pressed_mouse[ecodes.BTN_RIGHT] = event.value == 1
                elif event.code == ecodes.KEY_I and event.value == 1:  # scroll down on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, -1)
                elif event.code == ecodes.KEY_O and event.value == 1:  # scroll up on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, 1)
                ui.syn()
                continue  # Do not forward J/K/L/I/O key events
            elif not finger_down and event.code in pressed_keys:
                pressed_keys[event.code] = event.value == 1
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
