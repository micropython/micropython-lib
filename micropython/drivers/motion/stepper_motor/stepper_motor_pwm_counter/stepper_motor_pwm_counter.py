from utime import ticks_diff, ticks_us, ticks_ms
from machine import Pin, PWM, Counter


class StepperMotorPwmCounter:
    def __init__(
        self,
        pin_step=None,
        pin_dir=None,
        pin_step_in=None,
        pin_dir_in=None,
        freq=5_000,
        reverse=0,
        counter=None,
        pwm=None,
    ):
        if isinstance(pin_step, Pin):
            self.pin_step = pin_step
        else:
            self.pin_step = Pin(pin_step, Pin.OUT)

        if isinstance(pin_dir, Pin):
            self.pin_dir = pin_dir
        else:
            self.pin_dir = Pin(pin_dir, Pin.OUT, value=0)

        if pin_step_in is None:
            self.pin_step_in = self.pin_step
        else:
            if isinstance(pin_step_in, Pin):
                self.pin_step_in = pin_step_in
            else:
                self.pin_step_in = Pin(pin_step_in, Pin.OUT)

        if pin_dir_in is None:
            self.pin_dir_in = self.pin_dir
        else:
            if isinstance(pin_dir_in, Pin):
                self.pin_dir_in = pin_dir_in
            else:
                self.pin_dir_in = Pin(pin_dir_in, Pin.OUT, value=0)

        self.freq = freq

        self.reverse = reverse  # reverse the direction of movement of the motor

        if isinstance(counter, Counter):
            self._counter = counter
        else:
            self._counter = Counter(-1, src=self.pin_step_in, direction=self.pin_dir_in)

        self._steps_target = 0
        self._match = 0
        self._steps_over_run = 0

        self._direction = 0  # the current direction of movement of the motor (-1 - movement in the negative direction, 0 - motionless, 1 - movement in the positive direction)

        # must be after Counter() initialization!
        if isinstance(pwm, PWM):
            self._pwm = pwm
        else:
            self._pwm = PWM(pin_step, freq=self._freq, duty_u16=0)  # 0%

    def __repr__(self):
        return f"StepMotorPWMCounter(freq={self._freq}, reverse={self._reverse}, pwm={self._pwm}, counter={self._counter})"

    def deinit(self):
        try:
            self._pwm.deinit()
        except:
            pass
        try:
            self._counter.irq(handler=None)
        except:
            pass
        try:
            self._counter.deinit()
        except:
            pass

    # -----------------------------------------------------------------------
    @property
    def reverse(self):
        return self._reverse

    @reverse.setter
    def reverse(self, reverse: int):
        self._reverse = 1 if bool(reverse) else 0

    # -----------------------------------------------------------------------
    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, freq):
        self._freq = freq if freq > 0 else 1  # pulse frequency in Hz

    # -----------------------------------------------------------------------
    @property
    def direction(self) -> int:
        return self._direction

    @direction.setter
    def direction(self, delta: int):
        if delta > 0:
            self._direction = 1
            self.pin_dir(1 ^ self._reverse)
        elif delta < 0:
            self._direction = -1
            self.pin_dir(0 ^ self._reverse)
        else:
            self._direction = 0
        # print(f'Set direction:{delta} to {self._direction}')

    # -----------------------------------------------------------------------
    @property
    def steps_counter(self) -> int:
        return self._counter.value()

    # -----------------------------------------------------------------------
    @property
    def steps_target(self) -> int:
        return self._steps_target

    @steps_target.setter
    def steps_target(self, steps_target):
        # Set the target position that will be achieved in the main loop
        if self._steps_target != steps_target:
            self._steps_target = steps_target

            delta = self._steps_target - self._counter.value()
            if delta > 0:
                self._match = self._steps_target - self._steps_over_run  # * 2
            elif delta < 0:
                self._match = self._steps_target + self._steps_over_run  # * 2
            self._counter.init(match=self._match)
            self._counter.irq(handler=self.irq_handler, trigger=Counter.IRQ_MATCH)

    # -----------------------------------------------------------------------
    def irq_handler(self, obj):
        self.stop_pulses()
        self._steps_over_run = (
            self._steps_over_run + abs(self._counter.value() - self._match)
        ) // 2
        print(
            f" irq_handler: steps_over_run={self._steps_over_run}, counter.value()={self._counter.value()}"
        )

    def start_pulses(self):
        self._pwm.freq(self._freq)
        self._pwm.duty_u16(32768)

    def stop_pulses(self):
        self._pwm.duty_u16(0)

    def stop(self):
        self.stop_pulses()
        self._steps_target = self._counter.value()

    def go(self):
        delta = self._steps_target - self._counter.value()
        if delta > 0:
            self.direction = 1
            self.start_pulses()
        elif delta < 0:
            self.direction = -1
            self.start_pulses()
        else:
            self.stop_pulses()
        # print(f" go: delta={delta}, steps_target={self._steps_target}, match={self._match}, counter.value()={self._counter.value()}, direction={self._direction}, steps_over_run={self._steps_over_run}, freq={self._freq}")

    def is_ready(self) -> bool:
        delta = self._steps_target - self._counter.value()
        # print(f" is_ready: delta={delta}, counter.value()={self._counter.value()}, steps_target={self._steps_target}, direction={self._direction}")
        if self._direction > 0:
            if delta <= 0:
                self.stop_pulses()
                return True
        elif self._direction < 0:
            if delta >= 0:
                self.stop_pulses()
                return True
        else:
            return delta == 0
        return False
