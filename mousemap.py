#!/usr/bin/env python3
import asyncio
from evdev import InputDevice, categorize, ecodes, UInput, AbsInfo

# Adjust these for your system
TOUCHPAD = "/dev/input/event6"   # run `libinput list-devices` to find this
KEYBOARD = "/dev/input/event7"

# Virtual device to emit events
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

async def touchpad_monitor():
    global finger_down
    dev = InputDevice(TOUCHPAD)
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            finger_down = event.value == 1
            # print("held!", finger_down)

async def keyboard_monitor():
    global finger_down
    dev = InputDevice(KEYBOARD)
    # dev.grab()
    grabbed = False
    async for event in dev.async_read_loop():
        # Dynamically grab/ungrab based on finger_down
        if finger_down and not grabbed:
            dev.grab()
            grabbed = True
            print("grab")
        elif not finger_down and grabbed:
            dev.ungrab()
            grabbed = False
            print("ungrab")

        if event.type == ecodes.EV_KEY and event.value in (1, 0):  # press/release
            if finger_down and event.code in (ecodes.KEY_J, ecodes.KEY_K, ecodes.KEY_L):
                # Block J/K/L and map to mouse buttons
                if event.code == ecodes.KEY_J:
                    # if event.value == 1:
                    #     dev.grab()
                    # else:
                    #     dev.ungrab()
                    ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                    print("left",event.value)
                elif event.code == ecodes.KEY_K:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_MIDDLE, event.value)
                    print("middle",event.value)
                elif event.code == ecodes.KEY_L:
                    ui.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, event.value)
                    print("right",event.value)
                # Do not forward J/K/L key events
                continue
            # else:
                # Forward all other keys
                # ui.write_event(event)
        ui.syn()

async def main():
    await asyncio.gather(
        touchpad_monitor(),
        keyboard_monitor()
    )

if __name__ == "__main__":
    asyncio.run(main())
