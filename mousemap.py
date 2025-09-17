#!/usr/bin/env python3
import asyncio
import signal
import sys
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
    sys.exit(0)

# Virtual device to emit events
uiKey = UInput()
uiMouse = UInput({
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

isMapActive = False
keyDevice = InputDevice(KEYBOARD)
keyDevice.grab()

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
        uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, value)
        uiMouse.syn()
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


async def touchpad_monitor():
    global isMapActive
    touchpadDevice = InputDevice(TOUCHPAD)
    async for event in touchpadDevice.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            isMapActive = event.value == 1

async def keyboard_monitor():
    global isMapActive
    global keyDevice
    async for event in keyDevice.async_read_loop():
        isKeyEvent = event.type == ecodes.EV_KEY
        isPressedOrReleased = event.value in (1, 0)
        isToBeMapped = event.code in key_action_map
        isKeyDown = event.value == 1
        if isKeyEvent and isPressedOrReleased and isToBeMapped:
            if isKeyDown:
                key_action_map[event.code]["is_map_active"] = isMapActive
            action = key_action_map[event.code]
            if action["is_map_active"]:
                if action["type"] == "mouse":
                    uiMouse.write(ecodes.EV_KEY, action["button"], event.value)
                    uiMouse.syn()
                elif action["type"] == "scroll":
                    if isKeyDown:
                        uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                        uiMouse.syn()
                        addScrollTask(event, action)
                    else:
                        removeScrollTask(event)
                continue  # Do not forward J/K/L/I/O key events
        # Forward all other keys
        uiKey.write_event(event)
        uiKey.syn()

def cleanup():
    try:
        keyDevice.ungrab()
    except Exception:
        pass

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    try:
        await asyncio.gather(
            touchpad_monitor(),
            keyboard_monitor()
        )
    finally:
        cleanup()

if __name__ == "__main__":
    asyncio.run(main())
