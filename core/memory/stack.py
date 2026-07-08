class StackFrame:
    def __init__(self, return_ip, base_pointer):
        self.return_ip = return_ip
        self.base_pointer = base_pointer
