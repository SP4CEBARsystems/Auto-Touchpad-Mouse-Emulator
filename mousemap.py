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
MOUSE = find_device_path_evdev('SteelSeries SteelSeries Rival 3')
if MOUSE is not None:
    print("Mouse detected: This macro is now obsolete, exiting.")
    exit(0)

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
key_action_map = {
    ecodes.KEY_J: {"type": "mouse", "button": ecodes.BTN_LEFT},
    ecodes.KEY_K: {"type": "mouse", "button": ecodes.BTN_MIDDLE},
    ecodes.KEY_L: {"type": "mouse", "button": ecodes.BTN_RIGHT},
    ecodes.KEY_I: {"type": "scroll", "value": -1},  # scroll down
    ecodes.KEY_O: {"type": "scroll", "value": 1},   # scroll up
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
            if finger_down and event.code in key_action_map:
                print("press", event.value, event.code)
                action = key_action_map[event.code]
                if action["type"] == "mouse":
                    release_press_key(event, action["button"])
                elif action["type"] == "scroll" and event.value == 1:
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                ui.syn()
                continue  # Do not forward J/K/L/I/O key events
            elif not finger_down and event.code in pressed_keys:
                pressed_keys[event.code] = event.value == 1
        # Forward all other keys
        uiKey.write_event(event)
        uiKey.syn()

def release_press_key(event, button):
    ui.write(ecodes.EV_KEY, button, event.value)
    pressed_mouse[button] = event.value == 1

def press_key(event, button):
    ui.write(ecodes.EV_KEY, button, event.value)

async def main():
    await asyncio.gather(
        touchpad_monitor(),
        keyboard_monitor()
    )

if __name__ == "__main__":
    asyncio.run(main())
