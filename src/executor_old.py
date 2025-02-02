





from typing import List, Tuple
from .icpu import ICPU, Flags
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



def addressing(cpu: ICPU, ins: Instruction) -> Tuple[int|bytes, int|None]:
    data = 0
    addr = None
    match ins.addressing_method:
        case AddressingMethod.acc:
            data = cpu.regs.A
        case AddressingMethod.imm:
            data = ins.operand1
        case AddressingMethod.zp:
            addr = ins.operand1
            data = cpu.bus.read_byte(addr)
        case AddressingMethod.zpx:
            addr = (ins.operand1 + cpu.regs.X) & 0xFF
            data = cpu.bus.read_byte(addr)
        case AddressingMethod.zpy:
            addr = (ins.operand1 + cpu.regs.Y) & 0xFF
            data = cpu.bus.read_byte(addr)
        case AddressingMethod.rel:
            if ins.operand1 & 0x80:
                addr = cpu.regs.PC - (ins.operand1 & 0x7F)
            else:
                addr = cpu.regs.PC + ins.operand1
            data = addr
            
            # data = cpu.bus.read_byte(addr)
        case AddressingMethod.abs:
            addr = (ins.operand2 << 8) | ins.operand1
            data = cpu.bus.read_byte(addr)
        case AddressingMethod.abx:
            addr = ((ins.operand2 << 8) | ins.operand1) + cpu.regs.X
            data = cpu.bus.read_byte(addr & 0xFFFF)
        case AddressingMethod.aby:
            addr = ((ins.operand2 << 8) | ins.operand1) + cpu.regs.Y
            data = cpu.bus.read_byte(addr & 0xFFFF)
        case AddressingMethod.ind:
            addr = (ins.operand2 << 8) | ins.operand1
            # data = cpu.bus.read_word(addr)

            ## to emulate 6502 bug
            lo = cpu.bus.read_byte(addr)
            hi = cpu.bus.read_byte((addr & 0xFF00) | ((addr + 1) & 0xFF))
            data = (hi << 8) | lo
        case AddressingMethod.izx:
            # TODO: check if this is correct
            addr = cpu.bus.read_word((ins.operand1 + cpu.regs.X) & 0xFFFF)
            data = cpu.bus.read_byte(addr)
        case AddressingMethod.izy:
            # TODO: check if this is correct
            addr = (cpu.bus.read_word(ins.operand1) + cpu.regs.Y) & 0xFFFF
            data = cpu.bus.read_byte(addr)
        case _:
            raise ValueError("Invalid addressing method")
    return data, addr


# def add_8bit(a:bytes, b:bytes):
#     # # 限制输入范围在8位整数范围内
#     # a = int(a) & 0xFF
#     # b = int(b) & 0xFF
    
#     # 加法
#     sum = a + b
#     result = sum & 0xFF
    
#     # 检查进位
#     carry = sum > 0xFF
    
#     # 检查溢出（通过检查符号位）
#     sign_a = a >> 7
#     sign_b = b >> 7
#     sign_result = result >> 7
#     overflow = (sign_a == sign_b) and (sign_a != sign_result)
    
#     # 检查结果的正负
#     is_negative = sign_result == 1
    
#     return result, is_negative, carry, overflow

# def subtract_8bit(a:bytes, b:bytes):
#     # 补码减法
#     b = (~b + 1) & 0xFF  # 计算b的补码    
#     return add_8bit(a, b)


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


