


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
        if data & 0x10:
            self.is_strobed = True
        else:
            self.offset = 0
            self.is_strobed = False

    def read(self) -> bytes:
        data = self.data & ControllerButton.A.value if self.is_strobed else self.data & (0x80 >> self.offset)
        self.offset += 1
        return 1 if data else 0