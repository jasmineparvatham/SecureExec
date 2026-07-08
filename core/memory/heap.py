from core.errors import VMError

class HeapManager:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.heap_table = {}
        self.next_block_id = 1

    def allocate(self, process, size):
        if size <= 0:
            raise VMError("Invalid heap allocation size")

        # 1. Try to reuse a freed block (First-fit)
        for block_id, block in self.heap_table.items():
            if block["owner_pid"] == process.pid and not block["allocated"] and block["size"] >= size:
                block["allocated"] = True
                process.heap_allocations[block_id] = block
                return block["start_address"]

        # 2. Allocate new virtual memory pages
        start_addr = process.virtual_memory_size
        page_size = self.memory_manager.page_size
        num_pages = (size + page_size - 1) // page_size

        if len(self.memory_manager.free_frames) < num_pages:
            raise VMError("Out of physical memory for heap allocation")

        current_pages = len(process.page_table.mapping)
        for i in range(num_pages):
            p_frame = self.memory_manager.free_frames.pop(0)
            process.page_table.mapping[current_pages + i] = p_frame

        process.virtual_memory_size += num_pages * page_size

        # 3. Track block
        block_id = self.next_block_id
        self.next_block_id += 1

        block = {
            "start_address": start_addr,
            "size": size,
            "owner_pid": process.pid,
            "allocated": True
        }

        self.heap_table[block_id] = block
        process.heap_allocations[block_id] = block

        return start_addr

    def free(self, process, ptr):
        target_block_id = None
        for block_id, block in process.heap_allocations.items():
            if block["start_address"] == ptr:
                target_block_id = block_id
                break

        if not target_block_id:
            raise VMError(f"Invalid free or double free at address {ptr}")

        if not self.heap_table[target_block_id]["allocated"]:
            raise VMError(f"Double free detected at address {ptr}")

        self.heap_table[target_block_id]["allocated"] = False
        del process.heap_allocations[target_block_id]

    def process_exit(self, process):
        # Auto-free leaked memory blocks belonging to process
        to_remove = []
        for block_id, block in self.heap_table.items():
            if block["owner_pid"] == process.pid:
                to_remove.append(block_id)
        for bid in to_remove:
            del self.heap_table[bid]
