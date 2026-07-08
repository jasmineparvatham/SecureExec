"""
You just created:
two queues → q1, q2
rule system → quantum values
counter → for starvation handling later
one VM instance → shared executor
"""

from collections import deque
from core.vm.vm import Virtual_Machine
from core.memory.memory_manager import MemoryManager


class Scheduler:
    def __init__(self, memory_manager=None):
        self.q1 = deque()
        self.q2 = deque()

        self.q1_quantum = 5
        self.q2_quantum = 10

        self.cycle_limit = 2
        self.cycle_count = 0

        self.memory_manager = memory_manager or MemoryManager()
        from os_layer.kernel import Kernel
        self.kernel = Kernel(self.memory_manager, self)
        self.vm = Virtual_Machine(self.memory_manager, self.kernel)

        self.debug = True

        # Metrics
        self.current_time = 0
        self.total_processes_handled = 0
        self.total_scheduling_cycles = 0
        self.context_switch_count = 0
        self.cpu_busy_time = 0
        self.cpu_idle_time = 0
        self.last_run_pid = None
        
        self.completed_processes = []

    def load_processes(self, processes):
        for p in processes:
            self.memory_manager.create_process_memory(p)
            p.creation_time = self.current_time
            p.start()
            self.q1.append(p)
            if self.debug:
                print(f"PID {p.pid} entered Q1")
            self.total_processes_handled += 1

    # run ONE process ONCE
    def run_once(self):
        if self.q1:
            process = self.q1.popleft()
            quantum = self.q1_quantum
            queue_name = "Q1"
        elif self.q2:
            process = self.q2.popleft()
            quantum = self.q2_quantum
            queue_name = "Q2"
        else:
            self.cpu_idle_time += 1
            self.current_time += 1
            if self.debug:
                print("No processes to run")
            return

        if self.last_run_pid != process.pid:
            if self.last_run_pid is not None and self.debug:
                print(f"Context Switch:\nPID {self.last_run_pid} -> PID {process.pid}")
            self.context_switch_count += 1
            self.last_run_pid = process.pid

        if process.first_run_time is None:
            process.first_run_time = self.current_time
            process.response_time = process.first_run_time - process.creation_time

        process.run()
        try:
            process, used, finished = self.vm.run_step(process, quantum)
        except Exception as e:
            if self.debug:
                print(f"Process {process.pid} crashed: {e}")
            process.termination_reason = str(e)
            used = 1
            finished = True
        
        # Advance clock and track wait time for others
        self.current_time += used
        self.cpu_busy_time += used
        
        for p in self.q1:
            p.waiting_time += used
        for p in self.q2:
            p.waiting_time += used

        process.ema = 0.5 * used + 0.5 * process.ema
        process.cpu_time_used += used
        self.total_scheduling_cycles += 1

        if self.debug:
            print(f"From {queue_name}:\nPID {process.pid} Used: {used} instructions")

        if finished:
            if self.debug:
                print(f"Process PID {process.pid} completed and removed")
            process.completion_time = self.current_time
            process.turnaround_time = process.completion_time - process.creation_time
            process.terminate()
            self.memory_manager.release_memory(process)
            self.completed_processes.append(process)
        else:
            process.wait()
            if used == quantum:
                if self.debug:
                    print(f"Moving PID {process.pid} to Q2")
                process.queue_level = 2
                self.q2.append(process)
            else:
                if self.debug:
                    print(f"PID {process.pid} Staying in Q1 (short job)")
                process.queue_level = 1
                self.q1.append(process)

        self.cycle_count += 1

        if self.cycle_count % self.cycle_limit == 0:
            if self.debug and self.q2:
                print("Starvation prevention:\nMoving Q2 processes back to Q1")

            while self.q2:
                p = self.q2.popleft()
                p.queue_level = 1
                self.q1.append(p)

    # run ALL processes until everything finishes
    def run_all(self):
        while self.q1 or self.q2:
            self.run_once()

    def get_statistics(self):
        n = len(self.completed_processes)
        avg_wait = sum(p.waiting_time for p in self.completed_processes) / n if n > 0 else 0
        avg_turnaround = sum(p.turnaround_time for p in self.completed_processes) / n if n > 0 else 0
        avg_response = sum(p.response_time for p in self.completed_processes) / n if n > 0 else 0
        
        total_time = self.cpu_busy_time + self.cpu_idle_time
        cpu_utilization = (self.cpu_busy_time / total_time * 100) if total_time > 0 else 0
        
        return {
            "processes_completed": n,
            "context_switches": self.context_switch_count,
            "cpu_utilization": round(cpu_utilization, 2),
            "average_waiting_time": round(avg_wait, 2),
            "average_turnaround_time": round(avg_turnaround, 2),
            "average_response_time": round(avg_response, 2)
        }
