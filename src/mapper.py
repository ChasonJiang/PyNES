



from abc import ABC
import logging
from .interface import IMapper

from .exceptions import InvalidAddress
from .rom import NESRom
LOGGER = logging.getLogger(__name__)

def choose_mapper(rom:NESRom):
    if rom.header.mapper_type == 0:
        return Mapper0(bytearray(2*1024), rom.prg_data, rom.chr_data)
    else:
        raise NotImplementedError(f"Mapper {rom.header.mapper_type} not implemented")




class Mapper0(IMapper):
    is_mirrored:bool = False
    ram:bytearray = None
    prg_data:bytearray = None
    chr_data:bytearray = None

    def __init__(self, ram:bytearray, prg_data:bytearray, chr_data:bytearray):
        
        self.is_mirrored = True if len(prg_data) == 16*1024 else False
        self.ram = ram
        self.prg_data = prg_data
        self.chr_data = chr_data if len(chr_data) > 0 else bytearray(int(0x2000))

    def read(self, address:int)->bytes:
        # address &= 0xffff

        if address < 0x2000:
            return self.chr_data[address]
        elif address < 0x8000:
            if self.ram is None:
                raise InvalidAddress(f"Cannot access memory at {hex(address)}")
            return self.ram[address - 0x6000]
        elif address < 0x10000:
            return self.prg_data[(address & 0xbfff if self.is_mirrored else address) - 0x8000]
        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")
            
    def write(self, address:int, data:bytes):
        # address &= 0xffff

        if address < 0x2000:
            # CHR ROM
            self.chr_data[address] = data
            LOGGER.warn(f"Mapper0: Attempt to write a byte {data:04X} to CHR ROM at {address:04X}")
        elif address < 0x8000:
            # SRAM
            if self.ram is None:
                raise InvalidAddress(f"Cannot access memory at {hex(address)}")
            self.ram[address - 0x6000] = data
        elif address < 0x10000:
            # PRG ROM
            self.prg_data[(address & 0xbfff if self.is_mirrored else address) - 0x8000] = data
            LOGGER.warn(f"Mapper0: Attempt to write a byte {data:04X} to PRG ROM at {address:04X}")
        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")