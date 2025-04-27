from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor, Remote
from pybricks.iodevices import XboxController
from pybricks.parameters import Port, Button, Color, Direction
from pybricks.tools import wait, StopWatch

print("----------------------------------")

# <------------------ Configuration Parameters ------------------->
remote_name = "M3L1H_remote" # for lego controller 88010, can be "" string if not used
#--- MODE ----
mode = "acceleration" # "acceleration" or "geared"
gear = "high" # only if geared mode is selected, "low" or "high"
#--- JOYSTICK ----
dead_zone_joystick = 5
dead_zone_trigger = 1
#--- THRESHOLD # ms ----
remote_search_threshold = 4000
mode_switch_threshold = 5000
gear_switch_threshold = 3000
shutdown_switch_threshold = 4000
inactivity_timeout = 600000
after_return_threshold = 1000
after_straight_threshold = 1000
battery_check_threshold = 10000
cruise_control_threshold = 1000 
xbox_program_exit_threshold = 2000
#--- SPEED ----
slow_speed = 500
moderate_speed = 1000
fast_speed = 1600
#--- ACCELERATION ----
slow_acceleration = 1250
moderate_acceleration = 3000
upmid_acceleration = 5000
fast_acceleration = 10000
# <---------------------------------------------------------------->

# Custom Colors
Color.XBOX_GREEN = Color(h=119.45, s=89.34, v=47.84)
Color.ACCELERATION = Color(h=35, s=100, v=100)
Color.LOW = Color(h=190, s=100, v=100)
Color.HIGH = Color(h=240, s=100, v=100)
Color.CRUISE_CONTROL = Color(h=6, s=70, v=70)

# Initialize hub and motors
hub = TechnicHub()
right_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
left_motor = Motor(Port.B)

# Controller variables
controller_type = None
remote = None
xbox = None

# State variables
left_speed = 0
right_speed = 0
left_speed_previous = moderate_speed
right_speed_previous = moderate_speed
up_side = str(hub.imu.up())
joystick_drive_speed = fast_speed / 100

speed = None
turn = None
last_gear_high = None
last_gear_low = None
motor_acceleration = None
motor_deceleration = None
turn_opposite_acceleration = None
recently_rotated = None
recently_straight = None
cruise_control = None
brake = None
low_battery = None

# Timers
shutdown_timer = StopWatch()
mode_switch_timer = StopWatch()
low_gear_switch_timer = StopWatch()
high_gear_switch_timer = StopWatch()
inactivity_timer = StopWatch()
after_return_timer = StopWatch()
after_straight_timer = StopWatch()
battery_check_timer = StopWatch()
cruise_control_timer = StopWatch()
xbox_program_exit_timer = StopWatch()

def battery_level_check():
    try:
        battery = hub.battery.voltage()
        if battery < 6400:
            low_battery = True
            print("CHARGE BATTERY:", battery)
            hub.light.blink(Color.RED,[100,50])
            if remote:
                remote_light(Color.RED,5,50,100)
            wait(50)
            return True
        elif battery < 6550:
            print("LOW BATTERY:", battery)
            hub.light.on(Color.RED)
            if remote:
                remote.light.on(Color.RED)
            wait(50)
            return True
        else:
            print("Battery level good:", battery)
    except Exception as e:
        print(f"Battery check error: {e}")

def set_motor_limits(left_motor_acceleration, right_motor_acceleration, motor_deceleration):
    left_motor.control.limits(acceleration=[left_motor_acceleration, motor_deceleration])
    right_motor.control.limits(acceleration=[right_motor_acceleration, motor_deceleration])

def shutdown(message):
    print(message)
    right_motor.stop()
    left_motor.stop()
    if xbox:
        xbox.rumble(70, 200)
    hub.light.blink(Color.VIOLET,[100,50])
    if remote:
        remote_light(Color.VIOLET, 1, 50, 100)
    hub.light.on(Color.VIOLET)
    if remote:
        remote.light.on(Color.VIOLET)
    wait(200)
    if remote:
        remote.light.on(Color.NONE)
    hub.light.off()
    hub.system.shutdown()   
    
