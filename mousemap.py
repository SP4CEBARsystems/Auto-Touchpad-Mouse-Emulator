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

class MouseMap:
    def __init__(self):
        # Virtual device to emit events
        self.uiKey = UInput()
        self.uiMouse = UInput({
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

        self.isMapActive = False
        self.keyDevice = InputDevice(KEYBOARD)
        self.keyDevice.grab()

        self.key_action_map = {
            ecodes.KEY_J: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_LEFT},
            ecodes.KEY_K: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_MIDDLE},
            ecodes.KEY_L: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_RIGHT},
            ecodes.KEY_I: {"is_map_active": False, "type": "scroll", "value": -1},  # scroll down
            ecodes.KEY_O: {"is_map_active": False, "type": "scroll", "value": 1},   # scroll up
        }

        self.scroll_task_manager = ScrollTaskManager()

    async def touchpad_monitor(self):
        touchpadDevice = InputDevice(TOUCHPAD)
        async for event in touchpadDevice.async_read_loop():
            if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                self.isMapActive = event.value == 1

    async def keyboard_monitor(self):
        async for event in self.keyDevice.async_read_loop():
            isKeyEvent = event.type == ecodes.EV_KEY
            isPressedOrReleased = event.value in (1, 0)
            isToBeMapped = event.code in self.key_action_map
            isKeyDown = event.value == 1
            if isKeyEvent and isPressedOrReleased and isToBeMapped:
                if isKeyDown:
                    self.key_action_map[event.code]["is_map_active"] = self.isMapActive
                action = self.key_action_map[event.code]
                if action["is_map_active"]:
                    handleKeyMap(event, isKeyDown, action)
                    continue  # Do not forward J/K/L/I/O key events
            # Forward all other keys
            self.uiKey.write_event(event)
            self.uiKey.syn()

    def handleKeyMap(self, event, isKeyDown, action):
        if action["type"] == "mouse":
            self.uiMouse.write(ecodes.EV_KEY, action["button"], event.value)
            self.uiMouse.syn()
        elif action["type"] == "scroll":
            if isKeyDown:
                self.uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                self.uiMouse.syn()
                self.scroll_task_manager.addScrollTask(event, action)
            else:
                self.scroll_task_manager.removeScrollTask(event)

class ScrollTaskManager:
    def __init__(self):
        self.scroll_tasks = {}

    async def scroll_interval(self, key_code, value):
        await asyncio.sleep(0.5)  # Initial delay
        while mouseMap.key_action_map[key_code]["is_map_active"]:
            mouseMap.uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, value)
            mouseMap.uiMouse.syn()
            await asyncio.sleep(0.05)

    def addScrollTask(self, event, action):
        if event.code in self.scroll_tasks:
            return
        self.scroll_tasks[event.code] = asyncio.create_task(
            self.scroll_interval(event.code, action["value"])
        )

    def removeScrollTask(self, event):
        if event.code not in self.scroll_tasks:
            return
        self.scroll_tasks[event.code].cancel()
        del self.scroll_tasks[event.code]

mouseMap = MouseMap()

def cleanup():
    try:
        mouseMap.keyDevice.ungrab()
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
