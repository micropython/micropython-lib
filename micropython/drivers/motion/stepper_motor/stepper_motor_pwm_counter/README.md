## Stepper motor PWM-Counter driver

This MicroPython software driver is designed to control stepper motor using STEP/DIR hardware driver.

![stepper_motor_driver](https://github.com/IhorNehrutsa/micropython-lib/assets/70886343/27933a08-7225-4931-a1ee-8e0042d0b822)

* The driver signal "STEP" (aka "PULSE") is intended for clock pulses. In one pulse, the motor rotor turns one step. The higher the frequency of pulses, the higher the speed of rotation of the rotor.

* The driver signal "DIR" is intended to select the direction of rotation of the engine ("1" - in one direction, "0" - in the other direction).

![forward_reverse](https://github.com/IhorNehrutsa/micropython-lib/assets/70886343/f1986469-6fca-4d10-a6f2-262020a19946)

### Hardware

As an example of a STEP / DIR hardware driver:

* [TMC2209](https://wiki.fysetc.com/Silent2209) module, TB6612,

* [TB6560-V2](https://mypractic.com/stepper-motor-driver-tb6560-v2-description-characteristics-recommendations-for-use) module,

* [TB6600](https://mytectutor.com/tb6600-stepper-motor-driver-with-arduino) based driver,

* DM860H, DM556 etc.

### Software

The main feature of this driver is that the generation and counting of pulses are performed by hardware, which frees up time in the main loop. PWM will start pulses and Counter will stop pulses in irq handler.

The PWM unit creates STEP pulses and sets the motor speed.

The GPIO unit controls the DIR pin, the direction of rotation of the motor.

The Counter unit counts pulses, that is, the actual position of the stepper motor.

![stepper_motor_pwm_counter](https://github.com/IhorNehrutsa/micropython-lib/assets/70886343/4e6cf4b9-b198-4fa6-8bcc-51d873bf74ce)

In general case MicroPython ports need 4 pins: PWM STEP output, GPIO DIR output, Counter STEP input, Counter DIR input (red wires in the image).

The ESP32 port allows to connect Counter inputs to the same outputs inside the MCU(green wires in the picture), so 2 pins are needed.

This driver requires PR's:

[esp32/PWM: Reduce inconsitencies between ports. #10854](https://github.com/micropython/micropython/pull/10854)

[ESP32: Add Quadrature Encoder and Pulse Counter classes. #8766](https://github.com/micropython/micropython/pull/8766)

Constructor
-----------

class:: StepperMotorPwmCounter(pin_step, pin_dir, freq, reverse)

   Construct and return a new StepperMotorPwmCounter object using the following parameters:

      - *pin_step* is the entity on which the PWM is output, which is usually a
        :ref:`machine.Pin <machine.Pin>` object, but a port may allow other values, like integers.
      - *freq* should be an integer which sets the frequency in Hz for the
        PWM cycle i.e. motor speed.
      - *reverse*  reverse the motor direction if the value is True

Properties
----------

property:: StepperMotorPwmCounter.freq

      Get/set the current frequency of the STEP/PWM output.

property:: StepperMotorPwmCounter.steps_counter

      Get current steps position form the Counter.

property:: StepperMotorPwmCounter.steps_target

      Get/set the steps target.

Methods
-------

method:: StepperMotorPwmCounter.deinit()

      Disable the PWM output.

method:: StepperMotorPwmCounter.go()

      Call it in the main loop to move the motor to the steps_target position.

method:: StepperMotorPwmCounter.is_ready()

      Return True if steps_target is achieved.

Tested on ESP32.

**Simple example is:**
```
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
            print(f'motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}')
        else:
            print()
            print(f'motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}')
            print('SET steps_target', -motor.steps_target)
            print('sleep(1)')
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
```

**Output is:**
```
StepMotorPWMCounter(pin_step=Pin(26), pin_dir=Pin(23), freq=10000, reverse=0,
  pwm=PWM(Pin(26), freq=10000, duty_u16=0),
  counter=Counter(0, src=Pin(26), direction=Pin(23), edge=Counter.RISING, filter_ns=0))
motor.steps_target=8192, motor.steps_counter=2, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=1025, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=2048, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=3071, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=4094, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=5117, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=6139, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=7162, motor.is_ready()=False
motor.steps_target=8192, motor.steps_counter=8185, motor.is_ready()=False
 irq_handler: steps_over_run=6, counter.get_value()=8204

motor.steps_target=8192, motor.steps_counter=8204, motor.is_ready()=True
SET steps_target -8192
sleep(1)

motor.steps_target=-8192, motor.steps_counter=7200, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=6176, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=5153, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=4130, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=3107, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=2084, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=1061, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=37, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-986, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-2009, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-3032, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-4054, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-5077, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-6100, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-7123, motor.is_ready()=False
motor.steps_target=-8192, motor.steps_counter=-8146, motor.is_ready()=False
 irq_handler: steps_over_run=4, counter.get_value()=-8188
motor.steps_target=-8192, motor.steps_counter=-8189, motor.is_ready()=False

motor.steps_target=-8192, motor.steps_counter=-9209, motor.is_ready()=True
SET steps_target 8192
sleep(1)

motor.steps_target=8192, motor.steps_counter=-8205, motor.is_ready()=False
Traceback (most recent call last):
  File "<stdin>", line 25, in <module>
KeyboardInterrupt:
```

**Example with motor speed acceleration/deceleration:**
```
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
            print(f'motor.steps_target={motor.steps_target}, motor.steps_counter={motor.steps_counter}, motor.is_ready()={motor.is_ready()}')
            print('SET steps_target', -motor.steps_target)
            print('sleep(1)')
            print()
            sleep(1)
            motor_steps_start = motor.steps_target
            motor.steps_target = -motor.steps_target
            motor.go()


        m = min(abs(motor.steps_counter - motor_steps_start), abs(motor.steps_target - motor.steps_counter))
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

```
[Motor speed acceleration/deceleration video](https://drive.google.com/file/d/1HOkmqnaepOOmt4XUEJzPtQJNCVQrRUXs/view?usp=drive_link)
