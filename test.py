import logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='nes.log', filemode='w')
logging.basicConfig(level=logging.ERROR, format='%(levelname)s - %(message)s', filename='nes.log', filemode='w')

# from cpu import CPU
from typing import Tuple
from src.frame import NPFrame
from src.instruction import INSTRUCTION_TABLE
from src.machine import Machine
from src.cartridge import Cartridge
from src.cpu import CPUHookType



# def t1(d:dict):
#     d["a"] = 1
#     print(f"t1 d: {d}")


def status_hook(status: dict, result:dict):
    result["status"] = status
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

    print(f"{address:04X}\t{instrucion.mnemonic:<4} {operand:<10} A:{A:02X} X:{X:02X} Y:{Y:02X} P:{P:02X} SP:{SP:02X} CYC:{CYC}")


def load_test_data(file_path:str):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
    data = data.split('\n')
    _data = []
    for line in data:
        if line == '':
            continue
        # line = line.replace('\t',' ').replace("\r",'').split(' ')
        # l = [i for i in line if i!='']
        p = 0
        addr = int(line[0:4], 16)
        p += 4 + 12
        instr = line[p:p+3]
        p += 32
        A = int(line[p:p+4].split(":")[-1], 16)
        p += 4+1
        X = int(line[p:p+4].split(":")[-1], 16)
        p += 4+1
        Y = int(line[p:p+4].split(":")[-1], 16)
        p += 4+1
        P = int(line[p:p+4].split(":")[-1], 16)
        p += 4+1
        SP = int(line[p:p+5].split(":")[-1], 16)

        _data.append((addr, instr, A, X, Y, P, SP))
        
    
    return _data

def check_test_data(result:dict, test_data:Tuple):
    addr, instr, A, X, Y, P, SP = test_data
    status = result["status"]

    result = ""
    if addr != status["address"]:
        result += f"address should be {addr:04X} but {status['address']:04X} | "
    if instr != status["instruction"].mnemonic:
        result += f"instruction should be {instr} but {status['instruction'].mnemonic} | "
    if A != status["A"]:
        result +=  f"A should be {A:02X} but {status['A']:02X} | "
    if X != status["X"]:
        result +=  f"X should be {X:02X} but {status['X']:02X} | "
    if Y != status["Y"]:
        result +=  f"Y should be {Y:02X} but {status['Y']:02X} | "
    if P != status["P"]:
        result +=  f"P should be {P:02X} but {status['P']:02X} | "
    if SP != status["SP"]:
        result +=  f"SP should be {SP:02X} but {status['SP']:02X} | "

    return None if result == "" else result

def test_cpu(breakpoint_addr=None):
    breakpoint_addr = breakpoint_addr

    c=Cartridge("bugger/test_rom/nestest2.nes")
    m=Machine(c)
    m.hook_enable(True)
    m.reset(0x0C000)
    status_result = {}
    m.register_cpu_hook(CPUHookType.STATUS, status_hook, (status_result,))


    test_data = load_test_data("bugger/test_rom/nestest.log")
    for item in test_data:
        addr, instr, A, X, Y, P, SP = item
        # print(f"{addr:04X}\t{instr:<4} A:{A:02X} X:{X:02X} Y:{Y:02X} P:{P:02x} SP:{SP:02X}")
        m.debug_step()
        chech_result = check_test_data(status_result, item)
        if breakpoint_addr == status_result["status"]["address"] and breakpoint_addr is not None:
            # print(f"Breakpoint at {breakpoint_addr:04X}")
            pass
        if chech_result is not None:
            print(f"Error: At {addr:04X} | {chech_result}")
            pass
            # break

def test_all(breakpoint_addr=None):
    logging.basicConfig(level=logging.NOTSET, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("main")
    logger.setLevel(logging.NOTSET)
    breakpoint_addr = breakpoint_addr

    c=Cartridge("roms/Super Mario Bros (E).nes")
    m=Machine(c)
    m.hook_enable(True)
    m.reset()
    status_result = {"status": None}
    # m.register_cpu_hook(CPUHookType.STATUS, status_hook, (status_result,))

    m.run()

    # while True:
    #     # print(f"{addr:04X}\t{instr:<4} A:{A:02X} X:{X:02X} Y:{Y:02X} P:{P:02x} SP:{SP:02X}")

    #     # m.run()
    #     m.debug_step()
    #     if breakpoint_addr == status_result["status"]["address"] and breakpoint_addr is not None:
    #         # print(f"Breakpoint at {breakpoint_addr:04X}")
    #         pass



def show_bg():
    from PIL import Image
    import numpy as np

    c=Cartridge("bugger/test_rom/nestest2.nes")

    pattern_base_addr = 0x1000

    PALETTE={
        0: (0,0,0),
        1: (255,0,0),
        2: (0,255,0),
        3: (0,0,255),
    }
    frame = NPFrame()

    for offset in range(255):
        # Get Tile Index from Nametable
        tile_idx = offset
        tile_x = (offset % 32) * 8
        tile_y = (offset // 32) * 8

        # Get Tile Data from Pattern Table
        tile = [c.mapper.read(pattern_base_addr + (tile_idx * 16 + f)) for f in range(16)]
        
        # Render Tile
        for y in range(8):
            # TODO: check this
            high_byte = tile[y]
            low_byte = tile[y+8]

            for x in range(8):
                color_idx = ((high_byte >> (7-x)) & 0x01) << 1 | ((low_byte >> (7-x)) & 0x01) 
                color = PALETTE[color_idx]
                frame.set_pixel(tile_x+x, tile_y+y, color)

    img = Image.fromarray(frame.data.transpose(2,1,0), 'RGB')
    img.show()

if __name__ == '__main__':

    # test_cpu()
    test_all()
    # show_bg()



    # opcodes = list(INSTRUCTION_TABLE.keys())
    # opcodes.sort()
    # # opcodes = [hex(i) for i in opcodes ]
    # for i in range(0, 0xf):
    #     for j in range(0, 0xf):
    #         opcode = (i << 4) + j
    #         if opcode not in opcodes:
    #             print("   ", end="")
    #         else:
    #             print(f"{opcode:02X} ", end="")
        
    #     print()