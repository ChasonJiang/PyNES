







import logging

from abc import ABC
from typing import List

from .interface import IPPU, IBus, IORegister

LOGGER = logging.getLogger(__name__)






class AddressRegister(IORegister):
    hight:bytes = 0x00
    low:bytes = 0x00
    # w_latch:bool = True

    def reset(self):
        self.hight = 0x00
        self.low = 0x00
        # self.w_latch = True

    def write(self, data: int):
        self.hight = data >> 8
        self.low = data & 0x00FF

    def read(self)->int:
        return (self.hight << 8) | self.low
    
    def update(self, data:bytes, w_latch:bool):
        if w_latch:
            self.hight = data

        else:
            self.low = data

        # mirror down addr above 0x3fff
        if self.read() > 0x3fff:
            self.write(self.read() & 0x3fff)

        # self.w_latch = not self.w_latch

    def increment(self, inc:bytes):
        lo = self.low
        new_lo = (lo + inc)&0xff
        self.low = new_lo
        
        if lo > new_lo:
            self.hight = (self.hight + 1) & 0xff

        # mirror down addr above 0x3fff
        if self.read() > 0x3fff:
            self.write(self.read() & 0x3fff)

        # self.write(0x2000 + (self.read() + inc) % 0x2000)


#    // 7  bit  0
#    // ---- ----
#    // VPHB SINN
#    // |||| ||||
#    // |||| ||++- Base nametable address
#    // |||| ||    (0 = $2000; 1 = $2400; 2 = $2800; 3 = $2C00)
#    // |||| |+--- VRAM address increment per CPU read/write of PPUDATA
#    // |||| |     (0: add 1, going across; 1: add 32, going down)
#    // |||| +---- Sprite pattern table address for 8x8 sprites
#    // ||||       (0: $0000; 1: $1000; ignored in 8x16 mode)
#    // |||+------ Background pattern table address (0: $0000; 1: $1000)
#    // ||+------- Sprite size (0: 8x8 pixels; 1: 8x16 pixels)
#    // |+-------- PPU master/slave select
#    // |          (0: read backdrop from EXT pins; 1: output color on EXT pins)
#    // +--------- Generate an NMI at the start of the
#    //            vertical blanking interval (0: off; 1: on)

class PPUControlFlags:
    NAMETABLE1              = 0x01
    NAMETABLE2              = 0x02
    VRAM_ADD_INCREMENT      = 0x04
    SPRITE_PATTERN_ADDR     = 0x08
    BACKROUND_PATTERN_ADDR  = 0x10
    SPRITE_SIZE             = 0x20
    MASTER_SLAVE_SELECT     = 0x40
    GENERATE_NMI            = 0x80


class ControlRegister(IORegister):
    NAMETABLE1:bytes = 0
    NAMETABLE2:bytes = 0
    VRAM_ADD_INCREMENT:bytes = 0
    SPRITE_PATTERN_ADDR:bytes = 0
    BACKROUND_PATTERN_ADDR:bytes = 0
    SPRITE_SIZE:bytes = 0
    MASTER_SLAVE_SELECT:bytes = 0
    GENERATE_NMI:bytes = 0

    def read(self,):
        return (self.NAMETABLE1 << 0) | (self.NAMETABLE2 << 1) \
                | (self.VRAM_ADD_INCREMENT << 2) | (self.SPRITE_PATTERN_ADDR << 3) \
                | (self.BACKROUND_PATTERN_ADDR << 4) | (self.SPRITE_SIZE << 5) \
                | (self.MASTER_SLAVE_SELECT << 6) | (self.GENERATE_NMI << 7)


    def write(self, data: bytes):
        self.NAMETABLE1 = (data >> 0) & 0x01
        self.NAMETABLE2 = (data >> 1) & 0x01
        self.VRAM_ADD_INCREMENT = (data >> 2) & 0x01
        self.SPRITE_PATTERN_ADDR = (data >> 3) & 0x01
        self.BACKROUND_PATTERN_ADDR = (data >> 4) & 0x01
        self.SPRITE_SIZE = (data >> 5) & 0x01
        self.MASTER_SLAVE_SELECT = (data >> 6) & 0x01
        self.GENERATE_NMI = (data >> 7) & 0x01

    def get_increment(self)->int:
        return 1 if self.VRAM_ADD_INCREMENT == 0 else 32
    
    def get_nametable_addr(self)->int:
        idx = (self.NAMETABLE2 << 1) | self.NAMETABLE1 
        idx *= 0x400
        return 0x2000 + idx

    def get_sprite_pattern_addr(self)->int:
        return 0x0000 if self.SPRITE_PATTERN_ADDR == 0 else 0x1000

    def get_background_pattern_addr(self)->int:
        return 0x0000 if self.BACKROUND_PATTERN_ADDR == 0 else 0x1000

    def get_sprite_size(self)->int:
        return 8 if self.SPRITE_SIZE == 0 else 16





