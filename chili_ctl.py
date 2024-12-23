#!/usr/bin/env python3
"""Chili pad HW abstraction """
# -*- coding: utf-8 -*-

class ChiliCtl:
    """Control Chili pad HW. All temperatures in Fahrenheit

    Attributes: 
        temperature_target: target temperature we want chili to reach
        temperature: current chili pad temperature
        power_state: 
        temperature_target: 
    """
    max_temp = 105
    min_temp = 55
    def __init__(self) -> None:
        self.power_on()
        self.temperature_target = 0
        self.temperature = 5
        self.temperature = self.get_temp()
        self.power_state = 0

    def set_temp(self, temperature: int):
        self.temperature_target = temperature
        # TODO set temperature using chili pad hw

    def get_temp(self) -> int:
        # TODO read temperature from chili pad hw
        return self.temperature

    def power_on(self):
        # TODO power on chili pad
        self.power_state = 1

    def power_off(self):
        # TODO power off chili pad
        self.power_state = 0

def main():
    pass


if __name__ == '__main__':
    main()
