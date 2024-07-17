




from abc import ABC

from .interface import IMemory




class Memory(IMemory):
    memory:bytearray = None
    size:int = 0

    def __init__(self, size:int):
        self.size = size
        self.memory = bytearray(size)
    
    def write(self, address:int, data:bytes):
        self.memory[address] = data
    
    def read(self, address:int, size:int=1) -> bytes:
        if size == 1:
            return self.memory[address]
        else:
            return self.memory[address:address+size]