





from typing import List, Tuple
from .interface import ICPU, Flags
from .instruction import AddressingMethod, Instruction


EXECUTION_METHODS = {}

def method_register(func_name):
    def decorator(func):
        EXECUTION_METHODS[func_name] = func
        return func
    return decorator



class Executor:
    def __init__(self, cpu: ICPU):
        self.cpu = cpu

    def execute(self, ins: Instruction):
        method = EXECUTION_METHODS.get(ins.mnemonic, None)
        if method is None:
            raise ValueError(f"Unsupported instruction: {ins.mnemonic}")
        method(self.cpu, ins)




def push_byte(cpu:ICPU, data:bytes):
    addr = cpu.regs.SP + 0x100
    if addr < 0x100:
        raise RuntimeError("Stack overflow")
    cpu.bus.write_byte(addr, data)
    cpu.regs.SP -= 1



def push_word(cpu:ICPU, data:int):
    # high byte first (little-endian)
    push_byte(cpu, (data >> 8) & 0xFF)
    push_byte(cpu, data & 0xFF)


def pull_byte(cpu:ICPU) -> bytes:
    cpu.regs.SP += 1
    addr = cpu.regs.SP + 0x100
    if addr > 0x1FF:
        raise RuntimeError("Stack underflow")
    data = cpu.bus.read_byte(addr) 
    return data

def pull_word(cpu:ICPU) -> int:
    # low byte first (little-endian)
    low = pull_byte(cpu)
    high = pull_byte(cpu)
    return (high << 8) | low

def add_8bit(*nums:List[bytes])->Tuple[bytes, bool, bool, bool]:
    # 初始值
    total = 0
    carry = False
    overflow = False
    
    for num in nums:
        # num = int(num) & 0xFF
        new_total = total + num
        
        # 检查进位
        carry |= new_total > 0xFF
        
        # 计算临时结果
        result = new_total & 0xFF
        
        # 检查溢出（通过检查符号位）
        sign_total = total >> 7
        sign_num = num >> 7
        sign_result = result >> 7
        overflow |= (sign_total == sign_num) and (sign_total != sign_result)
        
        # 更新总数
        total = result
    
    # 检查结果的正负
    is_negative = total >> 7 == 1
    total &= 0xFF
    return total, is_negative, carry, overflow

def sub_8bit(*nums:List[bytes])->Tuple[bytes, bool, bool, bool]:
    # 初始值为第一个数
    total = int(nums[0]) & 0xFF
    carry = False
    overflow = False
    
    for num in nums[1:]:
        # num = int(num) & 0xFF
        # 补码减法
        num = (~num + 1) & 0xFF
        new_total = total + num
        
        # # 检查进位
        carry |= new_total > 0xFF
        
        # 计算临时结果
        result = new_total & 0xFF
        
        # 检查溢出（通过检查符号位）
        sign_total = total >> 7
        sign_num = num >> 7
        sign_result = result >> 7
        overflow |= (sign_total == sign_num) and (sign_total != sign_result)

        # result, n, c, v = add_8bit(total, num)

        # carry |= c
        # overflow |= v
        
        # 更新总数
        total = result
    
    # 检查结果的正负
    is_negative = total >> 7 == 1
    total &= 0xFF
    return total, is_negative, carry, overflow


@method_register("ADC")
def ADC(cpu: ICPU, ins: Instruction):
    # A,Z,C,N = A + M + C
    C = cpu.regs.P & Flags.C
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    
    result, is_negative, carry, overflow = add_8bit(A, M, C)

    if result == 0:
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if carry:
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C
        
    if is_negative:
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    if overflow:
        cpu.regs.P |= Flags.V
    else:
        cpu.regs.P &= ~Flags.V
        \

    cpu.regs.A = result
    cpu.defer_cycles += ins.cycles[0]


@method_register("AND")
def AND(cpu: ICPU, ins: Instruction):
    # A,Z,N = A & M
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    result = A & M
    if result == 0:
        cpu.regs.P |= Flags.Z
    if result >> 7:
        cpu.regs.P |= Flags.N

    cpu.regs.A = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("ASL")
