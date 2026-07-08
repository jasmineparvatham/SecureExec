class RuntimeLogger:
    def __init__(self, debug=False):
        self.debug_mode = debug
        self.logs = []

    def log(self, component, message):
        if self.debug_mode:
            out = f"[{component}]: {message}"
            self.logs.append(out)
            print(out)
