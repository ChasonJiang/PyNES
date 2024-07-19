


from abc import ABC
from enum import Enum

from .interface import ControllerButton




class Controller:
    data:bytes = 0x00
    is_strobed:bool = False
    offset:int = 0x00
    def update(self, button:ControllerButton, is_pressed:bool):
        if is_pressed:
            self.data |= button.value
        else:
            self.data &= ~button.value

    def write(self, data:bytes):
        if data & 0x01:
            self.is_strobed = True
            self.offset = 0
        else:

            self.is_strobed = False

    def read(self) -> bytes:
        data=0
        if self.is_strobed:
            data = self.data & 0x01
        else:
            data = self.data & (0x80 >> self.offset)
            self.offset += 1
            self.offset %= 8
        return 1 if data else 0