def ASL(cpu: ICPU, ins: Instruction):
    # A,Z,C,N = M << 1
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result = M << 1

    if (result & 0xFF) == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7 )& 0x01:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    if ins.addressing_method == AddressingMethod.acc:
        cpu.regs.A = result & 0xFF
    else:
        cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]



@method_register("BCC")
def BCC(cpu: ICPU, ins: Instruction):
    if not (cpu.regs.P & Flags.C):
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BCS")
def BCS(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.C:
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BEQ")
def BEQ(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.Z:
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BIT")
def BIT(cpu: ICPU, ins: Instruction):
    # Z,N,V = M & A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    A = cpu.regs.A
    result = M & A
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    # V
    m6 = ((M >> 6) & 0x01)
    if m6 == 1:
        cpu.regs.P |= Flags.V
    else:
        cpu.regs.P &= ~Flags.V

    # N
    m7 = ((M >> 7) & 0x01)
    if m7 == 1:
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.defer_cycles += ins.cycles[0]


@method_register("BMI")
def BMI(cpu: ICPU, ins: Instruction):
    # check if N flag is set
    if cpu.regs.P & Flags.N:
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BNE")
def BNE(cpu: ICPU, ins: Instruction):
    # check if Z flag is not set
    if not (cpu.regs.P & Flags.Z):
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BPL")
def BPL(cpu: ICPU, ins: Instruction):
    # check if N flag is not set
    if not (cpu.regs.P & Flags.N):
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]


@method_register("BRK")
def BRK(cpu: ICPU, ins: Instruction):

    push_word(cpu, cpu.regs.PC)
    push_byte(cpu, cpu.regs.P)

    cpu.regs.PC = cpu.bus.read_word(cpu.IRQ_ADDR)
    cpu.regs.P |= Flags.B

    cpu.defer_cycles += ins.cycles[0]


@method_register("BVC")
def BVC(cpu: ICPU, ins: Instruction):
    if not (cpu.regs.P & Flags.V):
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1
    
    cpu.defer_cycles += ins.cycles[0]

@method_register("BVS")
def BVS(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.V:
        cpu.regs.PC = ins.addr
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]


@method_register("CLC")
def CLC(cpu: ICPU, ins: Instruction):
    # clear C flag
    cpu.regs.P &= ~Flags.C
    cpu.defer_cycles += ins.cycles[0]


@method_register("CLD")
def CLD(cpu: ICPU, ins: Instruction):
    # clear D flag
    cpu.regs.P &= ~Flags.D
    cpu.defer_cycles += ins.cycles[0]


@method_register("CLI")
def CLI(cpu: ICPU, ins: Instruction):
    # clear I flag
    cpu.regs.P &= ~Flags.I
    cpu.defer_cycles += ins.cycles[0]


@method_register("CLV")
def CLV(cpu: ICPU, ins: Instruction):
    # clear V flag
    cpu.regs.P &= ~Flags.V
    cpu.defer_cycles += ins.cycles[0]


@method_register("CMP")
def CMP(cpu: ICPU, ins: Instruction):
    # compare A with M
    # Z,C,N = A-M
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)

    result = A - M
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else: 
        cpu.regs.P &= ~Flags.Z

    if result >= 0:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x1:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N


    cpu.defer_cycles += ins.cycles[0]


@method_register("CPX")
def CPX(cpu: ICPU, ins: Instruction):
    # compare X with M
    # Z,C,N = X-M
    X = cpu.regs.X
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    result = X - M
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else: 
        cpu.regs.P &= ~Flags.Z

    if result >= 0:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x1:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.defer_cycles += ins.cycles[0]


@method_register("CPY")
def CPY(cpu: ICPU, ins: Instruction):
    # compare Y with M
    # Z,C,N = Y-M
    Y = cpu.regs.Y
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)

    result = Y - M
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else: 
        cpu.regs.P &= ~Flags.Z

    if result >= 0:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x1:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N


    cpu.defer_cycles += ins.cycles[0]


@method_register("DEC")
def DEC(cpu: ICPU, ins: Instruction):
    # M = M - 1
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result, is_negative, carry, overflow = sub_8bit(M, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]


