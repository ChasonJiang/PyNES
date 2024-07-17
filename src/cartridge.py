


from abc import ABC

from .interface import ICatridge
from .mapper import IMapper, choose_mapper
from .rom import NESRom





class Cartridge(ICatridge):
    rom: NESRom = None
    mapper:IMapper = None
    def __init__(self, file_path:str):
        self.rom = NESRom(file_path)
        self.mapper = choose_mapper(self.rom)