class MaskRegister(IORegister):
    # 7  bit  0
    # ---- ----
    # BGRs bMmG
    # |||| ||||
    # |||| |||+- Greyscale (0: normal color, 1: produce a greyscale display)
    # |||| ||+-- 1: Show background in leftmost 8 pixels of screen, 0: Hide
    # |||| |+--- 1: Show sprites in leftmost 8 pixels of screen, 0: Hide
    # |||| +---- 1: Show background
    # |||+------ 1: Show sprites
    # ||+------- Emphasize red (green on PAL/Dendy)
    # |+-------- Emphasize green (red on PAL/Dendy)
    # +--------- Emphasize blue
    Greyscale:bytes = 0
    Show_background_left:bytes = 0
    Show_sprites_left:bytes = 0
    Show_background:bytes = 0
    Show_sprites:bytes = 0
    Emphasize_red:bytes = 0
    Emphasize_green:bytes = 0
    Emphasize_blue:bytes = 0

    is_rgb:bool = True

    def read(self,):
        return (self.Greyscale << 0) | (self.Show_background_left << 1) \
                | (self.Show_sprites_left << 2) | (self.Show_background << 3) \
                | (self.Show_sprites << 4) | (self.Emphasize_red << 5) \
                | (self.Emphasize_green << 6) | (self.Emphasize_blue << 7)

    def write(self, data: bytes):
        self.Greyscale = (data >> 0) & 0x01
        self.Show_background_left = (data >> 1) & 0x01
        self.Show_sprites_left = (data >> 2) & 0x01
        self.Show_background = (data >> 3) & 0x01
        self.Show_sprites = (data >> 4) & 0x01
        self.Emphasize_red = (data >> 5) & 0x01
        self.Emphasize_green = (data >> 6) & 0x01
        self.Emphasize_blue = (data >> 7) & 0x01

    def get_color_type(self)->str:
        if self.Greyscale == 0:
            return "rgb" if self.is_rgb else "grb"
        else:
            return "g"
        


class StatusRegister(IORegister):
    # 7  bit  0
    # ---- ----
    # VSO. ....
    # |||| ||||
    # |||+-++++- PPU open bus. Returns stale PPU bus contents.
    # ||+------- Sprite overflow. The intent was for this flag to be set
    # ||         whenever more than eight sprites appear on a scanline, but a
    # ||         hardware bug causes the actual behavior to be more complicated
    # ||         and generate false positives as well as false negatives; see
    # ||         PPU sprite evaluation. This flag is set during sprite
    # ||         evaluation and cleared at dot 1 (the second dot) of the
    # ||         pre-render line.
    # |+-------- Sprite 0 Hit.  Set when a nonzero pixel of sprite 0 overlaps
    # |          a nonzero background pixel; cleared at dot 1 of the pre-render
    # |          line.  Used for raster timing.
    # +--------- Vertical blank has started (0: not in vblank; 1: in vblank).
    #         Set at dot 1 of line 241 (the line *after* the post-render
    #         line); cleared after reading $2002 and at dot 1 of the
    #         pre-render line.

    VBLANK:bytes = 0
    SPRITE_ZERO_HIT:bytes = 0
    SPRITE_OVERFLOW:bytes = 0
    VRAM_WRITE_FLAG:bytes = 1

    def read(self,):
        result = (self.VBLANK << 7) | (self.SPRITE_ZERO_HIT << 6) \
                | (self.SPRITE_OVERFLOW << 5) | (self.VRAM_WRITE_FLAG << 4)
        self.clear_vblank()
        return result
    
    def write(self, data: bytes):
        self.VBLANK = (data >> 7) & 0x01
        self.SPRITE_ZERO_HIT = (data >> 6) & 0x01
        self.SPRITE_OVERFLOW = (data >> 5) & 0x01
        self.VRAM_WRITE_FLAG = (data >> 4) & 0x01

    def clear_vblank(self):
        self.VBLANK = 0

    def set_vblank(self):
        self.VBLANK = 1

    def set_sprite_zero_hit(self):
        self.SPRITE_ZERO_HIT = 1

    def clear_sprite_zero_hit(self):
        self.SPRITE_ZERO_HIT = 0

    def set_sprite_overflow(self):
        self.SPRITE_OVERFLOW = 1

    def clear_sprite_overflow(self):
        self.SPRITE_OVERFLOW = 0


class ScrollRegister:
    x:bytes = 0
    y:bytes = 0
    w:bool = True

    def write(self, data: bytes, addr_status:bool):
        self.w = addr_status
        if addr_status:
            self.x = data
        else:
            self.y = data

        


class PPUInternalRegister():
    v:bytes = 0
    t:bytes = 0
    x:bytes = 0
    w_latch:bool = True




class PPURegisterManager:
    internal_buffer:bytes = 0x00
    internal_reg:PPUInternalRegister = PPUInternalRegister()
    addr_reg:AddressRegister = AddressRegister()
    ctrl_reg:ControlRegister = ControlRegister()
    mask_reg:MaskRegister = MaskRegister()
    status_reg:StatusRegister = StatusRegister()
    scroll_reg:bytearray = bytearray(2)
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
            self.mask_reg.write(data)
        elif address == 0x2002:
            # Status Register
            LOGGER.warn(f"PPURegisterManager: Attempt to write to PPU Status Register at {address:04X}, it will be ignored")
        elif address == 0x2003:
            # OAM Address Register
            self.oam_addr_reg = data
        elif address == 0x2004:
            # OAM Data Register
            self.oam_data[self.oam_addr_reg] = data
            self.oam_addr_reg += 1
            self.oam_addr_reg %= 256
        elif address == 0x2005:
            # Scroll Register
            # share address register state
            if self.internal_reg.w_latch:
                self.scroll_reg[0] = data
            else:
                self.scroll_reg[1] = data
            self.update_w_latch()

        elif address == 0x2006:
            # PPU Address Register

            self.addr_reg.update(data, self.internal_reg.w_latch)
            self.update_w_latch()

        elif address == 0x2007:
            # PPU Data Register
            addr = self.addr_reg.read()
            self.addr_reg.increment(self.ctrl_reg.get_increment())
            self.ppu_bus.write_byte(addr, data)
        elif address == 0x4014:
            # OAM DMA

            for i in range(256):
                addr = (self.oam_addr_reg + i)%256
                self.oam_data[addr] = data[i]
        else:
            raise ValueError(f"Invalid PPU Register Address: {address}")
        
    def update_w_latch(self):
        self.internal_reg.w_latch = not self.internal_reg.w_latch


