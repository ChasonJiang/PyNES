




from abc import ABC
from enum import Enum
from typing import List

from .rom import NESRom


class IBus(ABC):
    def write_byte(self, address:int, data:bytes):
        pass
    
    def write_word(self, address:int, data:int):
        pass

    def read_byte(self, address:int) -> bytes:
        pass

    def read_word(self, address:int) -> int:
        pass


class IMapper(ABC):
    ram:bytearray = None
    prg_data:bytearray = None
    chr_data:bytearray = None
    def read(self, address:int) -> bytes:
        pass

    def write(self, address:int, data:bytes):
        pass


class ICatridge(ABC):
    rom: NESRom = None
    mapper:IMapper = None


class ControllerButton(Enum):
    A:bytes = 0x80
    B:bytes = 0x40
    SELECT:bytes = 0x20
    START:bytes = 0x10
    UP:bytes = 0x08
    DOWN:bytes = 0x04
    LEFT:bytes = 0x02
    RIGHT:bytes = 0x01

class IController(ABC):
    data:bytes = 0x00

    def update(self, button:ControllerButton, is_pressed:bool):
        pass

    def write(self, data:bytes):
        pass

    def read(self) -> bytes:
        pass



class IMemory(ABC):
    
    def write(self, address:int, data:bytes):
        pass
    
    def read(self, address:int, size:int=1) -> List[bytes|bytearray]:
        pass

class CPUStatusRegister:
    N: bytes = 0
    V: bytes = 0
    U: bytes = 0
    B: bytes = 0
    D: bytes = 0
    I: bytes = 0
    Z: bytes = 0
    C: bytes = 0

    def read(self) -> bytes:
        return (self.N << 7) | (self.V << 6) | (self.U << 5) | (self.B << 4) | (self.D << 3) | (self.I << 2) | (self.Z << 1) | self.C

    def write(self, data:bytes):
        self.N = (data >> 7) & 0x01
        self.V = (data >> 6) & 0x01
        self.U = (data >> 5) & 0x01
        self.B = (data >> 4) & 0x01
        self.D = (data >> 3) & 0x01
        self.I = (data >> 2) & 0x01
        self.Z = (data >> 1) & 0x01
        self.C = data & 0x01

class Register:
    PC: int = 0
    SP: bytes = 0
    A: bytes = 0
    X: bytes = 0
    Y: bytes = 0
    # P: bytes = 0
    P:CPUStatusRegister = CPUStatusRegister()


class Flags:
  C = 1 << 0 # Carry
  Z = 1 << 1 # Zero
  I = 1 << 2 # Disable interrupt
  D = 1 << 3 # Decimal Mode ( unused in nes )
  B = 1 << 4 # Break
  U = 1 << 5 # Unused ( always 1 )
  V = 1 << 6 # Overflow
  N = 1 << 7 # Negative



class ICPU(ABC):
    regs: Register = None
    bus: IBus = None
    cycles: int = 0
    defer_cycles: int = 0
    def clock(self):
        pass

    def cycle(self):
        pass

    def reset(self):
        pass

    def nmi(self):
        pass

    def irq(self):
        pass


class IORegister(ABC):
    
    def read(self, address:int):
        pass
    
    def write(self, address:int, data:bytes):
        pass
    
class IPPU(ABC):
    bus:IBus = None


class IFrame(ABC):
    width:int = 0
    height:int = 0
    data:object = None

    def set_pixel(self, x:int, y:int, color:object):
        pass


