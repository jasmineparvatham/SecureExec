class PageTable:
    def __init__(self):
        self.mapping = {}  # virtual_page -> physical_frame
