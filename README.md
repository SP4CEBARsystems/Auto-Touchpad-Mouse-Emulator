# Mouse-Like Agillity From A Touchpad!

## How To Use
Whenever the touchpad is touched, this macro will map the keyboard keys `j`, `k`, and `l` to the mouse buttons `left`, `middle`, and `right` respectively. 
This allows your right hand to press mouse buttons while controlling the touchpad with its thumb, allowing applications that require the use of a mouse to be operated from the touchpad. Examples of such applications include Solidworks, blender, and games like Minecraft or Fortnite.

## When To Use
When you need a mouse but do not have one near you right now.

## Platform
- This project was tested to work on Linux Mint cinnamon and will likely work on other distributions of Linux. If it doesn't, please [open an issue](https://github.com/SP4CEBARsystems/Auto-Touchpad-Mouse-Emulator/issues). If it does, please let me know some other way.
- For Windows refer to [Touchpad-Mouse-Emulator](https://github.com/SP4CEBARsystems/Touchpad-Mouse-Emulator).

## Installation
1. Download the script.
2. Unzip the script
3. Navigate to the script with this command or similar
  ```sh
  cd ~Downloads/Auto-Touchpad-Mouse-Emulator
  ```
4. modify the strings in the three calls to `find_device_path_evdev()` to match your pointer devices, note that the mouse detection is used to exits the program when it is not needed. 
5. Run it with the command below to test it (uses administrator privileges).
  ```sh
  sudo python3 mousemap.py
  ```
6. Navigate to the file in the terminal using `cd` and use the command below to make the file runnable
```sh
chmod +x mousemap.py
```
7. Finally run the path to your file as a command like below every time you want to run it:
```sh
/home/your-user-name/Scripts/mousemap.py
```
