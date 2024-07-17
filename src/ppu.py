






from abc import ABC
from typing import Callable, Dict, List, Tuple

from .frame import NPFrame

from .interface import IPPU, IBus
from .io_register import AddressRegister, ControlRegister, MaskRegister, PPUInternalRegister, StatusRegister
import logging

LOGGER = logging.getLogger(__name__)

class PPURegisterManager:
    internal_buffer:bytes = 0x00
    internal_reg:PPUInternalRegister = PPUInternalRegister()
    addr_reg:AddressRegister = AddressRegister()
    ctrl_reg:ControlRegister = ControlRegister()
    mask_reg:MaskRegister = MaskRegister()
    status_reg:StatusRegister = StatusRegister()
    scroll_reg:List[bytes] = [0, 0, 0] # x, y, w
    oam_addr_reg:bytes = 0x00
    # oam_data_reg:bytes = 0x00
    # oam_dma_reg:bytes = 0x00

    # To save sprite data
    oam_data:bytearray = bytearray(256)


    ppu_bus:IBus = None
    ppu:IPPU = None


    def __init__(self, ppu, ppu_bus: IBus):
        self.ppu_bus = ppu_bus
        self.ppu = ppu

    def read_for_cpu(self, address: int) -> bytes:
        if address in [0x2000, 0x2001, 0x2003, 0x2005, 0x2006, 0x4014]:
            # raise RuntimeError(f"Attempt to read from write-only PPU address {address:04X}")
            LOGGER.warn(f"PPURegisterManager: Attempt to read from write-only IORegister at {address:04X}, it will be returned as 0x00")
            # access write-only PPU register
            return 0x00
        elif address == 0x2002:
            # Status Register
            result = self.status_reg.read()
            self.status_reg.clear_vblank()
            self.internal_reg.w_latch = True
            return result
        elif address == 0x2004:
            # OAM Data Register
            # result = self.oam_data_reg
            return self.oam_data[self.oam_addr_reg]
        elif address == 0x2007:
            addr = self.addr_reg.read()
            self.addr_reg.increment(self.ctrl_reg.get_increment())
            if addr < 0x3f00:
                result = self.internal_buffer
                self.internal_buffer = self.ppu_bus.read_byte(addr)
                return result
            else:
                return self.ppu_bus.read_byte(addr)

    def write_for_cpu(self, address: int, data: bytes|bytearray):

        self.internal_buffer = data

        if address == 0x2000:
            # Control Register
            before_nmi_status = self.ctrl_reg.GENERATE_NMI
            self.ctrl_reg.write(data)
            if not before_nmi_status \
                and self.ctrl_reg.GENERATE_NMI \
                and self.status_reg.VBLANK:

                self.ppu.nmi_for_cpu()
                
        elif address == 0x2001:
            # Mask Register
            # TODO:check if mask register is implemented
            # print("Warning: PPU Mask Register is not implemented")
            self.mask_reg.write(data)
        elif address == 0x2002:
            # Status Register
            # TODO:check if status register is implemented
            # print("Warning: PPU Status Register is not implemented")
            # self.status_reg.write(data)
            LOGGER.warn(f"PPURegisterManager: Attempt to write to PPU Status Register at {address:04X}, it will be ignored")
        elif address == 0x2003:
            # OAM Address Register
            # TODO: check if oam address register is implemented
            # print("Warning: PPU OAM Address Register is not implemented")
            self.oam_addr_reg = data
        elif address == 0x2004:
            # OAM Data Register
            # TODO: check if oam data register is implemented
            # print("Warning: PPU OAM Data Register is not implemented")
            # self.oam_data_reg = data
            self.oam_data[self.oam_addr_reg] = data
            self.oam_addr_reg += 1
        elif address == 0x2005:
            # Scroll Register
            # TODO: check if scroll register is implemented
            # print("Warning: PPU Scroll Register is not implemented")
            # share address register state
            
            if self.internal_reg.w_latch:
                self.scroll_reg[0] = data
                self.scroll_reg[2] = 0
            else:
                self.scroll_reg[1] = data
                self.scroll_reg[2] = 1
            self.update_w_latch()

        elif address == 0x2006:
            # PPU Address Register

            self.addr_reg.update(data, self.internal_reg.w_latch)
            self.update_w_latch()
            # self.addr_reg.increment(self.ctrl_reg.get_increment())

        elif address == 0x2007:
            # PPU Data Register
            addr = self.addr_reg.read()
            self.addr_reg.increment(self.ctrl_reg.get_increment())
            self.ppu_bus.write_byte(addr, data)
        elif address == 0x4014:
            # OAM DMA
            # print("Warning: PPU OAM DMA is not implemented")
            self.oam_data = data
        else:
            raise ValueError(f"Invalid PPU Register Address: {address}")
        
    def update_w_latch(self):
        self.internal_reg.w_latch = not self.internal_reg.w_latch