def check_upside(up_side):
    try:
        pitch, roll = hub.imu.tilt()
        if abs(pitch) > 88:
            print("Tumble detected")
            if up_side == "Side.TOP":
                up_side = "Side.BOTTOM"
                left_motor.brake()
                right_motor.brake()
                hub.light.blink(Color.RED,[50,10])
                remote_light(Color.RED, 1, interval_none=10, interval_color=50)
                if controller_type == "xbox":
                    xbox.rumble((25, 25, 0, 0), 100)
                    wait(50)
                    xbox.rumble((0, 0, 25, 25), 100)
                set_led_by_mode()
            elif up_side == "Side.BOTTOM":
                up_side = "Side.TOP"
                left_motor.brake()
                right_motor.brake()
                hub.light.blink(Color.RED,[50,10])
                remote_light(Color.RED, 1, interval_none=10, interval_color=50)
                if controller_type == "xbox":
                    xbox.rumble((25, 25, 0, 0), 100)
                    wait(50)
                    xbox.rumble((0, 0, 25, 25), 100)
                set_led_by_mode()
                return up_side
        else:
            current_upside = str(hub.imu.up())
            if current_upside == "Side.TOP" or current_upside == "Side.BOTTOM":
                up_side = current_upside
                return up_side
        return up_side
    except Exception as e:
        print(f"IMU error: {e}")
        set_led_by_mode()
        return up_side


def perform_180_turn():
    print("Performing 180-degree turn")
    hub.light.blink(Color.YELLOW,[500,50])
    right_motor.brake()
    left_motor.brake()
    wait(50)
    try:
        right_motor.run_angle(fast_speed, 860, wait=False)
        left_motor.run_angle(fast_speed, -860)
        wait(50)
        set_led_by_mode()
    except Exception as e:
        print(f"Motor error during 180-turn: {e}")
        set_led_by_mode()

def apply_dead_zone(value, threshold):
    if value is None:
        return 0
    value = max(min(value, 100), -100)
    return value if abs(value) > threshold else 0

def remote_light(color, times=1, interval_none=50, interval_color=250):
    if remote:
        for _ in range(times):
            remote.light.on(Color.NONE)
            wait(interval_none)
            remote.light.on(color)
            wait(interval_color)
            remote.light.on(Color.NONE)
        wait(interval_none)

def set_led_by_mode():
    if mode == "acceleration":
        hub.light.off()
        if remote:
            remote.light.on(Color.NONE)
        wait(10)
        hub.light.on(Color.ACCELERATION)
        if remote:
            remote.light.on(Color.ACCELERATION)
    elif mode == "geared":
        if gear == "high":
            hub.light.off()
            if remote:
                remote.light.on(Color.NONE)
            wait(10)
            hub.light.on(Color.HIGH)
            if remote:
                remote.light.on(Color.HIGH)
        elif gear == "low":
            hub.light.off()
            if remote:
                remote.light.on(Color.NONE)
            wait(10)
            hub.light.on(Color.LOW)
            if remote:
                remote.light.on(Color.LOW)
    elif mode == "joystick":
        if cruise_control:
            hub.light.blink(Color.CRUISE_CONTROL,[500,200])
        else:
            hub.light.off()
            wait(10)
            hub.light.on(Color.XBOX_GREEN)

