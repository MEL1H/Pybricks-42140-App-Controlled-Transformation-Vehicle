## Project Overview

This repository contains a single MicroPython script (`PyBricks_42140.py`) that runs on a **LEGO Technic Hub** inside the LEGO 42140 App-Controlled Transformation Vehicle. It replaces the official LEGO app with custom controller support for a **LEGO Remote (88010)** or an **Xbox Controller**, and was designed to let a parent and young child share the same vehicle with age-appropriate speed settings.

The code runs entirely on-device under **PyBricks** (a MicroPython firmware for LEGO hubs). There is no host-side build system, no tests, and no external dependencies beyond the PyBricks runtime.

---

## Repository Structure

```
.
├── PyBricks_42140.py   # The entire program — single file, runs on the hub
├── README.md           # User-facing documentation
├── LICENSE             # MIT license (© 2025 MEL1H)
└── CLAUDE.md           # This file
```

---

## Hardware Context

| Component | Detail |
|-----------|--------|
| LEGO Hub | `TechnicHub` (LEGO 88012) |
| Right motor | `Port.A`, initialized with `Direction.COUNTERCLOCKWISE` |
| Left motor | `Port.B`, default direction |
| LEGO Remote | `Remote` (LEGO 88010), connected over Bluetooth |
| Xbox Controller | `XboxController`, connected over Bluetooth |
| IMU | Built-in to TechnicHub, used for tumble detection |
| Battery | Monitored via `hub.battery.voltage()` |

Motor direction is normalized at init time so that positive speed values always mean "forward" for both motors regardless of their physical mounting orientation.

---

## Operation Modes

The script supports three mutually exclusive drive modes, configured at startup via the top-level `mode` variable:

| Mode | Variable value | Description |
|------|----------------|-------------|
| Acceleration | `"acceleration"` | Smooth gradual acceleration; acceleration ramps based on recent movement history |
| Geared (Low) | `"geared"` + `gear = "low"` | Instant response, low top-speed, tight turns — ideal for young children |
| Geared (High) | `"geared"` + `gear = "high"` | Instant response, high top-speed |
| Joystick | `"joystick"` | Set automatically when Xbox Controller connects; analog trigger + joystick drive |

`mode` and `gear` are the two primary configuration variables. **All other speed/acceleration values are derived from these.**

---

## Configuration Parameters (top of file)

All tunable values are declared in the clearly marked configuration block (`lines 10–37`). These are the only values that should need adjustment for normal customization:

```python
remote_name           # Bluetooth name of the LEGO remote; set "" to skip name matching
mode                  # "acceleration" | "geared"
gear                  # "low" | "high" (only relevant when mode == "geared")

dead_zone_joystick    # Xbox joystick dead zone (%)
dead_zone_trigger     # Xbox trigger dead zone (%)

remote_search_threshold   # ms to wait for LEGO remote before trying Xbox
mode_switch_threshold     # ms both red buttons must be held to switch modes
gear_switch_threshold     # ms a single red button must be held to change gear
shutdown_switch_threshold # ms center/guide button must be held for shutdown
inactivity_timeout        # ms of no movement before auto-shutdown
after_return_threshold    # ms window used in acceleration-mode state logic
after_straight_threshold  # ms window used in acceleration-mode state logic
battery_check_threshold   # ms between battery voltage polls
cruise_control_threshold  # ms B-button must be held to toggle cruise control
xbox_program_exit_threshold # ms to hold View+Menu+Guide to reconnect controller

slow_speed            # deg/s
moderate_speed        # deg/s
fast_speed            # deg/s

slow_acceleration     # deg/s²
moderate_acceleration # deg/s²
upmid_acceleration    # deg/s²
fast_acceleration     # deg/s²
```

---

## Key Functions

| Function | Purpose |
|----------|---------|
| `connect_controller()` | Attempts LEGO remote first; falls back to Xbox; raises `SystemExit` if neither found |
| `gear_changer(input_mode, input_gear, initial)` | Transitions between modes/gears; sets global speed, acceleration, and motor limits; flashes LED |
| `set_motor_limits(left_accel, right_accel, decel)` | Applies acceleration/deceleration limits to both motors via `motor.control.limits()` |
| `set_led_by_mode()` | Updates hub LED (and remote LED if connected) to reflect the current mode/gear |
| `battery_level_check()` | Reads battery voltage; blinks red if below thresholds; returns `True` when low |
| `check_upside(up_side)` | Uses IMU tilt to detect if vehicle has been flipped; updates `up_side` state |
| `perform_180_turn()` | Executes a 180° point-turn using `run_angle` on both motors |
| `apply_dead_zone(value, threshold)` | Returns 0 when `abs(value) <= threshold`; clamps input to ±100 |
| `remote_light(color, times, ...)` | Blinks remote LED a given number of times with configurable timing |
| `shutdown(message)` | Stops motors, blinks violet, and calls `hub.system.shutdown()` |

---

## Main Loop Logic

The `while True:` loop (line 350 onward) runs continuously on the hub. Each iteration:

1. **Battery check** — polls every `battery_check_threshold` ms.
2. **Tumble detection** — calls `check_upside()` to update `up_side`.
3. **Controller branch** — reads inputs from either `remote` or `xbox` and computes `left_speed` / `right_speed`.
4. **Inactivity check** — shuts down after `inactivity_timeout` ms of zero motor output.
5. **Flip compensation** — if `up_side == "Side.BOTTOM"`, swaps and negates both speeds so forward always means forward from the driver's perspective.
6. **Motor commands** — runs, brakes, or stops motors based on computed speeds and `brake`/`low_battery` flags.
7. **`wait(10)`** — 10 ms loop cadence (~100 Hz).

