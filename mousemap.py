#!/usr/bin/env python3
import asyncio
from evdev import InputDevice, ecodes, UInput, list_devices

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

key_action_map = {
    ecodes.KEY_J: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_LEFT},
    ecodes.KEY_K: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_MIDDLE},
    ecodes.KEY_L: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_RIGHT},
    ecodes.KEY_I: {"is_map_active": False, "type": "scroll", "value": -1},  # scroll down
    ecodes.KEY_O: {"is_map_active": False, "type": "scroll", "value": 1},   # scroll up
}

scroll_tasks = {}

async def scroll_interval(key_code, value):
    await asyncio.sleep(0.5)  # Initial delay
    while key_action_map[key_code]["is_map_active"]:
        ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, value)
        ui.syn()
        await asyncio.sleep(0.05)

def addScrollTask(event, action):
    if event.code in scroll_tasks:
        return
    scroll_tasks[event.code] = asyncio.create_task(
        scroll_interval(event.code, action["value"])
    )

def removeScrollTask(event):
    if event.code not in scroll_tasks:
        return
    scroll_tasks[event.code].cancel()
    del scroll_tasks[event.code]


def find_device_path_evdev(name_hint):
    for path in list_devices():
        dev = InputDevice(path)
        if name_hint.lower() in dev.name.lower():
            return path
    return None


async def touchpad_monitor():
    global finger_down
    dev = InputDevice(TOUCHPAD)
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            finger_down = event.value == 1

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
                elif action["type"] == "scroll":
                    if isKeyDown:
                        ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                        addScrollTask(event, action)
                    else:
                        removeScrollTask(event)
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
