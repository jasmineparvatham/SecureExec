class VMConfig:
    def __init__(self, memory_size=256, register_count=8, max_program_size=10000, instruction_limit=50000):
        self.memory_size = memory_size
        self.register_count = register_count
        self.max_program_size = max_program_size
        self.instruction_limit = instruction_limit
