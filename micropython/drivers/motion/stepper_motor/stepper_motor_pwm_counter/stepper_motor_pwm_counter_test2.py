# stepper_motor_pwm_counter_test2.py

from time import sleep

from stepper_motor_pwm_counter import StepperMotorPwmCounter


try:
    motor = StepperMotorPwmCounter(26, 23)
    print(motor)

    f_min = 3_000
    f_max = 50_000
    df = 1_000
    motor.freq = f_min
    motor_steps_start = motor.steps_counter
    motor.steps_target = 8192 * 10
    while True:
        if not motor.is_ready():
            motor.go()
        else:
            print()
            print(
                f"motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}"
            )
            print("SET steps_target", -motor.steps_target)
            print("sleep(1)")
            print()
            sleep(1)
            motor_steps_start = motor.steps_target
            motor.steps_target = -motor.steps_target
            motor.go()

        m = min(
            abs(motor.steps_counter - motor_steps_start),
            abs(motor.steps_target - motor.steps_counter),
        )
        motor.freq = min(f_min + df * m // 1000, f_max)

        sleep(0.1)

except Exception as e:
    print(e)
    raise e
finally:
    try:
        motor.deinit()
    except:
        pass
