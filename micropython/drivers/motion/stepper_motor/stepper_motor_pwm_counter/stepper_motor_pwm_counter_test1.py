# stepper_motor_pwm_counter_test1.py

from time import sleep
from stepper_motor_pwm_counter import StepperMotorPwmCounter
from target_wiring import encoder_loopback_out_pins, encoder_loopback_in_pins

pin_step, pin_dir = encoder_loopback_out_pins
pin_step_in, pin_dir_in = encoder_loopback_in_pins

try:
    motor = StepperMotorPwmCounter(
        pin_step, pin_dir, pin_step_in=pin_step_in, pin_dir_in=pin_dir_in, freq=10_000
    )
    print(motor)

    motor.steps_target = 8192
    while True:
        if not motor.is_ready():
            motor.go()
            print(
                f"motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}"
            )
        else:
            print()
            print(
                f"motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}"
            )
            print("SET steps_target", -motor.steps_target)
            print("sleep(1)")
            print()
            sleep(1)
            motor.steps_target = -motor.steps_target
            motor.go()

        sleep(0.1)

except Exception as e:
    print(e)
    raise e
finally:
    try:
        motor.deinit()
    except:
        pass
