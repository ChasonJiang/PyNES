





from typing import Tuple
from .interface import ICPU
from .instruction import INSTRUCTION_TABLE, AddressingMethod, Instruction



class Decoder:
    def __init__(self, cpu: ICPU):
        self.cpu = cpu
        # self.ins = Instruction(0x00)

    def decode(self, opcode:bytes):
        ins:Instruction = Instruction(opcode)
        # self.ins.reset()
        # ins = self.ins
        ins.opcode = opcode
        instruction_info = INSTRUCTION_TABLE.get(opcode, None)
        if instruction_info is None:
            raise RuntimeError(f"Unknown instruction: {hex(ins.opcode)}")
        
        ins.instruction_info = instruction_info
        ins.mnemonic = ins.instruction_info[0]
        ins.addressing_method = ins.instruction_info[1]
        ins.length = ins.instruction_info[2]
        ins.cycles = ins.instruction_info[3]
        
        operand_len = ins.length - 1

        if operand_len == 1:
            ins.operand1 = self.cpu.bus.read_byte(self.cpu.regs.PC)
            self.cpu.regs.PC += 1

        elif operand_len == 2:
            ins.operand1 = self.cpu.bus.read_byte(self.cpu.regs.PC)
            self.cpu.regs.PC += 1
            ins.operand2 = self.cpu.bus.read_byte(self.cpu.regs.PC)
            self.cpu.regs.PC += 1

        ins.data, ins.addr = self.addressing(self.cpu, ins)

        return ins
    


    def addressing(self,cpu: ICPU, ins: Instruction) -> Tuple[int|bytes, int|None]:
        data = None
        addr = None
        match ins.addressing_method:
            case AddressingMethod.imp:
                data = None
                addr = None
            case AddressingMethod.acc:
                data = cpu.regs.A
            case AddressingMethod.imm:
                data = ins.operand1
            case AddressingMethod.zp:
                addr = ins.operand1 % 0x0100
                # data = cpu.bus.read_byte(addr % 0x0100) # It's 6502 bug, it should be addr % 0x0100
            case AddressingMethod.zpx:
                addr = (ins.operand1 + cpu.regs.X) & 0xFF
                # data = cpu.bus.read_byte(addr % 0x0100) # It's 6502 bug, it should be addr % 0x0100
            case AddressingMethod.zpy:
                addr = (ins.operand1 + cpu.regs.Y) & 0xFF
                # data = cpu.bus.read_byte(addr % 0x0100) # It's 6502 bug, it should be addr % 0x0100
            case AddressingMethod.rel:
                if ins.operand1 & 0x80:
                    addr = (cpu.regs.PC + (ins.operand1 & 0x7F) - 0x80)
                else:
                    addr = cpu.regs.PC + ins.operand1
                addr &= 0xFFFF
                # data = cpu.bus.read_byte(addr)
            case AddressingMethod.abs:
                addr = (ins.operand2 << 8) | ins.operand1
                addr &= 0xFFFF
                # data = cpu.bus.read_byte(addr)
            case AddressingMethod.abx:
                addr = ((ins.operand2 << 8) | ins.operand1) + cpu.regs.X
                addr &= 0xFFFF
                # data = cpu.bus.read_byte(addr & 0xFFFF)
            case AddressingMethod.aby:
                addr = ((ins.operand2 << 8) | ins.operand1) + cpu.regs.Y
                addr &= 0xFFFF
                # data = cpu.bus.read_byte(addr & 0xFFFF)
            case AddressingMethod.ind:
                addr = (ins.operand2 << 8) | ins.operand1

                ## to emulate 6502 bug
                lo = cpu.bus.read_byte(addr)
                hi = cpu.bus.read_byte((addr & 0xFF00) | ((addr + 1) & 0xFF))
                addr = (hi << 8) | lo
                addr &= 0xFFFF
                # data = cpu.bus.read_byte(addr)

            case AddressingMethod.izx:

                _addr = (ins.operand1 + cpu.regs.X) % 0x0100
                lo = cpu.bus.read_byte(_addr)
                hi = cpu.bus.read_byte((_addr & 0xFF00) | ((_addr + 1) & 0xFF))
                addr = (hi << 8) | lo
                addr &= 0xFFFF

                # data = cpu.bus.read_byte(addr)
            case AddressingMethod.izy:

                _addr = ins.operand1
                lo = cpu.bus.read_byte(_addr)
                hi = cpu.bus.read_byte((_addr & 0xFF00) | ((_addr + 1) & 0xFF))
                _addr = (hi << 8) | lo
                addr = _addr + cpu.regs.Y
                addr &= 0xFFFF

                # data = cpu.bus.read_byte(addr)
            case _:
                raise ValueError("Invalid addressing method")
            
        return data, addr