@method_register("DEX")
def DEX(cpu: ICPU, ins: Instruction):
    # X = X - 1
    X = cpu.regs.X
    result, is_negative, carry, overflow = sub_8bit(X, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("DEY")
def DEY(cpu: ICPU, ins: Instruction):
    # Y = Y - 1
    Y = cpu.regs.Y
    result, is_negative, carry, overflow = sub_8bit(Y, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.Y = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("EOR")
def EOR(cpu: ICPU, ins: Instruction):
    # A,Z,N = A ^ M
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    result = A ^ M
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (result >> 7) & 0x01 :
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.A = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("INC")
def INC(cpu: ICPU, ins: Instruction):
    # M = M + 1
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result, is_negative, carry, overflow = add_8bit(M, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]


@method_register("INX")
def INX(cpu: ICPU, ins: Instruction):
    # X = X + 1
    X = cpu.regs.X
    result, is_negative, carry, overflow = add_8bit(X, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("INY")
def INY(cpu: ICPU, ins: Instruction):
    # Y = Y + 1
    Y = cpu.regs.Y
    result, is_negative, carry, overflow = add_8bit(Y, 1)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.Y = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


@method_register("JMP")
def JMP(cpu: ICPU, ins: Instruction):
    # PC = addr
    cpu.regs.PC = ins.addr
    cpu.defer_cycles += ins.cycles[0]


@method_register("JSR")
def JSR(cpu: ICPU, ins: Instruction):
    # push PC-1, push P

    push_word(cpu, cpu.regs.PC-1)
    # push_byte(cpu.regs.P)

    # PC = addr
    cpu.regs.PC = ins.addr
    cpu.defer_cycles += ins.cycles[0]


@method_register("LDA")
def LDA(cpu: ICPU, ins: Instruction):
    # A = M
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    if M == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.A = M
    cpu.defer_cycles += ins.cycles[0]


@method_register("LDX")
def LDX(cpu: ICPU, ins: Instruction):
    # X = M
    X = cpu.regs.X
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    if M == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = M
    cpu.defer_cycles += ins.cycles[0]


@method_register("LDY")
def LDY(cpu: ICPU, ins: Instruction):
    # Y = M
    Y = cpu.regs.Y
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    if M == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.Y = M
    cpu.defer_cycles += ins.cycles[0]



@method_register("LSR")
def LSR(cpu: ICPU, ins: Instruction):
    # M = M >> 1
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result = M >> 1
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if M & 0x01:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    if ins.addressing_method == AddressingMethod.acc:
        cpu.regs.A = result & 0xFF
    else:
        cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]


@method_register("NOP")
def NOP(cpu: ICPU, ins: Instruction):
    # do nothing
    cpu.defer_cycles += ins.cycles[0]


@method_register("ORA")
def ORA(cpu: ICPU, ins: Instruction):
    # A,Z,N = A | M
    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    result = A | M
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (result >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.A = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]



@method_register("PHA")
def PHA(cpu: ICPU, ins: Instruction):
    # push A

    push_byte(cpu, cpu.regs.A)
    cpu.defer_cycles += ins.cycles[0]


@method_register("PHP")
def PHP(cpu: ICPU, ins: Instruction):
    # push P
    # push_byte(cpu.regs.P)
    push_byte(cpu, cpu.regs.P | Flags.B) # TODO:WTF? It's maybe a bug of NES CPU?
    cpu.defer_cycles += ins.cycles[0]


@method_register("PLA")
def PLA(cpu: ICPU, ins: Instruction):
    # pull A

    A = pull_byte(cpu)
    if A == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (A >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    # cpu.regs.A = A
    
    # TODO:WTF? It's maybe a bug of NES CPU?
    cpu.regs.A = A 
    cpu.defer_cycles += ins.cycles[0]


@method_register("PLP")
def PLP(cpu: ICPU, ins: Instruction):
    # pull P

    P = pull_byte(cpu)
    # cpu.regs.P = P

    # TODO:WTF? It's maybe a bug of NES CPU?
    cpu.regs.P = P & (~Flags.B) | Flags.U
    cpu.defer_cycles += ins.cycles[0]


@method_register("ROL")
def ROL(cpu: ICPU, ins: Instruction):
    # M = M << 1 | C
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result = (M << 1) | (cpu.regs.P & Flags.C)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7) & 0x01:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    if ins.addressing_method == AddressingMethod.acc:
        cpu.regs.A = result & 0xFF
    else:
        cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]


@method_register("ROR")
def ROR(cpu: ICPU, ins: Instruction):
    # M = (C << 7) | (M >> 1)
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    addr = ins.addr
    result = ((cpu.regs.P & Flags.C) << 7 )| ( M  >> 1 )
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if M  & 0x01:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    if ins.addressing_method == AddressingMethod.acc:
        cpu.regs.A = result & 0xFF
    else:
        cpu.bus.write_byte(addr, result & 0xFF)
    cpu.defer_cycles += ins.cycles[0]


@method_register("RTI")
def RTI(cpu: ICPU, ins: Instruction):
    # pull P, pull PC

    P = pull_byte(cpu)
    cpu.regs.P = P | Flags.U

    # PC_lo = pull_byte(cpu)
    # PC_hi = pull_byte(cpu)
    PC = pull_word(cpu)
    cpu.regs.PC = PC
    # cpu.regs.PC += 1
    cpu.defer_cycles += ins.cycles[0]


@method_register("RTS")
def RTS(cpu: ICPU, ins: Instruction):
    # pull PC+1, pull PC
    # PC_lo = pull_byte(cpu)
    # PC_hi = pull_byte(cpu)
    # cpu.regs.PC = (PC_hi << 8) | PC_lo
    PC = pull_word(cpu)
    cpu.regs.PC = PC
    cpu.regs.PC += 1
    cpu.defer_cycles += ins.cycles[0]


# @method_register("SBC")
# def SBC(cpu: ICPU, ins: Instruction):
#     # A,Z,C,N = A - M - (1 - C)
#     A = cpu.regs.A
#     M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
#     carry = (cpu.regs.P & Flags.C) ^ 0x01
#     result, is_negative, carry, overflow = sub_8bit(A, M, carry)
    
#     if result == 0:
#         # Z
#         cpu.regs.P |= Flags.Z
#     else:
#         cpu.regs.P &= ~Flags.Z

#     if is_negative:
#         # N
#         cpu.regs.P |= Flags.N
#     else:
#         cpu.regs.P &= ~Flags.N

#     if carry:
#         # C
#         cpu.regs.P |= Flags.C
#     else:
#         cpu.regs.P &= ~Flags.C

#     if overflow:
#         # V
#         # cpu.regs.P &= ~Flags.C    
#         cpu.regs.P |= Flags.V
#     else:
#         # cpu.regs.P |= Flags.C
#         cpu.regs.P &= ~Flags.V




#     # TODO: check Overflow Flag

#     cpu.regs.A = result & 0xFF
#     cpu.defer_cycles += ins.cycles[0]

@method_register("SBC")
def SBC(cpu: ICPU, ins: Instruction):

    A = cpu.regs.A
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    carry = (cpu.regs.P & Flags.C) ^ 0x01

    # Subtract M and the inverted carry from A
    result = A - M - carry
    
    # Compute flags
    carry_flag = 1 if result >= 0 else 0
    zero_flag = 1 if result == 0 else 0
    negative_flag = 1 if (result & 0x80) != 0 else 0  # Check if bit 7 is set
    overflow_flag = 1 if ((A ^ result) & (A ^ M) & 0x80) != 0 else 0  # Check if sign bit is incorrect
    
    # # Result should be within 8 bits
    # result &= 0xFF
    # 处理进位和溢出
    if carry_flag:
        cpu.regs.P |= Flags.C

    else:
        cpu.regs.P &= ~Flags.C


    # 处理零标志
    if zero_flag:
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    # 处理溢出标志 (如果符号位不正确)
    if overflow_flag:
        cpu.regs.P |= Flags.V
    else:
        # cpu.regs.P |= Flags.C
        cpu.regs.P &= ~Flags.V

    # 处理负标志
    if negative_flag:
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N
    # TODO: check Overflow Flag

    cpu.regs.A = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]

    

