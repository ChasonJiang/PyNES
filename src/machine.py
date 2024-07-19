



import time
import traceback
from typing import Callable

from .interface import ControllerButton

from .controller import Controller

from .frame import NPFrame

from .displayer import Displayer

from .ppu import PPU
from .bus import CPUBus, PPUBus
from .cartridge import Cartridge
from .cpu import CPU, CPUHookType
from .memory import Memory
import pygame
import keyboard
import logging
LOGGER = logging.getLogger(__name__)

KEY_STATUS = {
    "keys":{    
        "w": False,
        "a": False,
        "s": False,
        "d": False,
        "u": False,
        "i": False,
        "j": False,
        "k": False
    },
    "pressed": False
}
def key_down_callback(key:str):
    KEY_STATUS["keys"][key] = True
    KEY_STATUS["pressed"] = True


KEY_MAP = {
    "w": "UP",
    "a": "LEFT",
    "s": "DOWN",
    "d": "RIGHT",
    "u": "A",
    "i": "B",
    "j": "SELECT",
    "k": "START"
}

KEY_FLAGS={
    "A": 0b10000000,
    "B": 0b01000000,
    "SELECT": 0b00100000,
    "START": 0b00010000,
    "UP": 0b00001000,
    "DOWN": 0b00000100,
    "LEFT": 0b00000010,
    "RIGHT": 0b00000001
}


keyboard.add_hotkey('w', key_down_callback, args=("w",))
keyboard.add_hotkey('a', key_down_callback, args=("a",))
keyboard.add_hotkey('s', key_down_callback, args=("s",))
keyboard.add_hotkey('d', key_down_callback, args=("d",))
keyboard.add_hotkey('u', key_down_callback, args=("u",))
keyboard.add_hotkey('i', key_down_callback, args=("i",))
keyboard.add_hotkey('j', key_down_callback, args=("j",))
keyboard.add_hotkey('k', key_down_callback, args=("k",))


CPU_MEMORY_SIZE = 2*1024  # 2KB of RAM for the CPU
PPU_MEMORY_SIZE = 2*1024  # 2KB of VRAM for the PPU

NTSC_CPU_CLOCK_FREQ = 1876951  # NTSC CPU clock frequency in Hz
PAL_CPU_CLOCK_FREQ = 1740636  # PAL CPU clock frequency in Hz