@method_register("ADC")
def ADC(cpu: ICPU, ins: Instruction):
    # A,Z,C,N = A + M + C
    C = cpu.regs.P & Flags.C
    A = cpu.regs.A

    M, _ = addressing(cpu, ins)
    
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
    M, _ = addressing(cpu, ins)
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
    M, addr = addressing(cpu, ins)
    result = M << 1

    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if M >> 7:
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
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BCS")
def BCS(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.C:
        _, cpu.regs.PC = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BEQ")
def BEQ(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.Z:
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BIT")
def BIT(cpu: ICPU, ins: Instruction):
    # Z,N,V = M & A
    M, _ = addressing(cpu, ins)
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
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BNE")
def BNE(cpu: ICPU, ins: Instruction):
    # check if Z flag is not set
    if not (cpu.regs.P & Flags.Z):
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]

@method_register("BPL")
def BPL(cpu: ICPU, ins: Instruction):
    # check if N flag is not set
    if not (cpu.regs.P & Flags.N):
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1

    cpu.defer_cycles += ins.cycles[0]


@method_register("BRK")
def BRK(cpu: ICPU, ins: Instruction):
    def push_byte(data:bytes):
        cpu.bus.write_byte(cpu.regs.SP, data)
        cpu.regs.SP -= 1

    def push_word(data:int):
        # high byte first (little-endian)
        push_byte((data >> 8) & 0xFF)
        push_byte(data & 0xFF)

    push_word(cpu.regs.PC)
    push_byte(cpu.regs.P)

    cpu.regs.PC = cpu.bus.read_word(cpu.IRQ_ADDR)
    cpu.regs.P |= Flags.B

    cpu.defer_cycles += ins.cycles[0]


@method_register("BVC")
def BVC(cpu: ICPU, ins: Instruction):
    if not (cpu.regs.P & Flags.V):
        cpu.regs.PC, _ = addressing(cpu, ins)
        cpu.defer_cycles += 1
    
    cpu.defer_cycles += ins.cycles[0]

@method_register("BVS")
def BVS(cpu: ICPU, ins: Instruction):
    if cpu.regs.P & Flags.V:
        cpu.regs.PC, _ = addressing(cpu, ins)
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
    M, _ = addressing(cpu, ins)
    result, is_negative, carry, overflow = sub_8bit(A, M)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else: 
        cpu.regs.P &= ~Flags.Z

    if result >= 0 and result <= 0x80:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    # if carry:
    #     # C
    #     cpu.regs.P |= Flags.C
    # else:
    #     cpu.regs.P &= ~Flags.C

    cpu.defer_cycles += ins.cycles[0]


@method_register("CPX")
def CPX(cpu: ICPU, ins: Instruction):
    # compare X with M
    # Z,C,N = X-M
    X = cpu.regs.X
    M, _ = addressing(cpu, ins)
    result, is_negative, carry, overflow = sub_8bit(X, M)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if result >= 0 and result <= 0x80:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    # if carry:
    #     # C
    #     cpu.regs.P |= Flags.C
    # else:
    #     cpu.regs.P &= ~Flags.C

    cpu.defer_cycles += ins.cycles[0]


@method_register("CPY")
def CPY(cpu: ICPU, ins: Instruction):
    # compare Y with M
    # Z,C,N = Y-M
    Y = cpu.regs.Y
    M, _ = addressing(cpu, ins)
    result, is_negative, carry, overflow = sub_8bit(Y, M)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if result >= 0 and result <= 0x80:
        # C
        cpu.regs.P |= Flags.C
    else:
        cpu.regs.P &= ~Flags.C

    if is_negative:
        # N
        cpu.regs.P |= Flags.N
    else:
        cpu.regs.P &= ~Flags.N

    # if carry:
    #     # C
    #     cpu.regs.P |= Flags.C
    # else:
    #     cpu.regs.P &= ~Flags.C

    cpu.defer_cycles += ins.cycles[0]


@method_register("DEC")
def DEC(cpu: ICPU, ins: Instruction):
    # M = M - 1
    M, addr = addressing(cpu, ins)
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
    M, _ = addressing(cpu, ins)
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
    M, addr = addressing(cpu, ins)
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
    _, cpu.regs.PC = addressing(cpu, ins)
    cpu.defer_cycles += ins.cycles[0]


@method_register("JSR")
def JSR(cpu: ICPU, ins: Instruction):
    # push PC+1, push P
    def push_byte(data:bytes):
        cpu.bus.write_byte(cpu.regs.SP, data)
        cpu.regs.SP -= 1

    def push_word(data:int):
        # high byte first (little-endian)
        push_byte((data >> 8) & 0xFF)
        push_byte(data & 0xFF)

    push_word(cpu.regs.PC)
    # push_byte(cpu.regs.P)

    # PC = addr
    _, cpu.regs.PC = addressing(cpu, ins)
    cpu.defer_cycles += ins.cycles[0]


@method_register("LDA")
def LDA(cpu: ICPU, ins: Instruction):
    # A = M
    A = cpu.regs.A
    M, _ = addressing(cpu, ins)
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
    M, _ = addressing(cpu, ins)
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
    M, _ = addressing(cpu, ins)
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
    M, addr = addressing(cpu, ins)
    result = M >> 1
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


@method_register("NOP")
def NOP(cpu: ICPU, ins: Instruction):
    # do nothing
    cpu.defer_cycles += ins.cycles[0]


@method_register("ORA")
def ORA(cpu: ICPU, ins: Instruction):
    # A,Z,N = A | M
    A = cpu.regs.A
    M, _ = addressing(cpu, ins)
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
    def push_byte(data:bytes):
        cpu.bus.write_byte(cpu.regs.SP, data)
        cpu.regs.SP -= 1

    push_byte(cpu.regs.A)
    cpu.defer_cycles += ins.cycles[0]


@method_register("PHP")
def PHP(cpu: ICPU, ins: Instruction):
    # push P
    def push_byte(data:bytes):
        cpu.bus.write_byte(cpu.regs.SP, data)
        cpu.regs.SP -= 1

    push_byte(cpu.regs.P)
    cpu.defer_cycles += ins.cycles[0]


@method_register("PLA")
def PLA(cpu: ICPU, ins: Instruction):
    # pull A
    def pull_byte() -> bytes:
        cpu.regs.SP += 1
        data = cpu.bus.read_byte(cpu.regs.SP)
        return data
    

    A = pull_byte()
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
    cpu.regs.A = A | Flags.B 
    cpu.defer_cycles += ins.cycles[0]


@method_register("PLP")
def PLP(cpu: ICPU, ins: Instruction):
    # pull P
    def pull_byte() -> bytes:
        cpu.regs.SP += 1
        data = cpu.bus.read_byte(cpu.regs.SP)    
        return data

    P = pull_byte()
    # cpu.regs.P = P

    # TODO:WTF? It's maybe a bug of NES CPU?
    cpu.regs.P = P & (~Flags.B) | Flags.U
    cpu.defer_cycles += ins.cycles[0]


@method_register("ROL")
def ROL(cpu: ICPU, ins: Instruction):
    # M = M << 1 | C
    M, addr = addressing(cpu, ins)
    result = (M << 1) | (cpu.regs.P & Flags.C)
    if result == 0:
        # Z
        cpu.regs.P |= Flags.Z
    else:
        cpu.regs.P &= ~Flags.Z

    if (M >> 7) & 0x01:
        # C
        cpu.regs.P |= Flags.C
        result |= 0x01
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
    # M = (C | M ) >> 1
    M, addr = addressing(cpu, ins)
    result = ((cpu.regs.P & Flags.C) | M ) >> 1
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


@method_register("RTI")
def RTI(cpu: ICPU, ins: Instruction):
    # pull P, pull PC
    def pull_byte() -> bytes:
        cpu.regs.SP += 1
        data = cpu.bus.read_byte(cpu.regs.SP)
        return data

    P = pull_byte()
    cpu.regs.P = P

    PC_lo = pull_byte()
    PC_hi = pull_byte()
    cpu.regs.PC = (PC_hi << 8) | PC_lo
    cpu.defer_cycles += ins.cycles[0]


@method_register("RTS")
def RTS(cpu: ICPU, ins: Instruction):
    # pull PC+1, pull PC
    def pull_byte() -> bytes:   
        cpu.regs.SP += 1 
        data = cpu.bus.read_byte(cpu.regs.SP)
        return data

    PC_lo = pull_byte()
    PC_hi = pull_byte()
    cpu.regs.PC = (PC_hi << 8) | PC_lo
    # cpu.regs.PC += 1
    cpu.defer_cycles += ins.cycles[0]


@method_register("SBC")
def SBC(cpu: ICPU, ins: Instruction):
    # A,Z,C,N = A - M - (1 - C)
    A = cpu.regs.A
    M, _ = addressing(cpu, ins)
    carry = (cpu.regs.P & Flags.C) ^ 0x01
    result, is_negative, carry, overflow = sub_8bit(A, M, carry)
    
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

    # if not overflow:
    #     # C
    #     cpu.regs.P |= Flags.C
    # else:
    #     cpu.regs.P &= ~Flags.C

    if overflow:
        # V
        cpu.regs.P &= ~Flags.C    
        cpu.regs.P |= Flags.V
    else:
        cpu.regs.P |= Flags.C
        cpu.regs.P &= ~Flags.V




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
    M, addr = addressing(cpu, ins)
    cpu.bus.write_byte(addr, A)
    cpu.defer_cycles += ins.cycles[0]


@method_register("STX")
def STX(cpu: ICPU, ins: Instruction):
    # M = X
    X = cpu.regs.X
    M, addr = addressing(cpu, ins)
    cpu.bus.write_byte(addr, X)
    cpu.defer_cycles += ins.cycles[0]


@method_register("STY")
def STY(cpu: ICPU, ins: Instruction):
    # M = Y
    Y = cpu.regs.Y
    M, addr = addressing(cpu, ins)
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