@method_register("SEC")
def SEC(cpu: ICPU, ins: Instruction):
    # C = 1
    cpu.regs.P |= Flags.C
    cpu.defer_cycles += ins.cycles[0]


@method_register("SED")
def SED(cpu: ICPU, ins: Instruction):
    # D = 1
    cpu.regs.P |= Flags.D
    cpu.defer_cycles += ins.cycles[0]


@method_register("SEI")
def SEI(cpu: ICPU, ins: Instruction):
    # I = 1
    cpu.regs.P |= Flags.I
    cpu.defer_cycles += ins.cycles[0]


@method_register("STA")
def STA(cpu: ICPU, ins: Instruction):
    # M = A
    A = cpu.regs.A
    addr = ins.addr
    cpu.bus.write_byte(addr, A)
    cpu.defer_cycles += ins.cycles[0]


@method_register("STX")
def STX(cpu: ICPU, ins: Instruction):
    # M = X
    X = cpu.regs.X
    addr = ins.addr
    cpu.bus.write_byte(addr, X)
    cpu.defer_cycles += ins.cycles[0]


@method_register("STY")
def STY(cpu: ICPU, ins: Instruction):
    # M = Y
    Y = cpu.regs.Y
    addr = ins.addr
    cpu.bus.write_byte(addr, Y)
    cpu.defer_cycles += ins.cycles[0]


