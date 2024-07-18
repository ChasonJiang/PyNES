



from abc import ABC
import logging
from typing import Dict, List

from .interface import IBus

from .io_register import PPURegisterManager
from .interface import IController
# from cpu import ICPU
from .exceptions import CartridgeNotFound, InvalidAddress
from .memory import IMemory
from .cartridge import ICatridge

LOGGER = logging.getLogger(__name__)





class CPUBus(IBus):
    memory:IMemory = None
    cartridge:ICatridge = None
    controllers:IController = {}
    ppu_reg_manager:PPURegisterManager = None

    def __init__(self, memory:IMemory, ppu_reg_manager:PPURegisterManager=None):
        self.memory = memory
        self.ppu_reg_manager = ppu_reg_manager

    
    def set_cartridge(self, cartridge:ICatridge):
        self.cartridge = cartridge

    def register_controller(self, controller:IController, player_num:int=1):
        if player_num > 2:
            raise ValueError("Player number should be 1 or 2")
        self.controllers[player_num] = controller

    def unregister_controller(self, player_num:int=1):
        self.controllers.pop(player_num)

    def write_byte(self, address:int, data:bytes):
        if data is None:
            raise ValueError("Data cannot be None")
        
        if address < 0x2000:
            # RAM
            # mirror for $0x0800-$0x1FFF
            address %= 0x0800

            self.memory.write(address, data)
        elif address < 0x401f:
            # IO registers
            if address < 0x2008:
                # PPU registers
                self.ppu_reg_manager.write_for_cpu(address, data)

            elif address < 0x4000 and address >= 0x2008:
                # for mirror 0x2000-0x2007
                address = 0x2000 + (address % 8)
                self.write_byte(address, data)

            elif address == 0x4014:
                # OAMDMA
                # TODO: check this implementation
                addr = data * 0x100
                if addr > 0x07ff or addr < 0x0200:
                    # LOGGER.warn(f"CPUBus: OAMDMA address out of range: {hex(addr)}")
                    raise RuntimeError(f"CPUBus: OAMDMA address out of range: {hex(addr)}")
                sprite_data = self.memory.read(addr, 256)
                self.ppu_reg_manager.write_for_cpu(address, sprite_data)
    
            elif address == 0x4016:
                # Joystick
                if self.controllers == {}:
                    LOGGER.warn(f"CPUBus: Controller not found")
                    return
                for i in self.controllers.values():
                    i.write(data)
                return
            else:
                LOGGER.warn(f"CPUBus: IO registers not implemented")
        elif address < 0x6000:
            # TODO: Expansion ROM
            raise NotImplementedError("Expansion ROM not implemented")
        elif address < 0x10000:
            # Cartridge
            if self.cartridge is None:
                raise CartridgeNotFound("Cartridge not found")
            self.cartridge.mapper.write(address, data)
        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")

    def write_word(self, address:int, data:int):
        self.write_byte(address, data & 0xFF)
        self.write_byte(address+1, (data >> 8) & 0xFF)

    def read_byte(self, address:int) -> bytes:
        
        if address < 0x2000:
            # RAM
            # mirror for $0x0800-$0x1FFF
            address %= 0x0800

            return self.memory.read(address)
        elif address < 0x401f:
            # IO registers
            # if address == 0x2000:
            #     return self.ppu_reg_manager.ctrl_reg.read()
            if address < 0x2008 or address == 0x4014:
                return self.ppu_reg_manager.read_for_cpu(address)
            elif address < 0x4000 and address >= 0x2008:
                # for mirror 0x2000-0x2007
                address = 0x2000 + (address % 8)
                return self.read_byte(address)
            elif address == 0x4016:
                if self.controllers == {}:
                    LOGGER.warn(f"CPUBus: Controller not found")
                    return 0x00
                return self.controllers[1].read()
            elif address == 0x4017:
                if self.controllers == {}:
                    LOGGER.warn(f"CPUBus: Controller not found")
                    return 0x00
                return self.controllers[2].read()
            else:
                # TODO: IO registers
                LOGGER.warn(f"CPUBus: IO registers not implemented")
                return 0x00
            
        elif address < 0x6000:
            # TODO: Expansion ROM
            raise NotImplementedError("Expansion ROM not implemented")
        elif address < 0x10000:
            if self.cartridge is None:
                raise CartridgeNotFound("Cartridge not found")
            # Cartridge
            return self.cartridge.mapper.read(address)
        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")
        
    def read_word(self, address:int) -> int:
        low = self.read_byte(address)
        high = self.read_byte(address+1)
        return (high << 8) | low


