



from enum import Enum
from typing import Tuple


class AddressingMethod(Enum):
    imp:str = ""
    acc:str = "A"
    imm:str = "#$00"
    zp:str = "$00"
    zpx:str = "$00,X"
    zpy:str = "$00,Y"
    izx:str = "($00,X)"
    izy:str = "($00),Y"
    abs:str = "$0000"
    abx:str = "$0000,X"
    aby:str = "$0000,Y"
    ind:str = "($0000)"
    rel:str = "$0000 (PC-relative)"


class Mnemonic(Enum):
    ADC:str = "ADC"
    AND:str = "AND"
    ASL:str = "ASL"
    BCC:str = "BCC"
    BCS:str = "BCS"
    BEQ:str = "BEQ"
    BIT:str = "BIT"
    BMI:str = "BMI"
    BNE:str = "BNE"
    BPL:str = "BPL"
    BRK:str = "BRK"
    BVC:str = "BVC"
    BVS:str = "BVS"
    CLC:str = "CLC"
    CLD:str = "CLD"
    CLI:str = "CLI"
    CLV:str = "CLV"
    CMP:str = "CMP"
    CPX:str = "CPX"
    CPY:str = "CPY"
    DEC:str = "DEC"
    DEX:str = "DEX"
    DEY:str = "DEY"
    EOR:str = "EOR"
    INC:str = "INC"
    INX:str = "INX"
    INY:str = "INY"
    JMP:str = "JMP"
    JSR:str = "JSR"
    LDA:str = "LDA"
    LDX:str = "LDX"
    LDY:str = "LDY"
    LSR:str = "LSR"
    NOP:str = "NOP"
    ORA:str = "ORA"
    PHA:str = "PHA"
    PHP:str = "PHP"
    PLA:str = "PLA"
    PLP:str = "PLP"
    ROL:str = "ROL"
    ROR:str = "ROR"
    RTI:str = "RTI"
    RTS:str = "RTS"
    SBC:str = "SBC"
    SEC:str = "SEC"
    SED:str = "SED"
    SEI:str = "SEI"
    STA:str = "STA"
    STX:str = "STX"
    STY:str = "STY"
    TAX:str = "TAX"
    TAY:str = "TAY"
    TSX:str = "TSX"
    TXA:str = "TXA"
    TXS:str = "TXS"
    TYA:str = "TYA"
    