class Machine:
    def __init__(self, cartridge: Cartridge = None):
        self.is_ntsc: bool = True   
        self.machine_status: dict = {
            "is_running":False
        }

        self.displayer:Displayer = Displayer()

        self.ppu_memory = Memory(PPU_MEMORY_SIZE)
        self.ppu_palette_index_memory = Memory(32)
        self.ppu_bus = PPUBus(self.ppu_memory, self.ppu_palette_index_memory)
        self.ppu = PPU(self.ppu_bus)
        # self.ppu.register_renderer(self.displayer.render)

        self.cpu_memory = Memory(CPU_MEMORY_SIZE)
        self.cpu_bus = CPUBus(self.cpu_memory, self.ppu.reg_manager)
        self.cpu = CPU(self.cpu_bus)

        self.controller = Controller()

        self.cartridge: Cartridge = None
        self.set_cartridge(cartridge)

        # Notify the CPU trigger NMI from the PPU
        self.ppu.register_cpu_nmi(self.cpu.set_nmi)
        # Notify the PPU about the CPU's defer cycles
        self.cpu.register_hook(CPUHookType.AFTER_EXEC, lambda cpu: self.ppu.set_cpu_defer_cycles(cpu.defer_cycles))

        self.window = pygame.display.set_mode((256, 240))
        pygame.display.set_caption("PyNES")

        def render_callback(npframe:NPFrame, window: pygame.Surface):
            frame_surface = pygame.surfarray.make_surface(npframe.data.transpose(1,2,0))
            window.blit(frame_surface, (0, 0))
            pygame.display.flip()
            # pass
        self.ppu.register_renderer(render_callback, (self.window,))

        def shutdown_callback(cpu:CPU, machine_status: dict):
            machine_status["is_running"] = False

        self.cpu.register_hook(CPUHookType.ON_SHUTDOWN, shutdown_callback, (self.machine_status, ))
        
        def key_callback(cpu:CPU, key_status:dict, controller:Controller):
            key = 0
            if key_status["pressed"]:
                for key_name, is_pressed in key_status["keys"].items():
                    if is_pressed:
                        key |= KEY_FLAGS[KEY_MAP[key_name]]
                        key_status["keys"][key_name] = False
                        # print(f"Pressed {key_name}")
                    else:
                        key &= ~KEY_FLAGS[KEY_MAP[key_name]]
                controller.data = key
            key_status["pressed"] = False
            # self.cpu.bus.write_byte(0x4016, key)

        self.cpu_bus.register_controller(self.controller)
        # self.hook_keys(self.controller)
        self.cpu.register_hook(CPUHookType.BEFORE_EXEC,key_callback, args=(KEY_STATUS, self.controller))
        self.cpu.hook_enable(True)
    
    def hook_keys(self, ):
        def key_down_callback(key:keyboard.KeyboardEvent):
            key = key.name.lower()
            # print(f"Pressed {key}")
            KEY_STATUS["keys"][key] = True
            # KEY_STATUS["pressed"] = True
            # if key == "w":
            #     controller.update(ControllerButton.UP,True)
            # elif key == "a":
            #     controller.update(ControllerButton.LEFT,True)
            # elif key == "s":
            #     controller.update(ControllerButton.DOWN,True)
            # elif key == "d":
            #     controller.update(ControllerButton.RIGHT,True)
            # elif key == "j":
            #     controller.update(ControllerButton.A,True)
            # elif key == "k":
            #     controller.update(ControllerButton.B,True)
            # elif key == "u":
            #     controller.update(ControllerButton.SELECT,True)
            # elif key == "i":
            #     controller.update(ControllerButton.START,True)

        def key_up_callback(key:keyboard.KeyboardEvent):
            key = key.name.lower()
            # print(f"Released {key}")
            KEY_STATUS["keys"][key] = False
            for key_name, is_pressed in KEY_STATUS["keys"].items():
                if is_pressed:
                    return
            KEY_STATUS["pressed"] = False
            # if key == "w":
            #     controller.update(ControllerButton.UP,False)
            # elif key == "a":
            #     controller.update(ControllerButton.LEFT,False)
            # elif key == "s":
            #     controller.update(ControllerButton.DOWN,False)
            # elif key == "d":
            #     controller.update(ControllerButton.RIGHT,False)
            # elif key == "j":
            #     controller.update(ControllerButton.A,False)
            # elif key == "k":
            #     controller.update(ControllerButton.B,False)
            # elif key == "u":
            #     controller.update(ControllerButton.SELECT,False)
            # elif key == "i":
            #     controller.update(ControllerButton.START,False)


        keyboard.on_press(key_down_callback)
        keyboard.on_release(key_up_callback)
        # keyboard.add_hotkey('w', key_down_callback, args=("w",))
        # keyboard.add_hotkey('a', key_down_callback, args=("a",))
        # keyboard.add_hotkey('s', key_down_callback, args=("s",))
        # keyboard.add_hotkey('d', key_down_callback, args=("d",))
        # keyboard.add_hotkey('u', key_down_callback, args=("u",))
        # keyboard.add_hotkey('i', key_down_callback, args=("i",))
        # keyboard.add_hotkey('j', key_down_callback, args=("j",))
        # keyboard.add_hotkey('k', key_down_callback, args=("k",))


    def hook_enable(self, enable: bool):
        self.cpu.hook_enable(enable)
        
    def reset(self, start_address: int = None):
        self.cpu.reset(start_address)

    def debug_step(self):
        if self.cartridge is None:
            raise Exception("No cartridge loaded")
        self.cpu.clock(True)
        self.ppu.clock()

    def run(self):
        # pygame.init()
        start_time = time.perf_counter_ns()
        cycle_time = round(1000_000_000/NTSC_CPU_CLOCK_FREQ if self.is_ntsc else 1000_000_000/PAL_CPU_CLOCK_FREQ)
        self.machine_status["is_running"] = True
        try:
            delay_time = 0
            while self.machine_status["is_running"]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.machine_status["is_running"] = False
                # running_time = time.perf_counter_ns() - start_time
                # if cycle_time > running_time + delay_time:
                #     LOGGER.debug("Machine: Waiting for next cycle")
                #     # print(f"{cycle_time-(time.perf_counter_ns() - start_time):<8d}",end="\r")
                #     continue
                # else:
                #     if running_time > cycle_time:
                #         delay_time = running_time - cycle_time
                #     else:
                #         delay_time = 0
                    # print(f"{cycle_time-(time.perf_counter_ns() - start_time):<8d}",end="\r")



                start_time = time.perf_counter_ns()
                self.cpu.clock()
                self.ppu.clock()
        except:
            traceback.print_exc()
            pygame.quit()
        finally:
            pygame.quit()

    def set_cartridge(self, cartridge: Cartridge):
        self.cartridge = cartridge
        self.is_ntsc = self.cartridge.rom.header.video_mode == 0
        self.cpu_bus.set_cartridge(cartridge)
        self.ppu_bus.set_cartridge(cartridge)
        self.cpu.reset()
        

    def register_cpu_hook(self, hook_type: CPUHookType, func: Callable, args: tuple = (), kwargs: dict = {}):
        self.cpu.register_hook(hook_type, func, args, kwargs)

    def unregister_cpu_hook(self, hook_type: CPUHookType, func: Callable):
        self.cpu.unregister_hook(hook_type, func)
