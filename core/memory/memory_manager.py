from core.memory.physical_memory import PhysicalMemory
from core.memory.page_table import PageTable
from core.errors import VMError

class MemoryManager:
    def __init__(self, memory_size=65536, page_size=16):
        self.physical_memory = PhysicalMemory(memory_size)
        self.page_size = page_size
        self.num_frames = memory_size // page_size
        self.free_frames = list(range(self.num_frames))

    def create_process_memory(self, process):
        num_pages = (process.virtual_memory_size + self.page_size - 1) // self.page_size
        if len(self.free_frames) < num_pages:
            raise VMError("Out of physical memory")
        
        process.page_table = PageTable()
        for v_page in range(num_pages):
            p_frame = self.free_frames.pop(0)
            process.page_table.mapping[v_page] = p_frame

    def release_memory(self, process):
        if process.page_table:
            for p_frame in process.page_table.mapping.values():
                self.free_frames.append(p_frame)
            process.page_table.mapping.clear()

    def translate_address(self, process, virtual_address):
        if virtual_address < 0 or virtual_address >= process.virtual_memory_size:
            raise VMError(f"Memory access out of bounds: {virtual_address}")
            
        if not process.page_table:
            raise VMError("Process has no allocated memory")

        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        if page_number not in process.page_table.mapping:
            raise VMError(f"Segmentation fault: unmapped page {page_number}")

        frame_number = process.page_table.mapping[page_number]
        physical_address = (frame_number * self.page_size) + offset
        return physical_address

    def read(self, process, virtual_address):
        phys_addr = self.translate_address(process, virtual_address)
        return self.physical_memory.frames[phys_addr]

    def write(self, process, virtual_address, value):
        phys_addr = self.translate_address(process, virtual_address)
        self.physical_memory.frames[phys_addr] = value
