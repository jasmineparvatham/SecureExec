class PhysicalMemory:
    def __init__(self, size=65536):
        self.frames = [0] * size