PALETTE={
    0: (100,100,100),
    1: (255,0,0),
    2: (0,255,0),
    3: (0,0,255),
}

class PPU(IPPU):
    reg_manager: PPURegisterManager = None
    bus:IBus = None

    cpu_nmi_func:Callable = None

    tick:int = 0

    cycles:int = 0
    cpu_defer_cycles:int = 0

    renderers:Dict[str,Tuple[Callable,tuple,dict]] = {}

    current_frame: NPFrame = NPFrame()

    scanline:int = 0

    

    def __init__(self, bus:IBus):
        self.bus = bus
        self.reg_manager = PPURegisterManager(self, bus)


    def register_cpu_nmi(self, func: Callable):
        self.cpu_nmi_func = func

    def nmi_for_cpu(self):
        if self.cpu_nmi_func is not None:
            self._call_renderer()
            self.cpu_nmi_func()
        else:
            raise ValueError("CPU NMI Function is not registered")

    def set_cpu_defer_cycles(self, cycles:int):
        self.cpu_defer_cycles = cycles

    def clock(self,):
        self.cycles += self.cpu_defer_cycles*3
        self.set_cpu_defer_cycles(0)

        if self.cycles >= 341:
            if self.is_sprite_zero_hit(self.cycles):
                self.reg_manager.status_reg.set_sprite_zero_hit()
            
            self.cycles -= 341
            self.scanline += 1

            if self.scanline == 241:
                self.reg_manager.status_reg.set_vblank()
                self.reg_manager.status_reg.clear_sprite_zero_hit()

                if self.reg_manager.ctrl_reg.GENERATE_NMI:
                    self.nmi_for_cpu()
            
            if self.scanline >= 261:
                self.scanline = 0
                self.reg_manager.status_reg.clear_sprite_zero_hit()
                self.reg_manager.status_reg.clear_vblank()





    def is_sprite_zero_hit(self, cycle:int) -> bool:
        y = self.reg_manager.oam_data[0]
        x = self.reg_manager.oam_data[3]
        return self.scanline == y and x <= cycle and self.reg_manager.mask_reg.Show_sprites


    def register_renderer(self, renderer: Callable, args:tuple=(), kwargs:dict={}):

        self.renderers[renderer.__name__] = (renderer, args, kwargs)

    def _call_renderer(self):
        self.render_background()
        if self.renderers != {}:
            for renderer, args, kwargs in self.renderers.values():
                renderer(self.current_frame, *args, **kwargs)
        else:
            raise ValueError("Renderer is not registered")


    def execute(self):
        self.render_background()


    def render_background(self):
        pattern_base_addr = self.reg_manager.ctrl_reg.get_background_pattern_addr()
        nametable_base_addr = self.reg_manager.ctrl_reg.get_nametable_addr()
        self.current_frame = NPFrame()
        for offset in range(960):
            # Get Tile Index from Nametable
            tile_idx = self.bus.read_byte(nametable_base_addr + offset)
            tile_x = (offset % 32) * 8
            tile_y = (offset // 32) * 8

            # Get Tile Data from Pattern Table
            tile = [self.bus.read_byte(pattern_base_addr + (tile_idx * 16 + f)) for f in range(16)]
            
            # Render Tile
            for y in range(8):
                # TODO: check this
                high_byte = tile[y]
                low_byte = tile[y+8]

                for x in range(8):
                    color_idx = ((high_byte >> (7-x)) & 0x01) << 1 | ((low_byte >> (7-x)) & 0x01) 
                    color = self.index_palette(color_idx)
                    self.current_frame.set_pixel(tile_x+x, tile_y+y, color)
    

    def index_palette(self, color_idx:int) -> int:
        
        return PALETTE[color_idx]

                    
                    
