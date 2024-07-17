

class NESHeader:
    raw_data:bytearray = None

    sign:bytearray = None

    prg_block_size:int = 0 # a block is 16KB
    chr_block_size:int = 0 # a block is 8KB
    # flags 
    mirroring:int = 0 # 0: horizontal, 1: vertical
    has_sram:bool = False 
    has_trainer:bool = False
    has_vram:bool = False

    mapper_type_low:int = 0
    has_vs_unisystem:bool = False
    has_playchoice_10:bool = False  
    rom_version:int = 0
    mapper_type_high:int = 0
    mapper_type:int = 0
    num_blocks_of_ram:int = 0
    video_mode:int = None

    def __init__(self, raw_data:bytearray):
        self.raw_data = raw_data
        self.sign = self.raw_data[:4]
        self.prg_block_size = self.raw_data[4]
        self.chr_block_size = self.raw_data[5]
        self.mirroring = self.raw_data[6] & 0x01 # 0: horizontal, 1: vertical
        self.has_sram = bool((self.raw_data[6] & 0x02) >> 1)
        self.has_trainer = bool((self.raw_data[6] & 0x04) >> 2)
        self.has_vram = bool((self.raw_data[6] & 0x08) >> 3)
        self.mapper_type_low = (self.raw_data[6] & 0xF0) >> 4
        self.has_vs_unisystem = bool(self.raw_data[7] & 0x01)
        self.has_playchoice_10 = bool((self.raw_data[7] & 0x02) >> 1)   
        self.rom_version = int((self.raw_data[7] & 0x0C) >> 2)
        self.mapper_type_high = (self.raw_data[7] & 0xF0) >> 4
        self.mapper_type = self.mapper_type_high << 4 | self.mapper_type_low
        self.num_blocks_of_ram = self.raw_data[8]
        self.video_mode = 1 if (self.raw_data[9] & 0x01) == 0x0 else 0 # 0: NTSC, 1: PAL

    def __str__(self):
        return f'NES Header:\n' \
            f'Sign: {self.sign}\n' \
            f'PRG Block Size: {self.prg_block_size} blocks\n' \
            f'CHR Block Size: {self.chr_block_size} blocks\n' \
            f'Mirroring: {self.mirroring}\n' \
            f'Has SRAM: {self.has_sram}\n' \
            f'Has Trainer: {self.has_trainer}\n' \
            f'Has VRAM: {self.has_vram}\n' \
            f'Has VS Unisystem: {self.has_vs_unisystem}\n' \
            f'Has PlayChoice 10: {self.has_playchoice_10}\n' \
            f'ROM Version: {self.rom_version}\n' \
            f'Mapper Type: {self.mapper_type_high<<4 | self.mapper_type_low}\n' \
            f'Number of Blocks of RAM: {self.num_blocks_of_ram}\n' \
            f'Video Mode: {"PAL" if self.video_mode == 0 else "NTSC"}'
    
    def __repr__(self):
        return self.__str__()

class NESTrainer:
    raw_data:bytearray = None
    def __init__(self, raw_data:bytearray):
        self.raw_data = raw_data
    

class InvalidNESFile(Exception):
    pass


class NESRom:
    raw_data:bytearray = None
    header:NESHeader = None
    trainer:NESTrainer = None
    prg_data:bytearray = None
    chr_data:bytearray = None
    def __init__(self, file_path:str):
        self.file_path:str = file_path
        with open(file_path, 'rb') as f:
            self.raw_data = bytearray(f.read())

        self.header = NESHeader(self.raw_data[:16])
        if self.header.sign != b'NES\x1A':
            raise InvalidNESFile('Invalid NES file!')
        
        if self.header.has_trainer:
            self.trainer = NESTrainer(self.raw_data[16:16+512])
            self.prg_data = self.raw_data[16+512:16+512+self.header.prg_block_size*16*1024]
            self.chr_data = self.raw_data[16+512+self.header.prg_block_size*16*1024:]
        else:
            self.prg_data = self.raw_data[16:16+self.header.prg_block_size*16*1024]
            self.chr_data = self.raw_data[16+self.header.prg_block_size*16*1024:]



if __name__ == '__main__':
    nes_rom = NESRom('roms\Super Mario Bros (E).nes')
    print(nes_rom.header)