INSTRUCTION_TABLE = {
    # opcodes: (mnemonic, addressing_method, bytes, cycles)
    0x69: ("ADC", AddressingMethod.imm, 2, (2, 0)),
    0x65: ("ADC", AddressingMethod.zp, 2, (3, 0)),
    0x75: ("ADC", AddressingMethod.zpx, 2, (4, 0)),
    0x6D: ("ADC", AddressingMethod.abs, 3, (4, 0)),
    0x7D: ("ADC", AddressingMethod.abx, 3, (4, 1)),
    0x79: ("ADC", AddressingMethod.aby, 3, (4, 1)),
    0x61: ("ADC", AddressingMethod.izx, 2, (6, 0)),
    0x71: ("ADC", AddressingMethod.izy, 2, (5, 1)),

    0x29: ("AND", AddressingMethod.imm, 2, (2, 0)),
    0x25: ("AND", AddressingMethod.zp, 2, (3, 0)),
    0x35: ("AND", AddressingMethod.zpx, 2, (4, 0)),
    0x2D: ("AND", AddressingMethod.abs, 3, (4, 0)),
    0x3D: ("AND", AddressingMethod.abx, 3, (4, 1)),
    0x39: ("AND", AddressingMethod.aby, 3, (4, 1)),
    0x21: ("AND", AddressingMethod.izx, 2, (6, 0)),
    0x31: ("AND", AddressingMethod.izy, 2, (5, 1)),

    0x0A: ("ASL", AddressingMethod.acc, 1, (2, 0)),
    0x06: ("ASL", AddressingMethod.zp, 2, (5, 0)),
    0x16: ("ASL", AddressingMethod.zpx, 2, (6, 0)),
    0x0E: ("ASL", AddressingMethod.abs, 3, (6, 0)),
    0x1E: ("ASL", AddressingMethod.abx, 3, (7, 0)),

    0x90: ("BCC", AddressingMethod.rel, 2, (2, 1, 2)),

    0xB0: ("BCS", AddressingMethod.rel, 2, (2, 1, 2)),

    0xF0: ("BEQ", AddressingMethod.rel, 2, (2, 1, 2)),

    0x24: ("BIT", AddressingMethod.zp, 2, (3, 0)),
    0x2C: ("BIT", AddressingMethod.abs, 3, (4, 0)),

    0x30: ("BMI", AddressingMethod.rel, 2, (2, 1, 2)),

    0xD0: ("BNE", AddressingMethod.rel, 2, (2, 1, 2)),

    0x10: ("BPL", AddressingMethod.rel, 2, (2, 1, 2)),

    0x00: ("BRK", AddressingMethod.imp, 1, (7, 0)),

    0x50: ("BVC", AddressingMethod.rel, 2, (2, 1, 2)),

    0x70: ("BVS", AddressingMethod.rel, 2, (2, 1, 2)),

    0x18: ("CLC", AddressingMethod.imp, 1, (2, 0)),

    0xD8: ("CLD", AddressingMethod.imp, 1, (2, 0)),

    0x58: ("CLI", AddressingMethod.imp, 1, (2, 0)),

    0xB8: ("CLV", AddressingMethod.imp, 1, (2, 0)),

    0xC9: ("CMP", AddressingMethod.imm, 2, (2, 0)),
    0xC5: ("CMP", AddressingMethod.zp, 2, (3, 0)),
    0xD5: ("CMP", AddressingMethod.zpx, 2, (4, 0)),
    0xCD: ("CMP", AddressingMethod.abs, 3, (4, 0)),
    0xDD: ("CMP", AddressingMethod.abx, 3, (4, 1)),
    0xD9: ("CMP", AddressingMethod.aby, 3, (4, 1)),
    0xC1: ("CMP", AddressingMethod.izx, 2, (6, 0)),
    0xD1: ("CMP", AddressingMethod.izy, 2, (5, 1)),

    0xE0: ("CPX", AddressingMethod.imm, 2, (2, 0)),
    0xE4: ("CPX", AddressingMethod.zp, 2, (3, 0)),
    0xEC: ("CPX", AddressingMethod.abs, 3, (4, 0)),

    0xC0: ("CPY", AddressingMethod.imm, 2, (2, 0)),
    0xC4: ("CPY", AddressingMethod.zp, 2, (3, 0)),
    0xCC: ("CPY", AddressingMethod.abs, 3, (4, 0)),

    0xC6: ("DEC", AddressingMethod.zp, 2, (5, 0)),
    0xD6: ("DEC", AddressingMethod.zpx, 2, (6, 0)),
    0xCE: ("DEC", AddressingMethod.abs, 3, (6, 0)),
    0xDE: ("DEC", AddressingMethod.abx, 3, (7, 0)),

    0xCA: ("DEX", AddressingMethod.imp, 1, (2, 0)),

    0x88: ("DEY", AddressingMethod.imp, 1, (2, 0)),

    0x49: ("EOR", AddressingMethod.imm, 2, (2, 0)),
    0x45: ("EOR", AddressingMethod.zp, 2, (3, 0)),
    0x55: ("EOR", AddressingMethod.zpx, 2, (4, 0)),
    0x4D: ("EOR", AddressingMethod.abs, 3, (4, 0)),
    0x5D: ("EOR", AddressingMethod.abx, 3, (4, 1)),
    0x59: ("EOR", AddressingMethod.aby, 3, (4, 1)),
    0x41: ("EOR", AddressingMethod.izx, 2, (6, 0)),
    0x51: ("EOR", AddressingMethod.izy, 2, (5, 1)),

    0xE6: ("INC", AddressingMethod.zp, 2, (5, 0)),
    0xF6: ("INC", AddressingMethod.zpx, 2, (6, 0)),
    0xEE: ("INC", AddressingMethod.abs, 3, (6, 0)),
    0xFE: ("INC", AddressingMethod.abx, 3, (7, 0)),

    0xE8: ("INX", AddressingMethod.imp, 1, (2, 0)),

    0xC8: ("INY", AddressingMethod.imp, 1, (2, 0)),

    0x4C: ("JMP", AddressingMethod.abs, 3, (3, 0)),
    0x6C: ("JMP", AddressingMethod.ind, 3, (5, 0)),

    0x20: ("JSR", AddressingMethod.abs, 3, (6, 0)),

    0xA9: ("LDA", AddressingMethod.imm, 2, (2, 0)),
    0xA5: ("LDA", AddressingMethod.zp, 2, (3, 0)),
    0xB5: ("LDA", AddressingMethod.zpx, 2, (4, 0)),
    0xAD: ("LDA", AddressingMethod.abs, 3, (4, 0)),
    0xBD: ("LDA", AddressingMethod.abx, 3, (4, 1)),
    0xB9: ("LDA", AddressingMethod.aby, 3, (4, 1)),
    0xA1: ("LDA", AddressingMethod.izx, 2, (6, 0)),
    0xB1: ("LDA", AddressingMethod.izy, 2, (5, 1)),

    0xA2: ("LDX", AddressingMethod.imm, 2, (2, 0)),
    0xA6: ("LDX", AddressingMethod.zp, 2, (3, 0)),
    0xB6: ("LDX", AddressingMethod.zpy, 2, (4, 0)),
    0xAE: ("LDX", AddressingMethod.abs, 3, (4, 0)),
    0xBE: ("LDX", AddressingMethod.aby, 3, (4, 1)),

    0xA0: ("LDY", AddressingMethod.imm, 2, (2, 0)),
    0xA4: ("LDY", AddressingMethod.zp, 2, (3, 0)),
    0xB4: ("LDY", AddressingMethod.zpx, 2, (4, 0)),
    0xAC: ("LDY", AddressingMethod.abs, 3, (4, 0)),
    0xBC: ("LDY", AddressingMethod.abx, 3, (4, 1)),

    0x4A: ("LSR", AddressingMethod.acc, 1, (2, 0)),
    0x46: ("LSR", AddressingMethod.zp, 2, (5, 0)),
    0x56: ("LSR", AddressingMethod.zpx, 2, (6, 0)),
    0x4E: ("LSR", AddressingMethod.abs, 3, (6, 0)),
    0x5E: ("LSR", AddressingMethod.abx, 3, (7, 0)),

    0xEA: ("NOP", AddressingMethod.imp, 1, (2, 0)),

    0x09: ("ORA", AddressingMethod.imm, 2, (2, 0)),
    0x05: ("ORA", AddressingMethod.zp, 2, (3, 0)),
    0x15: ("ORA", AddressingMethod.zpx, 2, (4, 0)),
    0x0D: ("ORA", AddressingMethod.abs, 3, (4, 0)),
    0x1D: ("ORA", AddressingMethod.abx, 3, (4, 1)),
    0x19: ("ORA", AddressingMethod.aby, 3, (4, 1)),
    0x01: ("ORA", AddressingMethod.izx, 2, (6, 0)),
    0x11: ("ORA", AddressingMethod.izy, 2, (5, 1)),

    0x48: ("PHA", AddressingMethod.imp, 1, (3, 0)),

    0x08: ("PHP", AddressingMethod.imp, 1, (3, 0)),

    0x68: ("PLA", AddressingMethod.imp, 1, (4, 0)),

    0x28: ("PLP", AddressingMethod.imp, 1, (4, 0)),

    0x2A: ("ROL", AddressingMethod.acc, 1, (2, 0)),
    0x26: ("ROL", AddressingMethod.zp, 2, (5, 0)),
    0x36: ("ROL", AddressingMethod.zpx, 2, (6, 0)),
    0x2E: ("ROL", AddressingMethod.abs, 3, (6, 0)),
    0x3E: ("ROL", AddressingMethod.abx, 3, (7, 0)),

    0x6A: ("ROR", AddressingMethod.acc, 1, (2, 0)),
    0x66: ("ROR", AddressingMethod.zp, 2, (5, 0)),
    0x76: ("ROR", AddressingMethod.zpx, 2, (6, 0)),
    0x6E: ("ROR", AddressingMethod.abs, 3, (6, 0)),
    0x7E: ("ROR", AddressingMethod.abx, 3, (7, 0)),

    0x40: ("RTI", AddressingMethod.imp, 1, (6, 0)),

    0x60: ("RTS", AddressingMethod.imp, 1, (6, 0)),

    0xE9: ("SBC", AddressingMethod.imm, 2, (2, 0)),
    0xE5: ("SBC", AddressingMethod.zp, 2, (3, 0)),
    0xF5: ("SBC", AddressingMethod.zpx, 2, (4, 0)),
    0xED: ("SBC", AddressingMethod.abs, 3, (4, 0)),
    0xFD: ("SBC", AddressingMethod.abx, 3, (4, 1)),
    0xF9: ("SBC", AddressingMethod.aby, 3, (4, 1)),
    0xE1: ("SBC", AddressingMethod.izx, 2, (6, 0)),
    0xF1: ("SBC", AddressingMethod.izy, 2, (5, 1)),

    0x38: ("SEC", AddressingMethod.imp, 1, (2, 0)),

    0xF8: ("SED", AddressingMethod.imp, 1, (2, 0)),

    0x78: ("SEI", AddressingMethod.imp, 1, (2, 0)),

    0x85: ("STA", AddressingMethod.zp, 2, (3, 0)),
    0x95: ("STA", AddressingMethod.zpx, 2, (4, 0)),
    0x8D: ("STA", AddressingMethod.abs, 3, (4, 0)),
    0x9D: ("STA", AddressingMethod.abx, 3, (5, 0)),
    0x99: ("STA", AddressingMethod.aby, 3, (5, 0)),
    0x81: ("STA", AddressingMethod.izx, 2, (6, 0)),
    0x91: ("STA", AddressingMethod.izy, 2, (6, 0)),

    0x86: ("STX", AddressingMethod.zp, 2, (3, 0)),
    0x96: ("STX", AddressingMethod.zpy, 2, (4, 0)),
    0x8E: ("STX", AddressingMethod.abs, 3, (4, 0)),

    0x84: ("STY", AddressingMethod.zp, 2, (3, 0)),
    0x94: ("STY", AddressingMethod.zpx, 2, (4, 0)),
    0x8C: ("STY", AddressingMethod.abs, 3, (4, 0)),

    0xAA: ("TAX", AddressingMethod.imp, 1, (2, 0)),

    0xA8: ("TAY", AddressingMethod.imp, 1, (2, 0)),

    0xBA: ("TSX", AddressingMethod.imp, 1, (2, 0)),

    0x8A: ("TXA", AddressingMethod.imp, 1, (2, 0)),

    0x9A: ("TXS", AddressingMethod.imp, 1, (2, 0)),

    0x98: ("TYA", AddressingMethod.imp, 1, (2, 0)),

    0x02: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x12: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x22: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x32: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x42: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x52: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x62: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x72: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0x92: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0xB2: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0xD2: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    0xF2: ("KIL", AddressingMethod.imp, 1, (0, 0)),
    
    0x04: ("NOP", AddressingMethod.zp, 2, (3, 0)),
    0x0c: ("NOP", AddressingMethod.abs, 3, (4, 0)),

    0x14: ("NOP", AddressingMethod.zpx, 2, (4, 0)),
    0x1a: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0x1c: ("NOP", AddressingMethod.abx, 3, (4, 0)),

    0x34: ("NOP", AddressingMethod.zpx, 2, (4, 0)),
    0x3a: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0x3c: ("NOP", AddressingMethod.abx, 3, (4, 0)),

    0x44: ("NOP", AddressingMethod.zp, 2, (3, 0)),

    0x54: ("NOP", AddressingMethod.zpx, 2, (4, 0)), 
    0x5a: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0x5c: ("NOP", AddressingMethod.abx, 3, (4, 0)),

    0x64: ("NOP", AddressingMethod.zp, 2, (3, 0)),

    0x74: ("NOP", AddressingMethod.zpx, 2, (4, 0)),
    0x7a: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0x7c: ("NOP", AddressingMethod.abx, 3, (4, 0)),

    0x80: ("NOP", AddressingMethod.imm, 2, (2, 0)),
    0x82: ("NOP", AddressingMethod.imm, 2, (2, 0)),
    0x89: ("NOP", AddressingMethod.imm, 2, (2, 0)),

    0xc2: ("NOP", AddressingMethod.imm, 2, (2, 0)),

    0xd4: ("NOP", AddressingMethod.zpx, 2, (4, 0)),
    0xda: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0xdc: ("NOP", AddressingMethod.abx, 3, (4, 0)),

    0xe2: ("NOP", AddressingMethod.imm, 2, (2, 0)),
    0xea: ("NOP", AddressingMethod.imp, 1, (2, 0)),

    0xf4: ("NOP", AddressingMethod.zpx, 2, (4, 0)),
    0xfa: ("NOP", AddressingMethod.imp, 1, (2, 0)),
    0xfc: ("NOP", AddressingMethod.abx, 3, (4, 0)),




    0x03: ("SLO", AddressingMethod.izx, 2, (8, 0)),
    0x13: ("SLO", AddressingMethod.izy, 2, (8, 1)),
    0x23: ("RLA", AddressingMethod.izx, 2, (8, 0)),
    0x33: ("RLA", AddressingMethod.izy, 2, (8, 1)),
    0x43: ("SRE", AddressingMethod.izx, 2, (8, 0)),
    0x53: ("SRE", AddressingMethod.izy, 2, (8, 1)),
    0x63: ("RRA", AddressingMethod.izx, 2, (8, 0)),
    0x73: ("RRA", AddressingMethod.izy, 2, (8, 1)),
    0x83: ("SAX", AddressingMethod.izx, 2, (6, 1)),
    0x93: ("AHX", AddressingMethod.izy, 2, (6, 1)),
    0xa3: ("LAX", AddressingMethod.izx, 2, (6, 1)),
    0xb3: ("LAX", AddressingMethod.izy, 2, (5, 1)),
    0xc3: ("DCP", AddressingMethod.izx, 2, (8, 0)),
    0xd3: ("DCP", AddressingMethod.izy, 2, (8, 1)),
    0xe3: ("ISB", AddressingMethod.izx, 2, (8, 0)),
    0xf3: ("ISB", AddressingMethod.izy, 2, (8, 1)),

    0x07: ("SLO", AddressingMethod.zp, 2, (5, 0)),
    0x17: ("SLO", AddressingMethod.zpx, 2, (6, 0)),
    0x27: ("RLA", AddressingMethod.zp, 2, (5, 0)),
    0x37: ("RLA", AddressingMethod.zpx, 2, (6, 0)),
    0x47: ("SRE", AddressingMethod.zp, 2, (5, 0)),
    0x57: ("SRE", AddressingMethod.zpx, 2, (6, 0)),
    0x67: ("RRA", AddressingMethod.zp, 2, (5, 0)),
    0x77: ("RRA", AddressingMethod.zpx, 2, (6, 0)),
    0x87: ("SAX", AddressingMethod.zp, 2, (3, 0)),
    0x97: ("SAX", AddressingMethod.zpy, 2, (4, 0)),
    0xa7: ("LAX", AddressingMethod.zp, 2, (3, 0)),
    0xb7: ("LAX", AddressingMethod.zpy, 2, (4, 0)),
    0xc7: ("DCP", AddressingMethod.zp, 2, (5, 0)),
    0xd7: ("DCP", AddressingMethod.zpx, 2, (6, 0)),
    0xe7: ("ISB", AddressingMethod.zp, 2, (5, 0)),
    0xf7: ("ISB", AddressingMethod.zpx, 2, (6, 0)),

    0x0b: ("ANC", AddressingMethod.imm, 2, (2, 0)),
    0x1b: ("SLO", AddressingMethod.aby, 3, (7, 0)),
    0X2B: ("ANC", AddressingMethod.imm, 2, (2, 0)),
    0x3b: ("RLA", AddressingMethod.aby, 3, (7, 0)),
    0x4b: ("ALR", AddressingMethod.imm, 2, (2, 0)),
    0x5b: ("SRE", AddressingMethod.aby, 3, (7, 0)),
    0x6b: ("ARR", AddressingMethod.imm, 2, (2, 0)),
    0x7b: ("RRA", AddressingMethod.aby, 3, (7, 0)),
    0x8b: ("XAA", AddressingMethod.imm, 2, (2, 0)),
    0x9b: ("TAS", AddressingMethod.aby, 3, (5, 1)),
    0xab: ("LAX", AddressingMethod.imm, 2, (2, 1)),
    0xbb: ("LAS", AddressingMethod.aby, 3, (4, 1)),
    0xcb: ("AXS", AddressingMethod.imm, 2, (2, 0)),
    0xdb: ("DCP", AddressingMethod.aby, 3, (7, 0)),
    0xeb: ("SBC", AddressingMethod.imm, 2, (2, 0)),
    0xfb: ("ISB", AddressingMethod.aby, 3, (7, 0)),

    0x0f: ("SLO", AddressingMethod.abs, 3, (6, 0)),
    0x1f: ("SLO", AddressingMethod.abx, 3, (7, 0)),
    0x2f: ("RLA", AddressingMethod.abs, 3, (6, 0)),
    0x3f: ("RLA", AddressingMethod.abx, 3, (7, 0)),
    0x4f: ("SRE", AddressingMethod.abs, 3, (6, 0)),
    0x5f: ("SRE", AddressingMethod.abx, 3, (7, 0)),
    0x6f: ("RRA", AddressingMethod.abs, 3, (6, 0)),
    0x7f: ("RRA", AddressingMethod.abx, 3, (7, 0)),
    0x8f: ("SAX", AddressingMethod.abs, 3, (4, 0)),
    0x9f: ("AHX", AddressingMethod.aby, 3, (5, 0)),
    0xaf: ("LAX", AddressingMethod.abs, 3, (4, 0)),
    0xbf: ("LAX", AddressingMethod.aby, 3, (4, 1)),
    0xcf: ("DCP", AddressingMethod.abs, 3, (6, 0)),
    0xdf: ("DCP", AddressingMethod.abx, 3, (7, 0)),
    0xef: ("ISB", AddressingMethod.abs, 3, (6, 0)),
    0xff: ("ISB", AddressingMethod.abx, 3, (7, 0)),

    0X9c: ("SHY", AddressingMethod.abx, 3, (5, 0)),
    0x9e: ("SHX", AddressingMethod.aby, 3, (5, 0)),
}




