from random import randrange
from typing import List


def get_random(start: float, stop: float) -> float:
    start *= 100
    stop *= 100
    int_start = int(start)
    int_stop = int(stop)
    value = randrange(int_start, int_stop) / 100
    return round(value, 2)


class PowerManager:
    """
    This class is to generate how much power each battery should give.
    The amount is random between specified values, and the range changes depending on the value of previous generated powers
    For example if the range was between 1 and 2, and the first time the value was 1.9,
    the next time the range would be from 1 to a number slightly less than one.
    """

    def __init__(self, top_range: float, bottom_range: float) -> None:
        """
        Initialize the power manager.

        Args:
            top_range (float): The top of the range of values to output
            bottom_range (float): The lower value of the range of values to output
        """
        self.init_top_range = top_range
        self.init_bottom_range = bottom_range
        self.previous_values: List[float] = []

    def get_average(self) -> float:
        """
        Gets the averate of the values in `self.previous_values`

        Returns:
            float: [description]
        """
        total: float = 0
        count = 0
        for value in self.previous_values:
            total += value
            count += 1

        return total / count

    def generate_power(self) -> float:
        top_range = self.init_top_range
        bottom_range = self.init_bottom_range

        print(top_range, bottom_range)
        if len(self.previous_values) > 0:
            average = self.get_average()
            mid_point = (self.init_top_range - self.init_bottom_range) / 2
            difference = (average - self.init_bottom_range) - mid_point
            if difference > 0:
                top_range -= difference
            else:
                bottom_range -= difference
            print(top_range, bottom_range, average, mid_point, difference)

        value = get_random(bottom_range, top_range)
        self.previous_values.append(value)
        return value
