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

# def valid_key_codes():
#     # Only include integer key codes, not aliases or non-key constants
#     return [code for name, code in ecodes.__dict__.items()
#             if name.startswith("KEY_") and isinstance(code, int)]

# Virtual device to emit events
uiKey = UInput()
ui = UInput({
    ecodes.EV_KEY: (
        [
            ecodes.BTN_LEFT,
            ecodes.BTN_MIDDLE,
            ecodes.BTN_RIGHT
        ]
        # + valid_key_codes()
    ),
    ecodes.EV_REL: [
        ecodes.REL_X,
        ecodes.REL_Y,
        ecodes.REL_WHEEL
    ]
})

finger_down = False
# finger_down = True
# grabbed = True
keyDev = InputDevice(KEYBOARD)
# keyDev.grab()

# keyDev.grab()
# for event in keyDev.read_loop():
#     uiKey.write_event(event)
#     uiKey.syn()

async def touchpad_monitor():
    global finger_down
    global keyDev
    # = InputDevice(KEYBOARD)
    dev = InputDevice(TOUCHPAD)
    grabbed = False
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            finger_down = event.value == 1
            # print("held!", finger_down)
            if finger_down and not grabbed:
                keyDev.grab()
                grabbed = True
                # print("grab")
            elif not finger_down and grabbed:
                keyDev.ungrab()
                grabbed = False
                # print("ungrab")

async def keyboard_monitor():
    global finger_down
    global keyDev

    # keyDev.grab()
    # for event in keyDev.read_loop():
    #     uiKey.write_event(event)
    #     uiKey.syn()
    # print("escaped")

    # keyDev = InputDevice(KEYBOARD)
    async for event in keyDev.async_read_loop():
        # uiKey.write_event(event)
        # uiKey.syn()
        # continue
        # print("escaped")
        # Always check and update grab state BEFORE processing the event
        # print("event")

        if event.type == ecodes.EV_KEY and event.value in (1, 0):  # press/release
            # uiKey.write_event(event)
            # uiKey.syn()
            # continue
            if finger_down and event.code in (ecodes.KEY_J, ecodes.KEY_K, ecodes.KEY_L, ecodes.KEY_I, ecodes.KEY_O):
                # Block J/K/L and map to mouse buttons
                if event.code == ecodes.KEY_J:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                    # print("left", event.value)
                elif event.code == ecodes.KEY_K:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_MIDDLE, event.value)
                    # print("middle", event.value)
                elif event.code == ecodes.KEY_L:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, event.value)
                    # print("right", event.value)
                elif event.code == ecodes.KEY_I and event.value == 1:  # scroll down on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, -1)
                    # print("scroll down")
                elif event.code == ecodes.KEY_O and event.value == 1:  # scroll up on key press
                    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, 1)
                    # print("scroll up")
                continue  # Do not forward J/K/L/I/O key events
            elif finger_down:
                # Forward all other keys
                uiKey.write_event(event)
                # uiKey.syn()
        # else:
        #     ui.write_event(event)
        uiKey.syn()
        ui.syn()

async def main():
    await asyncio.gather(
        touchpad_monitor(),
        keyboard_monitor()
    )

if __name__ == "__main__":
    asyncio.run(main())