### LEGO Remote Button Mapping

| Buttons pressed | Action |
|-----------------|--------|
| Left+ only | Both motors forward at `speed` |
| Left- only | Both motors backward at `speed` |
| Left± + Right± | Differential turn (outer motor at `speed`, inner at `turn`) |
| Right± only | Pivot spin in place (no left input) |
| Center (hold 4s) | Shutdown |
| Left-red + Right-red (hold 5s) | Toggle Acceleration ↔ Geared mode |
| Left-red only (hold 3s, in geared) | Switch to high gear |
| Right-red only (hold 3s, in geared) | Switch to low gear |

### Xbox Controller Mapping

| Input | Action |
|-------|--------|
| Right trigger | Forward throttle (0–100%) |
| Left trigger | Reverse throttle (0–100%) |
| Left joystick X | Steering (scales with throttle) |
| A button | Handbrake (run at 0) |
| B button (hold 1s) | Toggle cruise control |
| Y button | Perform 180° turn |
| Guide (hold 4s) | Shutdown |
| View + Menu + Guide (hold 2s) | Reconnect controller (calls `connect_controller()`) |

---

## Global State Variables

These are module-level variables mutated throughout the program. Be aware of them when modifying logic:

```python
mode, gear            # Current drive mode and gear
speed, turn           # Speed values for current mode (set by gear_changer)
motor_acceleration, motor_deceleration, turn_opposite_acceleration
recently_rotated, recently_straight  # Acceleration mode state tracking
up_side               # "Side.TOP" or "Side.BOTTOM"
cruise_control        # Boolean; True when Xbox cruise control is active
brake                 # Boolean; True for one loop iteration on A-press
low_battery           # Boolean; stops motors when True
controller_type       # "remote" | "xbox" | None
remote, xbox          # Controller object references
```

---

## LED Color Conventions

| Color | Meaning |
|-------|---------|
| Violet (solid) | Searching for LEGO remote |
| Violet (blinking fast) | Searching for Xbox controller |
| Violet (blink + solid) | Shutdown sequence |
| Orange (`Color.ACCELERATION`) | Acceleration mode active |
| Cyan (`Color.LOW`) | Geared low mode active |
| Cornflower blue (`Color.HIGH`) | Geared high mode active |
| Xbox green (`Color.XBOX_GREEN`) | Xbox / joystick mode active |
| Dark red (`Color.CRUISE_CONTROL`) | Cruise control active (blinking) |
| Red (solid) | Low battery warning |
| Red (blinking fast) | Critical battery / tumble detected |
| Magenta (brief blink) | Mode/gear change transition |
| Yellow (blinking) | 180° turn in progress |

---

## Development Conventions

### File Editing
- There is **one source file**: `PyBricks_42140.py`. All logic lives here.
- The configuration block at the top of the file (lines 9–37) is the intended customization surface. Avoid scattering magic numbers throughout the code.
- Custom `Color` constants are defined immediately after imports (lines 40–44) using HSV values.

### PyBricks API Constraints
- This runs on **MicroPython** on the hub — no standard library modules like `time`, `os`, or `sys` are available. Use `pybricks.tools.wait()` for delays and `StopWatch` for elapsed time.
- `motor.control.limits(acceleration=[accel, decel])` takes a list, not separate keyword arguments.
- `hub.system.shutdown()` terminates the program and powers off the hub.
- Avoid raising unhandled exceptions in the main loop — the hub will display an error pattern but give no stack trace to the user.

### Style
- Snake_case for all variables and functions.
- Global state mutations use `global` declarations explicitly.
- Print statements (`print(...)`) serve as the primary debug/logging mechanism — visible in the PyBricks IDE console while connected via USB.

### No Test Infrastructure
There is no test runner, linter, or CI pipeline. The program can only be validated by flashing it to the hub via the [PyBricks IDE](https://code.pybricks.com/) and running it on real hardware.

---

## Deployment

1. Open [code.pybricks.com](https://code.pybricks.com/) in a Chromium-based browser.
2. Connect the LEGO Technic Hub via USB or Bluetooth.
3. Flash PyBricks firmware to the hub if not already done.
4. Paste or open `PyBricks_42140.py` in the editor.
5. Press **Run** (▶) to execute on the hub.

There is no compilation step. The `.py` file is sent directly to the hub and interpreted by MicroPython.

---

## Common Pitfalls

- **Remote name mismatch**: If `remote_name` is set to a string that does not match the paired remote's Bluetooth name, `Remote()` will time out and fall through to Xbox search. Set `remote_name = ""` to connect to any LEGO remote.
- **`up_side` initialization**: `up_side` is set at startup via `str(hub.imu.up())`. If the vehicle is placed upside-down before the script starts, driving will be immediately inverted.
- **Cruise control exit**: Cruise control runs its own inner `while cruise_control:` loop. Code after the Xbox input block (inactivity check, flip compensation, motor run) does **not** execute during cruise control — motor commands are issued inside the inner loop directly.
- **`low_battery` scope bug**: In `battery_level_check()`, the line `low_battery = True` creates a local variable rather than mutating the global. This is a known limitation in the current code — the global `low_battery` flag is never actually set to `True` by this function.
