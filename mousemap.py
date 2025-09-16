#!/usr/bin/env python3
import asyncio
from evdev import InputDevice, ecodes, UInput, list_devices

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
    # print("debug override")
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

keyDev = InputDevice(KEYBOARD)
keyDev.grab()

key_action_map = {
    ecodes.KEY_J: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_LEFT},
    ecodes.KEY_K: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_MIDDLE},
    ecodes.KEY_L: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_RIGHT},
    ecodes.KEY_I: {"is_map_active": False, "type": "scroll", "value": -1},  # scroll down
    ecodes.KEY_O: {"is_map_active": False, "type": "scroll", "value": 1},   # scroll up
}
finger_down = False
touch_width = 0  # Add this line

try:
    MT_WIDTH = ecodes.ABS_MT_WIDTH
except AttributeError:
    MT_WIDTH = getattr(ecodes, 'ABS_MT_PRESSURE', None)  # fallback

async def touchpad_monitor():
    global finger_down, touch_width
    dev = InputDevice(TOUCHPAD)
    async for event in dev.async_read_loop():
        if MT_WIDTH and event.type == ecodes.EV_ABS and event.code == MT_WIDTH:
            touch_width = event.value
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            finger_down = event.value == 1 and touch_width < 8

async def keyboard_monitor():
    global finger_down
    global keyDev
    async for event in keyDev.async_read_loop():
        isKeyEvent = event.type == ecodes.EV_KEY
        isPressedOrReleased = event.value in (1, 0)
        isToBeMapped = event.code in key_action_map
        isKeyDown = event.value == 1
        if isKeyEvent and isPressedOrReleased and isToBeMapped:
            if isKeyDown:
                key_action_map[event.code]["is_map_active"] = finger_down
            action = key_action_map[event.code]
            if action["is_map_active"]:
                if action["type"] == "mouse":
                    ui.write(ecodes.EV_KEY, action["button"], event.value)
                elif action["type"] == "scroll" and isKeyDown:
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                ui.syn()
                if finger_down:
                    key_action_map[event.code]["is_map_active"] = finger_down
                continue  # Do not forward J/K/L/I/O key events
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
