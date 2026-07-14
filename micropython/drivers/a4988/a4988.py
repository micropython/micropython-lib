import time

# Constants
STEPS_PER_REV = 200  # Number of steps per motor revolution
MIN_DELAY = 0.001    # Minimum delay between steps (controls maximum speed)

class A4988:
    def __init__(self, step_pin, dir_pin, en_pin=None):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.en_pin = en_pin
        if self.en_pin is not None:
            self.enable_motor(enabled=True)

    def enable_motor(self, enabled=True):
        """Enable or disable the motor driver (active low)."""
        if self.en_pin:
            self.en_pin.value(0 if enabled else 1)

    def step_motor(self, steps=STEPS_PER_REV, direction=1, delay=0.005):
        """Move the motor a specified number of steps in the given direction."""
        self.dir_pin.value(direction)  # Set direction (1 = forward, 0 = backward)
        for _ in range(steps):
            self.step_pin.value(1)
            time.sleep(delay)
            self.step_pin.value(0)
            time.sleep(delay)

    def calculate_speed(self, current_delay):
        """Calculate the current speed in steps per second and RPM."""
        if current_delay <= 0:
            return 0, 0
        steps_per_second = 1 / (2 * current_delay)  # Delay is for each half-step
        rpm = (steps_per_second / STEPS_PER_REV) * 60  # Convert to RPM
        return steps_per_second, rpm

    def inc_speed(self, current_delay):
        """Decrease delay to increase speed, respecting minimum delay limit."""
        new_delay = max(current_delay - 0.001, MIN_DELAY)
        return new_delay

    def dec_speed(self, current_delay):
        """Increase delay to decrease speed."""
        new_delay = current_delay + 0.001
        return new_delay

    def forward_motion(self, steps=STEPS_PER_REV, delay=0.005):
        """Move motor forward for a given number of steps and delay."""
        self.step_motor(steps=steps, direction=1, delay=delay)

    def backward_motion(self, steps=STEPS_PER_REV, delay=0.005):
        """Move motor backward for a given number of steps and delay."""
        self.step_motor(steps=steps, direction=0, delay=delay)
