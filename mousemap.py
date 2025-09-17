#!/usr/bin/env python3
import asyncio
import signal
import sys
from evdev import InputDevice, ecodes, UInput, list_devices

class DeviceFinder:
    def __init__(self):
        """
        Initialize DeviceFinder by locating touchpad, keyboard, and mouse devices.
        Exits if a mouse is detected.
        """
        self.touchpad = self.findDevicePathEvdev('touchpad') or "/dev/input/event6"
        self.keyboard = self.findDevicePathEvdev('Asus Keyboard') or "/dev/input/event7"
        self.mouse = self.findDevicePathEvdev('SteelSeries SteelSeries Rival 3')
        if self.mouse is not None:
            print("Mouse detected: This macro is now obsolete, exiting.")
            sys.exit(0)

    @staticmethod
    def findDevicePathEvdev(name_hint):
        """
        Search for an input device path containing the given name hint.

        Args:
            name_hint (str): Substring to match in device names.

        Returns:
            str or None: Path to the device if found, else None.
        """
        for path in list_devices():
            dev = InputDevice(path)
            if name_hint.lower() in dev.name.lower():
                return path
        return None

class MouseMap:
    def __init__(self):
        """
        Initialize MouseMap, set up devices, virtual input, key mappings, and scroll manager.
        """
        self.devices = DeviceFinder()
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
        self.keyDevice = InputDevice(self.devices.keyboard)
        self.keyDevice.grab()
        print("keyboard grabbed")

        self.keyActionMap = {
            ecodes.KEY_J: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_LEFT},
            ecodes.KEY_K: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_MIDDLE},
            ecodes.KEY_L: {"is_map_active": False, "type": "mouse", "button": ecodes.BTN_RIGHT},
            ecodes.KEY_I: {"is_map_active": False, "type": "scroll", "value": -1},  # scroll down
            ecodes.KEY_O: {"is_map_active": False, "type": "scroll", "value": 1},   # scroll up
        }

        self.scrollTaskManager = ScrollTaskManager()

    async def touchpadMonitor(self):
        """
        Monitor touchpad events and update isMapActive based on touch state.
        """
        touchpadDevice = InputDevice(self.devices.touchpad)
        async for event in touchpadDevice.async_read_loop():
            if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                self.isMapActive = event.value == 1

    async def keyboardMonitor(self):
        """
        Monitor keyboard events, map specific keys to mouse actions if active, and forward others.
        """
        async for event in self.keyDevice.async_read_loop():
            isKeyEvent = event.type == ecodes.EV_KEY
            isPressedOrReleased = event.value in (1, 0)
            isToBeMapped = event.code in self.keyActionMap
            isKeyDown = event.value == 1
            if isKeyEvent and isPressedOrReleased and isToBeMapped:
                if isKeyDown:
                    self.keyActionMap[event.code]["is_map_active"] = self.isMapActive
                action = self.keyActionMap[event.code]
                if action["is_map_active"]:
                    self.handleKeyMap(event, isKeyDown, action)
                    continue  # Do not forward J/K/L/I/O key events
            # Forward all other keys
            self.uiKey.write_event(event)
            self.uiKey.syn()

    def handleKeyMap(self, event, isKeyDown, action):
        """
        Handle mapped key events, emitting mouse button or scroll actions.

        Args:
            event: The input event object.
            isKeyDown (bool): True if key is pressed, False if released.
            action (dict): Mapping info for the key.
        """
        if action["type"] == "mouse":
            self.uiMouse.write(ecodes.EV_KEY, action["button"], event.value)
            self.uiMouse.syn()
        elif action["type"] == "scroll":
            if isKeyDown:
                self.uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, action["value"])
                self.uiMouse.syn()
                self.scrollTaskManager.addScrollTask(event, action)
            else:
                self.scrollTaskManager.removeScrollTask(event)

class ScrollTaskManager:
    def __init__(self):
        """
        Initialize ScrollTaskManager to manage scroll tasks for keys.
        """
        self.scrollTasks = {}

    async def scrollInterval(self, key_code, value):
        """
        Emit repeated scroll events while the mapped key is active.

        Args:
            key_code (int): Key code being monitored.
            value (int): Scroll direction and amount.
        """
        await asyncio.sleep(0.5)  # Initial delay
        while mouseMap.keyActionMap[key_code]["is_map_active"]:
            mouseMap.uiMouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, value)
            mouseMap.uiMouse.syn()
            await asyncio.sleep(0.05)

    def addScrollTask(self, event, action):
        """
        Start a scroll task for a key if not already running.

        Args:
            event: The input event object.
            action (dict): Mapping info for the key.
        """
        if event.code in self.scrollTasks:
            return
        self.scrollTasks[event.code] = asyncio.create_task(
            self.scrollInterval(event.code, action["value"])
        )

    def removeScrollTask(self, event):
        """
        Cancel and remove the scroll task for a key.

        Args:
            event: The input event object.
        """
        if event.code not in self.scrollTasks:
            return
        self.scrollTasks[event.code].cancel()
        del self.scrollTasks[event.code]

class CleanupManager:
    @staticmethod
    def cleanup():
        """
        Release grabbed keyboard device and print status.
        """
        try:
            mouseMap.keyDevice.ungrab()
            print("keyboard ungrabbed")
        except Exception:
            pass

    @staticmethod
    def signalHandler(sig, frame):
        """
        Handle termination signals, clean up resources, and exit.
        """
        CleanupManager.cleanup()
        print("exiting...")
        sys.exit(0)

    @staticmethod
    def setupSignalHandlers():
        """
        Register signal handlers for graceful termination.
        """
        signal.signal(signal.SIGINT, CleanupManager.signalHandler)
        signal.signal(signal.SIGTERM, CleanupManager.signalHandler)

mouseMap = MouseMap()
CleanupManager.setupSignalHandlers()

async def main():
    """
    Run the main event loop for touchpad and keyboard monitoring.
    Ensures cleanup on exit.
    """
    try:
        await asyncio.gather(
            mouseMap.touchpadMonitor(),
            mouseMap.keyboardMonitor()
        )
    finally:
        CleanupManager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
