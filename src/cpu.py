






from abc import ABC
from enum import Enum
from typing import List, Tuple

from .decoder import Decoder

from .bus import CPUBus
from .executor import Executor
from .interface import ICPU, Flags, Register
from .instruction import INSTRUCTION_TABLE, Instruction

import logging

LOGGER = logging.getLogger(__name__)






class CPUHookType(Enum):
    STATUS = 1
    BEFORE_EXEC = 2
    AFTER_EXEC= 3
    ON_SHUTDOWN = 4


class CPU(ICPU):
    NMI_ADDR = 0XFFFA
    REST_ADDR = 0XFFFC
    IRQ_ADDR = 0XFFFE
    def __init__(self, bus: CPUBus):
        self.regs: Register = Register()
        self.bus: CPUBus = bus
        self.cycles: int = 0
        self.defer_cycles: int = 0
        self.decoder = Decoder(self)
        self.executor = Executor(self)
        self.current_instruction: Instruction = None

        self._status_hook_func: dict = {}
        self._before_exec_hook_func: dict = {}
        self._after_exec_hook_func: dict = {}
        self._shutdown_hook_func: dict = {}

        self.nmi_enabled: bool = False
        self.irq_enabled: bool = False

        self.hook_enabled: bool = False


    def hook_enable(self, enable:bool):
        self.hook_enabled = enable

    def push_byte(self, data:bytes):
        addr = self.regs.SP + 0x100
        if addr < 0x100:
            raise RuntimeError("Stack overflow")
        self.bus.write_byte(addr, data)
        self.regs.SP -= 1

    def pop_byte(self) -> bytes:
        self.regs.SP += 1
        addr = self.regs.SP + 0x100
        if addr > 0x1FF:
            raise RuntimeError("Stack underflow")
        data = self.bus.read_byte(addr) 
        return data
    
    def push_word(self, data:int):
        # high byte first (little-endian)
        self.push_byte((data >> 8) & 0xFF)
        self.push_byte(data & 0xFF)
        

    def pop_word(self) -> int:
        lo = self.pop_byte()
        hi = self.pop_byte()
        return (hi << 8) | lo

    def irq(self):
        if self.regs.P & Flags.I != 0:
            return
        
        self.push_word(self.regs.PC)
        self.push_byte((self.regs.P | Flags.U) & ~Flags.B)

        self.regs.P |= Flags.I
        self.regs.PC = self.bus.read_word(self.IRQ_ADDR)
        self.defer_cycles += 7

    def nmi(self):
        self.push_word(self.regs.PC)
        self.push_byte((self.regs.P | Flags.U) & ~Flags.B)

        self.regs.P |= Flags.I
        self.regs.PC = self.bus.read_word(self.NMI_ADDR)
        self.defer_cycles += 7

    def reset(self, start_addr:int=None):
        self.regs.A = 0
        self.regs.X = 0
        self.regs.Y = 0
        self.regs.SP = 0xFD
        self.regs.P = Flags.I | Flags.U
        self.regs.PC = self.bus.read_word(self.REST_ADDR) if start_addr is None else start_addr
        self.defer_cycles = 7
        self.cycles = 0        

    def set_nmi(self,):
        self.nmi_enabled = True
    
    def set_irq(self,):
        self.irq_enabled = True

    def clock(self, debug:bool=False):
        
        if debug:
            if self.defer_cycles !=0:
                self.cycles += self.defer_cycles
                self.defer_cycles = 0
                
        
        if self.defer_cycles == 0:
            self.cycle()
        else:
            self.defer_cycles -= 1
        self.cycles += 1
    
    def cycle(self,):
        if self.nmi_enabled:
            self.nmi()
            self.nmi_enabled = False
        elif self.irq_enabled:
            self.irq()
            self.irq_enabled = False

        opcode:bytes = self.fetch()
        self.current_instruction = self.decode(opcode)

        if self.hook_enabled:
            self._call_before_exec_hook()
            self._call_status_hook()
        self.log()
        self.execute(self.current_instruction)

        if self.hook_enabled:
            self._call_after_exec_hook()



    def fetch(self) -> bytes:
        if self.regs.PC > 0xFFFF:
            raise RuntimeError("CPU: PC out of range")
        opcode:bytes = self.bus.read_byte(self.regs.PC)
        self.regs.PC += 1

            # self.regs.PC &= 0xFFFF
        return opcode

    def decode(self, opcode:bytes) -> Instruction:
        return self.decoder.decode(opcode)
    
    def execute(self, ins:Instruction):
        self.executor.execute(ins)

    def get_status(self) -> dict:
        return {
            "address": self.regs.PC-self.current_instruction.length,
            "instruction": self.current_instruction,
            "A": self.regs.A,
            "X": self.regs.X,
            "Y": self.regs.Y,
            "P": self.regs.P,
            "SP": self.regs.SP,
            "CYC": self.cycles
        }
    
    def register_hook(self, hook_type:CPUHookType, func, args:Tuple=(), kwargs:dict={}):
        if hook_type == CPUHookType.STATUS:
            self._status_hook_func[func.__name__] = (func, args, kwargs)
        elif hook_type == CPUHookType.BEFORE_EXEC:
            self._before_exec_hook_func[func.__name__] = (func, args, kwargs)
        elif hook_type == CPUHookType.AFTER_EXEC:
            self._after_exec_hook_func[func.__name__] = (func, args, kwargs)
        elif hook_type == CPUHookType.ON_SHUTDOWN:
            self._shutdown_hook_func[func.__name__] = (func, args, kwargs)
        else:
            raise ValueError("Invalid hook type")

    def _call_status_hook(self):
        for func, args, kwargs in self._status_hook_func.values():
            func(self.get_status(), *args, **kwargs)

    def _call_before_exec_hook(self):
        for func, args, kwargs in self._before_exec_hook_func.values():
            func(self, *args, **kwargs)

    def _call_after_exec_hook(self):
        for func, args, kwargs in self._after_exec_hook_func.values():
            func(self, *args, **kwargs)

    def _call_shutdown_hook(self):
        self.reset()
        for func, args, kwargs in self._shutdown_hook_func.values():
            func(self, *args, **kwargs)


    def unregister_hook(self, hook_type:CPUHookType, func):
        if hook_type == CPUHookType.STATUS:
            self._status_hook_func.pop(func.__name__, None)
        elif hook_type == CPUHookType.BEFORE_EXEC:
            self._before_exec_hook_func.pop(func.__name__, None)
        elif hook_type == CPUHookType.AFTER_EXEC:
            self._after_exec_hook_func.pop(func.__name__, None)
        else:
            raise ValueError("Invalid hook type")
        
    def log(self,):
        status = self.get_status()
        address = status['address']
        instrucion = status['instruction']
        A = status['A']
        X = status['X']
        Y = status['Y']
        P = status['P']
        SP = status['SP']
        CYC = status['CYC']

        operand = ""
        if instrucion.length > 1:
            if instrucion.addr is None and instrucion.data is not None:
                operand = f"#${instrucion.data:04X}"
            else:
                operand = f"${instrucion.addr:04X}"

        LOGGER.debug(f"CPU: {address:04X}\t{instrucion.mnemonic:<4} {operand:<10} A:{A:02X} X:{X:02X} Y:{Y:02X} P:{P:02X} SP:{SP:02X} CYC:{CYC}")