@method_register("TAX")
def TAX(cpu: ICPU, ins: Instruction):
    # X = A
    X = cpu.regs.A
    if X == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (X >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = X
    cpu.defer_cycles += ins.cycles[0]


@method_register("TAY")
def TAY(cpu: ICPU, ins: Instruction):
    # Y = A
    Y = cpu.regs.A
    if Y == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (Y >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.Y = Y
    cpu.defer_cycles += ins.cycles[0]


@method_register("TSX")
def TSX(cpu: ICPU, ins: Instruction):
    # X = SP
    X = cpu.regs.SP
    if X == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (X >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = X
    cpu.defer_cycles += ins.cycles[0]


@method_register("TXA")
def TXA(cpu: ICPU, ins: Instruction):
    # A = X
    A = cpu.regs.X
    if A == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (A >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.A = A
    cpu.defer_cycles += ins.cycles[0]


@method_register("TXS")
def TXS(cpu: ICPU, ins: Instruction):
    # SP = X
    cpu.regs.SP = cpu.regs.X
    cpu.defer_cycles += ins.cycles[0]


@method_register("TYA")
def TYA(cpu: ICPU, ins: Instruction):
    # A = Y
    A = cpu.regs.Y
    if A == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (A >> 7) & 0x01:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.A = A
    cpu.defer_cycles += ins.cycles[0]





















### Combined instructions
@method_register("SLO")
def SLO(cpu: ICPU, ins: Instruction):
    ASL(cpu, ins)
    if ins.addressing_method == AddressingMethod.acc:
        ins.data = cpu.regs.A
    else:
        ins.data = cpu.bus.read_byte(ins.addr)

    ORA(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("RLA")
def RLA(cpu: ICPU, ins: Instruction):
    ROL(cpu, ins)
    if ins.addressing_method == AddressingMethod.acc:
        ins.data = cpu.regs.A
    else:
        ins.data = cpu.bus.read_byte(ins.addr)
        
    AND(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("SRE")
def SRE(cpu: ICPU, ins: Instruction):
    LSR(cpu, ins)
    if ins.addressing_method == AddressingMethod.acc:
        ins.data = cpu.regs.A
    else:
        ins.data = cpu.bus.read_byte(ins.addr)

    EOR(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("RRA")
def RRA(cpu: ICPU, ins: Instruction):
    ROR(cpu, ins)
    if ins.addressing_method == AddressingMethod.acc:
        ins.data = cpu.regs.A
    else:
        ins.data = cpu.bus.read_byte(ins.addr)

    ADC(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]



@method_register("SAX")
def SAX(cpu: ICPU, ins: Instruction):
    # M = (A & X)
    A = cpu.regs.A
    X = cpu.regs.X
    result = (A & X)
    cpu.bus.write_byte(ins.addr, result)
    cpu.defer_cycles += ins.cycles[0]


@method_register("LAX")
def LAX(cpu: ICPU, ins: Instruction):
    LDA(cpu, ins)
    LDX(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("DCP")
def DCP(cpu: ICPU, ins: Instruction):
    DEC(cpu, ins)
    ins.data = cpu.bus.read_byte(ins.addr)
    CMP(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]

@method_register("ISB")
@method_register("ISC")
def ISC(cpu: ICPU, ins: Instruction):
    INC(cpu, ins)
    ins.data = cpu.bus.read_byte(ins.addr)
    SBC(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]



@method_register("ANC")
def ANC(cpu: ICPU, ins: Instruction):
    AND(cpu, ins)
    cpu.regs.P &= ~Flags.C
    cpu.regs.P |= (cpu.regs.A >> 7) & Flags.C
    cpu.defer_cycles = ins.cycles[0]

@method_register("ALR")
def ALR(cpu: ICPU, ins: Instruction):
    AND(cpu, ins)
    LSR(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]

@method_register("ARR")
def ARR(cpu: ICPU, ins: Instruction):
    AND(cpu, ins)
    ROR(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]

@method_register("XAA")
def XAA(cpu: ICPU, ins: Instruction):
    TAX(cpu, ins)
    AND(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("LAX")
def LAX(cpu: ICPU, ins: Instruction):
    LDA(cpu, ins)
    TAX(cpu, ins)
    cpu.defer_cycles = ins.cycles[0]


@method_register("AXS")
def AXS(cpu: ICPU, ins: Instruction):
    # X = (A & X) - M
    A = cpu.regs.A
    X = cpu.regs.X
    M = ins.data if ins.data is not None else cpu.bus.read_byte(ins.addr)
    result = (A & X) - M

    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else: 
        cpu.regs.P &= ~Flags.Z

    if result >= 0:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if (result >> 7) & 0x1:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    cpu.regs.X = result & 0xFF
    cpu.defer_cycles += ins.cycles[0]


# @method_register("SBC*")
# def SBC_star(cpu: ICPU, ins: Instruction):
#     SBC(cpu, ins)
#     NOP(cpu, ins)

@method_register("AHX")
def AHX(cpu: ICPU, ins: Instruction):
    # M = (A & X) & 0xFF
    A = cpu.regs.A
    X = cpu.regs.X
    result = (A & X) & 0xFF
    cpu.bus.write_byte(ins.addr, result)
    cpu.defer_cycles += ins.cycles[0]


@method_register("SHX")
def SHX(cpu: ICPU, ins: Instruction):
    # M = X & 0xFF
    X = cpu.regs.X
    result = X & 0xFF
    cpu.bus.write_byte(ins.addr, result)
    cpu.defer_cycles += ins.cycles[0]


@method_register("SHY")
def SHY(cpu: ICPU, ins: Instruction):
    # M = Y & 0xFF
    Y = cpu.regs.Y
    result = Y & 0xFF
    cpu.bus.write_byte(ins.addr, result)
    cpu.defer_cycles += ins.cycles[0]


@method_register("TAS")
def TAS(cpu: ICPU, ins: Instruction):
    # SP+ = A & X
    # M = A & X & 0xFF
    A = cpu.regs.A
    X = cpu.regs.X
    result = A & X
    push_byte(cpu, result)
    cpu.bus.write_byte(ins.addr, result & 0xFF)


@method_register("LAS")
def LAS(cpu: ICPU, ins: Instruction):
    # SP+ = M & SP-
    # A = M & SP-
    # X = M & SP-
    SP_ = pull_byte(cpu)
    M = cpu.bus.read_byte(ins.addr)
    result = M & SP_
    cpu.regs.A = result
    cpu.regs.X = result
    push_byte(cpu, result)




@method_register("KIL")
def KIL(cpu: ICPU, ins: Instruction):
    cpu._call_shutdown_hook()