def gear_changer(input_mode, input_gear="low",initial=False):
    global mode, gear, speed, turn, last_gear_high, last_gear_low, motor_acceleration, motor_deceleration, turn_opposite_acceleration, recently_rotated
    if input_mode == "geared" and input_gear == "low":
        mode = "geared"
        gear = "low"
        speed = slow_speed
        turn = slow_speed / 4
        last_gear_high = False
        last_gear_low = True
        recently_rotated = False
        after_return_timer.reset()
        motor_acceleration = slow_acceleration
        motor_deceleration = fast_acceleration
        turn_opposite_acceleration = slow_acceleration
    elif input_mode == "geared" and input_gear == "high":
        gear = "high"
        speed = fast_speed
        turn = slow_speed
        last_gear_high = True
        last_gear_low = False
        recently_rotated = False
        after_return_timer.reset()
        motor_acceleration = fast_acceleration
        motor_deceleration = fast_acceleration
        turn_opposite_acceleration = fast_acceleration
    elif input_mode == "acceleration":
        mode = "acceleration"
        speed = fast_speed
        turn = slow_speed * 2 / 3
        last_gear_high = False
        last_gear_low = False
        recently_rotated = False
        after_return_timer.reset()
        motor_acceleration = slow_acceleration
        motor_deceleration = fast_acceleration
        turn_opposite_acceleration = slow_acceleration
    if initial:
        if input_mode == "acceleration":
            print("Initial mode :", mode[0].upper()+mode[1:])
        else:
            print("Initial mode :", gear[0].upper()+gear[1:], mode[0].upper()+mode[1:])
    else:
        hub.light.blink(Color.MAGENTA,[250,50])
        remote_light(Color.MAGENTA, 1, interval_none=50, interval_color=250)
        set_led_by_mode()
        if input_mode == "acceleration":
            print("Switched to", mode[0].upper()+mode[1:])
        else:
            print("Switched to", gear[0].upper()+gear[1:], mode[0].upper()+mode[1:])
    set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)

def connect_controller():
    global remote, controller_type, mode, gear, xbox
    try:
        if xbox:
            raise SystemExit
        hub.light.on(Color.VIOLET)
        print("Searching for Lego Controller")
        remote = Remote(remote_name, timeout=remote_search_threshold)
        controller_type = "remote"
        print("Connected to", remote_name)
        mode = mode
        if mode == "geared":
            gear = gear
            if gear == "low":
                hub.light.blink(Color.LOW,[100,50,100,50,100,50])
                remote_light(Color.LOW, 3, interval_color=100)
            else:
                hub.light.blink(Color.HIGH,[100,50,100,50,100,50])
                remote_light(Color.HIGH, 3, interval_color=100)
            set_led_by_mode()
        else:
            hub.light.blink(Color.ACCELERATION,[100,50,100,50,100,50])
            remote_light(Color.ACCELERATION, 3, interval_color=100)
            set_led_by_mode()

    except OSError:
        try:
            print("Lego Controller not available")
            print("Searching for XBOX Controller")
            hub.light.blink(Color.VIOLET,[50,100])
            xbox = XboxController()
            controller_type = "xbox"
            print("Connected to Xbox Controller.")
            mode = "joystick"
            hub.light.blink(Color.XBOX_GREEN,[100,50,100,50,100,50])
            remote_light(Color.XBOX_GREEN, 3, interval_color=100)
            xbox.rumble(70, 200)
            set_led_by_mode()

        except OSError:
            print("No controller found.")
            hub.light.blink(Color.RED,[50,50,50,50,50,50])
            right_motor.stop()
            left_motor.stop()
            raise SystemExit
            
# <------------------ Main program starts here ------------------->

connect_controller()

if mode == "geared":
    if gear == "low":
        gear_changer("geared", "low", True)
    elif gear == "high":
        gear_changer("geared", "high", True)
elif mode == "acceleration":
    gear_changer("acceleration", initial=True)
elif mode == "joystick":
    pass

