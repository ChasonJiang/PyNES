import numpy as np

from .interface import IFrame


class NPFrame(IFrame):
    width:int = 256
    height:int = 240
    data:np.ndarray = np.zeros((3, width, height), dtype=np.uint8)

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]):
        self.data[0, x, y] = color[0]
        self.data[1, x, y] = color[1]
        self.data[2, x, y] = color[2]