class PPUBus(IBus):
    memory:IMemory = None
    cartridge:ICatridge = None
    palette_index_memory:IMemory = None

    is_horizontal_mirror:bool = True

    exist_extended_vram:bool = False

    def __init__(self, memory:IMemory, palette_index_memory:IMemory):
        self.memory = memory
        self.palette_index_memory = palette_index_memory

    def set_cartridge(self, cartridge:ICatridge):
        self.cartridge = cartridge
        self.is_horizontal_mirror = self.cartridge.rom.header.mirroring == 0
        if self.cartridge.mapper.ram is not None\
            and len(self.cartridge.mapper.ram) >= 2*1024:
            self.exist_extended_vram = True
        else:
            self.exist_extended_vram = False

    def write_byte(self, address:int, data:bytes):
        # for mirror
        address %= 0x4000

        if address < 0x2000:
            # CHR-ROM (parttern table)
            if self.cartridge is None:
                raise CartridgeNotFound("Cartridge not found")
            self.cartridge.mapper.write(address, data)
        elif address < 0x3f00: 
            # vram  (name table)

            if address >= 0x3000:
                # for mirror
                address -= 0x1000
            address -= 0x2000
            # self.write_to_vram(address, data)
            # offset = 0x0400 if self.is_horizontal_mirror else 0x0800
            # self.write_to_vram(address + offset, data)
            
            if self.is_horizontal_mirror:
                # address %= 0x0800
                if address < 0x0800:
                    address %= 0x0400
                    self.memory.write(address, data)
                    if self.exist_extended_vram:
                        self.cartridge.mapper.write(address, data)            
                else:
                    address %= 0x0400
                    address += 0x0400
                    self.memory.write(address, data)  
                    if self.exist_extended_vram:
                        self.cartridge.mapper.write(address, data)    

            else:
                if address < 0x0800:
                    self.memory.write(address, data)
                elif address >= 0x0800:
                    address -= 0x0800
                    self.memory.write(address, data)
                    if self.exist_extended_vram:
                        self.cartridge.mapper.write(address, data)
            
                    

        
        elif address < 0x4000:
            # palette
            address -= 0x3f00
            address %= 0x20
            self.palette_index_memory.write(address, data)
            # LOGGER.warn(f"CPUBus: palette not implemented")
        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")
        

    def write_word(self, address:int, data:int):
        self.write_byte(address, data & 0xFF)
        self.write_byte(address+1, (data >> 8) & 0xFF)

    def read_byte(self, address:int) -> bytes:
        # for mirror
        address %= 0x4000

        if address < 0x2000:
            # CHR-ROM (parttern table)
            if self.cartridge is None:
                raise CartridgeNotFound("Cartridge not found")
            return self.cartridge.mapper.read(address)
        elif address < 0x3f00:
            if address >= 0x3000:
                # for mirror
                address -= 0x1000

            # # vram  (name table)
            # if address < 0x2800:
            #     # on vram
            #     address -= 0x2000
            #     return self.memory.read(address)
            # elif address < 0x3000:
            #     # on cartridge
            #     return self.cartridge.mapper.read(address)

            # return self.read_from_vram(address - 0x2000)

            address -= 0x2000
            if self.is_horizontal_mirror:
                if address < 0x0800:
                    address %= 0x0400
                    return self.memory.read(address)
                else:
                    address %= 0x0400
                    address += 0x0400
                    return self.memory.read(address)
            else:
                if address < 0x0800:
                    return self.memory.read(address)
                else:
                    address -= 0x0800
                    return self.memory.read(address)


        elif address < 0x4000:
            address -= 0x3f00
            address %= 0x20
            # palette
            # LOGGER.warn(f"CPUBus: palette not implemented")
            return self.palette_index_memory.read(address)

        else:
            raise InvalidAddress(f"Cannot access memory at {hex(address)}")


    def read_word(self, address:int) -> int:
        low = self.read_byte(address)
        high = self.read_byte(address+1)
        return (high << 8) | low