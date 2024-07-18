






from abc import ABC
from functools import lru_cache
from typing import Callable, Dict, List, Tuple

from .palette import STANDARD_PALETTE

from .frame import NPFrame

from .interface import IPPU, IBus
from .io_register import PPURegisterManager
import logging

LOGGER = logging.getLogger(__name__)

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
        self.render()
        if self.renderers != {}:
            for renderer, args, kwargs in self.renderers.values():
                renderer(self.current_frame, *args, **kwargs)
        else:
            raise ValueError("Renderer is not registered")


    def render(self):
        self.current_frame = NPFrame()
        self.render_background()
        self.render_sprite()


    def _get_bg_palette(self, nametable_base_addr:int, tile_x:int, tile_y:int, view_port_offset_x:int=0, view_port_offset_y:int=0):
        tile_offset_x = view_port_offset_x//8
        tile_offset_y = view_port_offset_y//8
        attr_idx = 0
        is_horizontal_mirror = self.bus.is_horizontal_mirror
        if not is_horizontal_mirror:
            if 31 - tile_offset_x >= tile_x:
                attr_idx = (tile_y // 4)  * 8 + ((tile_x + tile_offset_x) // 4)
            else:
                tile_x = (tile_x -(31 - tile_offset_x))
                attr_idx = (tile_y // 4)  * 8 + (tile_x // 4) + 0x400
        else:
            if 29 - tile_offset_y >= tile_y:
                attr_idx = ((tile_y + tile_offset_y) // 4)  * 8 + (tile_x // 4)

            else:
                tile_y = (tile_y + tile_offset_y - 29)
                attr_idx = ((tile_y // 4)  * 8 + (tile_x // 4)) + 0x400
        attr = self.bus.read_byte(nametable_base_addr + 0x3C0 + attr_idx)


        palette_idx = 0x00
        match (tile_y % 4 // 2, tile_x % 4 // 2):
            case (0, 0):
                palette_idx = (attr >> 0) & 0x03
            case (0, 1):
                palette_idx = (attr >> 2) & 0x03
            case (1, 0):
                palette_idx = (attr >> 4) & 0x03
            case (1, 1):
                palette_idx = (attr >> 6) & 0x03

        
        palette_start_addr = 0x3F00 + palette_idx*4

        return self._get_palette(palette_start_addr)
        

    def _get_palette(self, base_addr:int) -> List[Tuple[int,int,int]]:
        color_idx = [self.bus.read_byte(base_addr + i) if i!=0 else self.bus.read_byte(0x3F00) for i in range(4)]
        palette = [STANDARD_PALETTE[i] for i in color_idx]
        return palette
    
    # @lru_cache(maxsize=1024)
    def tile_pos_to_tile_idx(self, tile_x:int, tile_y:int, view_port_offset_x:int=0, view_port_offset_y:int=0):
        # tile_idx = (tile_y + view_port_offset_y//8 ) * 32 + (tile_x + view_port_offset_x//8)
        # return tile_idx
        
        tile_offset_x = view_port_offset_x//8
        tile_offset_y = view_port_offset_y//8
        tile_idx = 0
        is_next_nametable = False
        is_horizontal_mirror = self.bus.is_horizontal_mirror
        if not is_horizontal_mirror:
            if 31 - tile_offset_x >= tile_x:
                tile_idx = tile_y * 32 + (tile_x + tile_offset_x)
            else:
                tile_idx = tile_y * 32 + (tile_x -(31 - tile_offset_x)) + 0x400
                is_next_nametable = True
        else:
            if 29 - tile_offset_y >= tile_y:
                tile_idx = (tile_y + tile_offset_y) * 32 + tile_x
            else:
                tile_idx = (tile_y + tile_offset_y - 29) * 32 + tile_x + 0x400
                is_next_nametable = True

        return tile_idx, is_next_nametable

    # @lru_cache(maxsize=960)
    def tile_idx_to_tile_pos(self, tile_idx:int):
        tile_x = tile_idx % 32
        tile_y = tile_idx // 32
        return (tile_x, tile_y)


    def render_background(self):
        pattern_base_addr = self.reg_manager.ctrl_reg.get_background_pattern_addr()
        nametable_base_addr = self.reg_manager.ctrl_reg.get_nametable_addr()

        view_port_offset_x = self.reg_manager.scroll_reg[0]
        view_port_offset_y = self.reg_manager.scroll_reg[1]
        
        for offset in range(960):
            # Get Tile Index from Nametable
            tile_x, tile_y = self.tile_idx_to_tile_pos(offset)
            tile_idx, is_next_nametable = self.tile_pos_to_tile_idx(tile_x, tile_y, view_port_offset_x, view_port_offset_y)
            tile_addr = nametable_base_addr + tile_idx
            pattern_idx = self.bus.read_byte(tile_addr)

            # Get Tile Data from Pattern Table
            tile = [self.bus.read_byte(pattern_base_addr + (pattern_idx * 16 + f)) for f in range(16)]

            palette = self._get_bg_palette(nametable_base_addr, tile_x, tile_y,view_port_offset_x, view_port_offset_y)
            
            # Render Tile
            for y in range(8):
                # TODO: check this
                high_byte = tile[y]
                low_byte = tile[y+8]

                for x in range(8):
                    low_bit = (high_byte >> (7-x)) & 0x01
                    high_bit = (low_byte >> (7-x)) & 0x01
                    color_idx = (high_bit << 1) | low_bit
                    color = palette[color_idx]

                    self.current_frame.set_pixel(tile_x * 8  +x, tile_y * 8+y, color)

    def render_sprite(self):
        pattern_base_addr = self.reg_manager.ctrl_reg.get_sprite_pattern_addr()
        # nametable_base_addr = self.reg_manager.ctrl_reg.get_nametable_addr()

        for sprite_idx in range(64):
            tile_y = self.reg_manager.oam_data[sprite_idx*4]
            tile_x = self.reg_manager.oam_data[sprite_idx*4+3]
            pattern_idx = self.reg_manager.oam_data[sprite_idx*4+1]
            attr = self.reg_manager.oam_data[sprite_idx*4+2]
            flip_h = (attr >> 6) & 0x01 == 1
            flip_v = (attr >> 7) & 0x01 == 1
            # prio = (attr >> 5) & 0x01

            tile = [self.bus.read_byte(pattern_base_addr + (pattern_idx * 16 + f)) for f in range(16)]
            palette_idx = attr & 0b11
            palette_start_addr = 0x3F10 + palette_idx*4
            palette = self._get_palette(palette_start_addr)

            # Render Tile
            for y in range(8):
                # TODO: check this
                high_byte = tile[y]
                low_byte = tile[y+8]
                for x in range(8):
                    low_bit = (high_byte >> (7-x)) & 0x01
                    high_bit = (low_byte >> (7-x)) & 0x01
                    color_idx = (high_bit << 1) | low_bit

                    color = palette[color_idx]
                    pos_x = 0
                    pos_y = 0
    
                    match (flip_h, flip_v):
                        case (False, False):
                           
                           pos_x = tile_x + x
                           pos_y = tile_y + y
                        case (True, False):
                            # self.current_frame.set_pixel(tile_x+7-x, tile_y+y, color)
                            pos_x = tile_x + 7 - x
                            pos_y = tile_y + y
                        case (False, True):
                            # self.current_frame.set_pixel(tile_x+x, tile_y+7-y, color)
                            pos_x = tile_x + x
                            pos_y = tile_y + 7 - y
                        case (True, True):
                            # self.current_frame.set_pixel(tile_x+7-x, tile_y+7-y, color)
                            pos_x = tile_x + 7 - x
                            pos_y = tile_y + 7 - y

                    if pos_x >= 0 and pos_x < 256 and pos_y >= 0 and pos_y < 240:
                        self.current_frame.set_pixel(pos_x, pos_y, color)
    

                    
