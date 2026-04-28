# stepper_motor_pwm_counter_test1.py

from time import sleep

from stepper_motor_pwm_counter import StepperMotorPwmCounter


try:
    motor = StepperMotorPwmCounter(26, 23, freq=10_000)
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