class Instruction:
    mnemonic:str = ""
    addressing_method:AddressingMethod = None
    length:int = 0
    cycles:Tuple[int, int]|Tuple[int, int, int] = 0

    opcode:bytes = None
    operand1:bytes = None
    operand2:bytes = None

    data:bytes = None
    addr:int = None
    
    instruction_info:tuple = None
    def __init__(self, opcode:bytes):
        self.opcode = opcode


    # def decode(self, cpu:ICPU):
    #     self.instruction_info = INSTRUCTION_TABLE.get(self.opcode[0], None)
    #     if self.instruction_info is None:
    #         raise Exception(f"Unknown instruction: {self.opcode.hex()}")
    #     self.mnemonic = self.instruction_info[0]
    #     self.addressing_method = self.instruction_info[1]
    #     self.length = self.instruction_info[2]
    #     self.cycles = self.instruction_info[3]
        
    #     operand_len = self.length - 1

    #     if operand_len == 1:
    #         self.operand1 = cpu.bus.read_byte(cpu.regs.PC)
    #         cpu.regs.PC += 1

    #     elif operand_len == 2:
    #         self.operand1 = cpu.bus.read_byte(cpu.regs.PC)
    #         cpu.regs.PC += 1
    #         self.operand2 = cpu.bus.read_byte(cpu.regs.PC)
    #         cpu.regs.PC += 1