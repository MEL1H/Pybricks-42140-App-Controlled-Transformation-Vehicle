# LEGO App-Controlled Transformation Vehicle - PyBricks Script

This is a Python script for controlling the LEGO App-Controlled Transformation Vehicle using PyBricks.

My goal was to create a script that allows me to play with the vehicle together with my son. He uses a LEGO remote controller (safe for small kids), while I can enjoy the vehicle with a more dynamic, video game-like experience.  
Both the LEGO remote and an Xbox controller can connect to the vehicle (not simultaneously), and I can select the desired initial speed mode for the LEGO controller.  
For example, a low geared mode is perfect for my 3-year-old son, as it’s easier to control. Later, as he grows, he can enjoy faster speed modes too!

## Features
- Connection support for LEGO Remote (88010) or Xbox controller
- Three speed modes:
  - **Acceleration Mode** (smooth gradual acceleration)
  - **Geared Mode** (Low and High gears)
- Idle automatic turn-off
- Cruise control (Xbox controller)
- Handbrake functionality (Xbox controller)
- Change control modes dynamically
- LED color effects based on the current state

## How It Works
- The script first searches for the LEGO remote.  
  **Solid purple LED** = searching for LEGO controller.
- After 4 seconds, if no LEGO controller is found, it switches to search for an Xbox controller.  
  **Blinking purple LED** = searching for Xbox controller.

> **Note:**  
> If you didn't set a custom name for your LEGO remote, make sure to remove the remote name line from the code, or connection may fail.

## Controller Behavior

### LEGO Controller
- Automatically starts in the initial speed mode specified at the beginning of the code.
- **Acceleration Mode:** Smooth and gradual speed increase.
- **Geared Mode:** Instant response to gear changes:
  - Press and hold **left center button** = switch to high gear.
  - Press and hold **right center button** = switch to low gear.
  - Press both **left and right center buttons** for 3 seconds to toggle between Acceleration and Geared modes.

### Xbox Controller
- No gear modes — triggers and joysticks provide analog control, like a PC racing game.
- Acceleration is based on how fast you press the trigger or move the joystick.
- **Cruise Control:**  
  Press **B** button to activate cruise mode. The vehicle will maintain its current speed but still allow steering.  
  Press **B** again to deactivate.
- **Handbrake:**  
  Press **A** button to immediately resist movement (brake effect).

## Notes
- The LED on the hub will change colors and effects based on current control mode, connection status, and vehicle behavior.
- This script focuses on both safety and fun: low-speed control for young kids, and dynamic driving for adults.