while True:
    if battery_check_timer.time() >= battery_check_threshold:
        battery_level_check()
        battery_check_timer.reset()
        
    inactivity_timer.resume()
    up_side = check_upside(up_side)

    if controller_type == "remote":
        pressed = remote.buttons.pressed()

        left_plus = Button.LEFT_PLUS in pressed
        left_minus = Button.LEFT_MINUS in pressed
        right_plus = Button.RIGHT_PLUS in pressed
        right_minus = Button.RIGHT_MINUS in pressed
        center_green = Button.CENTER in pressed
        left_red = Button.LEFT in pressed
        right_red = Button.RIGHT in pressed

        if center_green:
            if shutdown_timer.time() >= shutdown_switch_threshold:
                shutdown("Manual shutdown requested.")
        else:
            shutdown_timer.reset()

        if left_red and right_red:
            if mode_switch_timer.time() >= mode_switch_threshold:
                if mode == "acceleration":
                    gear_changer("geared", "low")
                else:
                    gear_changer("acceleration")
                mode_switch_timer.reset()
                
        else:
            mode_switch_timer.reset()

        if left_red and not last_gear_high and not right_red:
            if low_gear_switch_timer.time() >= gear_switch_threshold:
                if mode == "geared":
                    gear_changer("geared", "high")
                low_gear_switch_timer.reset()
        else:
            low_gear_switch_timer.reset()

        if right_red and not last_gear_low and not left_red:
            if high_gear_switch_timer.time() >= gear_switch_threshold:
                if mode == "geared":
                    gear_changer("geared", "low")
                high_gear_switch_timer.reset()
        else:
            high_gear_switch_timer.reset()

        if (left_plus or left_minus) and not (right_plus or right_minus):
            if left_plus and not left_minus:
                left_speed = speed
                right_speed = speed
            elif left_minus and not left_plus:
                left_speed = -speed
                right_speed = -speed
            else:
                left_speed = right_speed = 0
            if mode == "acceleration":
                recently_straight = True
                after_straight_timer.reset()
                if recently_rotated:
                    if after_return_timer.time() <= after_return_threshold:
                        motor_acceleration = upmid_acceleration
                        motor_deceleration = fast_acceleration
                        turn_opposite_acceleration = upmid_acceleration
                        set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
                    else:
                        recently_rotated = False
                else:
                    motor_acceleration = slow_acceleration
                    motor_deceleration = fast_acceleration
                    turn_opposite_acceleration = slow_acceleration
                    set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
            else:
                set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
                
        elif (left_plus or left_minus) and (right_plus or right_minus):
            if mode == "acceleration":
                recently_rotated = True
                after_return_timer.reset()
                if recently_straight:
                    if after_straight_timer.time() <= after_straight_threshold:
                        motor_acceleration = upmid_acceleration
                        motor_deceleration = fast_acceleration
                        turn_opposite_acceleration = upmid_acceleration
                    else:
                        recently_straight = False
                else:
                    motor_acceleration = slow_acceleration
                    motor_deceleration = fast_acceleration
                    turn_opposite_acceleration = slow_acceleration
            if left_plus:
                if right_plus:
                    left_speed = turn
                    right_speed = speed
                    set_motor_limits(motor_acceleration, turn_opposite_acceleration, motor_deceleration)
                else:
                    left_speed = speed
                    right_speed = turn
                    set_motor_limits(turn_opposite_acceleration, motor_acceleration, motor_deceleration)
            if left_minus:
                if right_plus:
                    left_speed = -turn
                    right_speed = -speed
                    set_motor_limits(motor_acceleration, turn_opposite_acceleration, motor_deceleration)
                else:
                    left_speed = -speed
                    right_speed = -turn
                    set_motor_limits(turn_opposite_acceleration, motor_acceleration, motor_deceleration)
                    
        elif (right_plus or right_minus) and not (left_plus or left_minus):
            if right_plus and not right_minus:
                left_speed = turn * -2
                right_speed = turn * 2
            elif right_minus and not right_plus:
                left_speed = turn * 2
                right_speed = turn * -2
            else:
                left_speed = right_speed = 0
            if mode == "geared":
                if gear == "high":
                    left_speed = left_speed / 2
                    right_speed = right_speed / 2
                if gear == "low":
                    left_speed = left_speed * 2
                    right_speed = right_speed * 2
            if mode == "acceleration":
                recently_rotated = True
                if recently_straight:
                    if after_straight_timer.time() <= after_straight_threshold:
                        motor_acceleration = upmid_acceleration
                        motor_deceleration = fast_acceleration
                        turn_opposite_acceleration = upmid_acceleration
                        set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
                    else:
                        recently_straight = False
                else:
                    motor_acceleration = slow_acceleration
                    motor_deceleration = fast_acceleration
                    turn_opposite_acceleration = slow_acceleration
                    set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
            else:
                set_motor_limits(motor_acceleration, motor_acceleration, motor_deceleration)
        else:
            left_speed = 0
            right_speed = 0
        
    elif controller_type == "xbox":
        pressed = xbox.buttons.pressed()

        # Button.A in pressed
        # Button.B in pressed
        # Button.X in pressed
        # Button.Y in pressed
        # Button.UP in pressed
        # Button.DOWN in pressed
        # Button.RIGHT in pressed
        # Button.LEFT in pressed
        # Button.LB in pressed
        # Button.RB in pressed
        # Button.LJ in pressed
        # Button.RJ in pressed
        # Button.GUIDE in pressed
        # Button.MENU in pressed
        # Button.VIEW in pressed
        # Button.P1 in pressed
        # Button.P2 in pressed
        # Button.P3 in pressed
        # Button.P4 in pressed

        right_trigger, left_trigger = xbox.triggers()
        left_x_axis, left_y_axis = xbox.joystick_left()
        right_x_axis, right_y_axis = xbox.joystick_right()

        if Button.GUIDE in pressed and Button.VIEW not in pressed and Button.MENU not in pressed:
            if shutdown_timer.time() >= shutdown_switch_threshold:
                shutdown("Manual shutdown requested.")
        else:
            shutdown_timer.reset()

        if Button.Y in pressed:
            perform_180_turn()
            
        if Button.A in pressed:
            brake = True
            
        if Button.VIEW in pressed and Button.MENU in pressed and Button.GUIDE in pressed:
            if xbox_program_exit_timer.time() >= xbox_program_exit_threshold:
                connect_controller()
        else:
            xbox_program_exit_timer.reset()
                

        dead_zoned_left_trigger = apply_dead_zone(left_trigger, dead_zone_trigger)
        dead_zoned_right_trigger = apply_dead_zone(right_trigger, dead_zone_trigger)
        dead_zoned_left_x_axis = apply_dead_zone(left_x_axis, dead_zone_joystick)

        speed_vertical = dead_zoned_left_trigger - dead_zoned_right_trigger

        if speed_vertical > 0:
            joystick_sensivity = abs(speed_vertical)/100
            calibrated_left_x_axis = dead_zoned_left_x_axis * joystick_sensivity
            left_speed = (speed_vertical + calibrated_left_x_axis) * joystick_drive_speed
            right_speed = (speed_vertical - calibrated_left_x_axis) * joystick_drive_speed
        elif speed_vertical < 0:
            joystick_sensivity = abs(speed_vertical)/100
            calibrated_left_x_axis = dead_zoned_left_x_axis * joystick_sensivity
            left_speed = (speed_vertical - calibrated_left_x_axis) * joystick_drive_speed
            right_speed = (speed_vertical + calibrated_left_x_axis) * joystick_drive_speed
        else:
            joystick_sensivity = (abs(dead_zoned_left_x_axis)/100)/2
            calibrated_left_x_axis = dead_zoned_left_x_axis * joystick_sensivity
            left_speed = (calibrated_left_x_axis) * joystick_drive_speed
            right_speed = (-calibrated_left_x_axis) * joystick_drive_speed
        
        if dead_zoned_left_x_axis != 0:
            if speed_vertical != 0 and (abs(speed_vertical)+abs(dead_zoned_left_x_axis)) < 100:
                joystick_acceleration_ratio = int(moderate_acceleration + (((((abs(speed_vertical)+abs(dead_zoned_left_x_axis))/2) - 0) * (fast_acceleration - moderate_acceleration)) / (100 - 0)))
            elif (abs(speed_vertical)+abs(dead_zoned_left_x_axis)) > 100:
                joystick_acceleration_ratio = int(fast_acceleration)
            else:
                joystick_acceleration_ratio = int(moderate_acceleration + (((((abs(dead_zoned_left_x_axis))/1) - 0) * (fast_acceleration - moderate_acceleration)) / (100 - 0)))
        else:
            if speed_vertical != 0:
                joystick_acceleration_ratio = int(moderate_acceleration + (((((abs(speed_vertical))/1) - 0) * (fast_acceleration - moderate_acceleration)) / (100 - 0)))
            else:
                joystick_acceleration_ratio = int(moderate_acceleration)

        set_motor_limits(joystick_acceleration_ratio, joystick_acceleration_ratio, fast_acceleration)

        left_speed_previous = left_speed
        right_speed_previous = right_speed        
  
        if Button.B in pressed:
            if cruise_control_timer.time() >= cruise_control_threshold:
                if not cruise_control:
                    cruise_control_timer.reset()
                    recorded_left_speed = left_speed
                    recorded_right_speed = right_speed
                    if recorded_left_speed * recorded_right_speed > 0:
                        total_speed = recorded_left_speed + recorded_right_speed
                        left_speed = total_speed / 2
                        right_speed = total_speed / 2
                    cruise_control = True
                    hub.light.blink(Color.CRUISE_CONTROL,[500,200])
                while cruise_control:
                    up_side = check_upside(up_side)
                    pressed = xbox.buttons.pressed()
                    right_trigger, left_trigger = xbox.triggers()
                    left_x_axis, left_y_axis = xbox.joystick_left()
                    dead_zoned_left_trigger = apply_dead_zone(left_trigger, dead_zone_trigger)
                    dead_zoned_right_trigger = apply_dead_zone(right_trigger, dead_zone_trigger)
                    dead_zoned_left_x_axis = apply_dead_zone(left_x_axis, dead_zone_joystick)
                    if Button.B in pressed or (recorded_left_speed == 0 and recorded_right_speed == 0):
                        if cruise_control_timer.time() >= cruise_control_threshold:
                            cruise_control = False
                            cruise_control_timer.reset()
                            set_led_by_mode()
                    elif Button.A in pressed:
                        cruise_control = False
                        cruise_control_timer.reset()
                        set_led_by_mode()
                    else:
                        if recorded_left_speed * recorded_right_speed > 0:
                            if abs(dead_zoned_left_x_axis) > 0:
                                if total_speed > 0:
                                    left_speed = (total_speed / 2) + ((total_speed / 2) * (dead_zoned_left_x_axis / 100))
                                    right_speed = (total_speed / 2) - ((total_speed / 2) * (dead_zoned_left_x_axis / 100))
                                elif total_speed < 0:
                                    left_speed = (total_speed / 2) + ((total_speed / 2) * (dead_zoned_left_x_axis / 100))
                                    right_speed = (total_speed / 2) - ((total_speed / 2) * (dead_zoned_left_x_axis / 100))
                            else:
                                left_speed = total_speed / 2
                                right_speed = total_speed / 2
                        if up_side == "Side.BOTTOM":
                            left_speed, right_speed = -right_speed, -left_speed
                        left_motor.run(left_speed)
                        right_motor.run(right_speed)
                        inactivity_timer.reset()
                        wait (10)
                    
    if inactivity_timer.time() >= inactivity_timeout:
        shutdown("Inactivity timeout reached. Shutting down...")
    
    if up_side == "Side.BOTTOM":
        left_speed, right_speed = -right_speed, -left_speed

    if low_battery:
        left_motor.stop()
        right_motor.stop()
        inactivity_timer.reset()
    elif brake:
        brake = False
        left_motor.run(0)
        right_motor.run(0)
        inactivity_timer.reset()
    elif left_speed or right_speed:
        left_motor.run(left_speed)
        right_motor.run(right_speed)
        inactivity_timer.reset()
    else:
        left_motor.stop() 
        right_motor.stop()
        if pressed:
            inactivity_timer.reset()
    
    wait(10)
    