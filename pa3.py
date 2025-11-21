import sys
from itertools import product

# CPU frequency + power table (index aligned with WCET)
FREQUENCIES = [1188, 918, 648, 384]

class Task:
    def __init__(self, name, period, wcet_list):
        self.name = name
        self.period = period
        self.wcet = wcet_list  # [wcet_1188, wcet_918, wcet_648, wcet_384]
        self.freq_idx = 0      # 0 = 1188 MHz set as default 

class Job:
    def __init__(self, task, release_time, deadline):
        self.task = task
        self.release_time = release_time
        self.deadline = deadline
        self.remaining_time = task.wcet[0]  # default = fastest

def parse_input_file(filename):
    with open(filename, "r") as f:
        data = f.read().strip().split()

    idx = 0
    num_tasks = int(data[idx]); idx += 1
    simulation_time = int(data[idx]); idx += 1

    # Powers in the same order as FREQUENCIES
    power_1188 = int(data[idx]); idx += 1
    power_918  = int(data[idx]); idx += 1
    power_648  = int(data[idx]); idx += 1
    power_384  = int(data[idx]); idx += 1
    idle_power = int(data[idx]); idx += 1

    power_table = {
        1188: power_1188,
        918: power_918,
        648: power_648,
        384: power_384,
        "IDLE": idle_power
    }

    tasks = []
    for _ in range(num_tasks):
        name = data[idx]; idx += 1
        period = int(data[idx]); idx += 1
        wcets = []

        for _ in range(4):
            wcets.append(int(data[idx]))
            idx += 1

        tasks.append(Task(name, period, wcets))

    return num_tasks, simulation_time, power_table, tasks


# Create all job instances for the whole simulation time
def generate_jobs(tasks, simulation_time):
    jobs = []

    for t in tasks:
        release = 0
        while release < simulation_time:
            deadline = release + t.period
            jobs.append(Job(t, release, deadline))
            release += t.period

    return jobs

def count_jobs(task, simulation_time):
    """How many jobs of this task are released in [0, simulation_time)."""
    count = 0
    t = 0
    while t < simulation_time:
        count += 1
        t += task.period
    return count

def select_frequencies_for_tasks(tasks, power_table, simulation_time, mode):
    """
    Offline EE selection: choose one freq index per task to minimize
    total energy over the simulation, subject to sum(U_i) <= 1.
    """
    num_freqs = len(FREQUENCIES)
    num_tasks = len(tasks)

    # precompute #jobs per task
    jobs_per_task = [count_jobs(task, simulation_time) for task in tasks]
    
    if mode == "EDF":
        run_schedule_limit = 1.0
    else:
        run_schedule_limit = num_tasks * (2**(1/num_tasks) - 1)
        
    best_energy = float("inf")
    best_combo = None

    # Try every combination of frequencies (Ci) for each task
    for combo in product(range(num_freqs), repeat=num_tasks):
        total_U = 0.0
        total_E = 0.0

        ok = True
        for task, freq_idx, njobs in zip(tasks, combo, jobs_per_task):
            C = task.wcet[freq_idx]
            total_U += C / task.period
            if total_U > run_schedule_limit:   # schedulability constraint
                ok = False
                break

            freq = FREQUENCIES[freq_idx]
            P = power_table[freq]  # mW
            total_E += njobs * C * P  # mJ

        if not ok:
            continue

        if total_E < best_energy:
            best_energy = total_E
            best_combo = combo

    # If nothing found (shouldn't happen with this input), fall back to max speed
    if best_combo is None:
        best_combo = tuple(0 for _ in tasks)

    # Assign chosen freq_idx to each task
    for task, freq_idx in zip(tasks, best_combo):
        task.freq_idx = freq_idx

# EDF scheduler: choose job with earliest deadline
def edf_select(ready_jobs):
    if not ready_jobs:
        return None
    return min(ready_jobs, key=lambda job: job.deadline)


# RM scheduler: choose job with smallest period
def rm_select(ready_jobs):
    if not ready_jobs:
        return None
    return min(ready_jobs, key=lambda job: job.task.period)


# The simulation loop (shared for EDF/RM)
def run_schedule(simulation_time, jobs, power_table, mode="EDF"):
    timeline = []
    current_time = 0

    # Sort jobs by release time (they all start at release_time)
    jobs = sorted(jobs, key=lambda j: j.release_time)

    ready = []           # ready queue
    running = None       # currently running job
    
    while current_time < simulation_time:
        # Check for deadline misses
        active_jobs_to_check = set(ready)
        if running:
            active_jobs_to_check.add(running)
        for j in active_jobs_to_check:
            if current_time == j.deadline and j.remaining_time > 0:
                print(f"\n--- SIMULATION FAILED ---")
                print(f"ERROR: Task {j.task.name} (released at {j.release_time}) missed its deadline at time {current_time}.")
                print(f"       Task still had {j.remaining_time}s of work remaining.\n")
                return timeline

        # Release jobs at this time
        for j in list(jobs):
            if j.release_time == current_time:
                # reset remaining time at chosen frequency
                j.remaining_time = j.task.wcet[j.task.freq_idx]
                ready.append(j)
                jobs.remove(j)

        # If running job finished, remove it
        if running and running.remaining_time <= 0:
            ready.remove(running)
            running = None

        # Choose highest-priority job (EDF or RM) and preempt if necessary
        if mode == "EDF":
            pick = edf_select(ready)
        else:
            pick = rm_select(ready)

        # If RM/EDF picks a new job then preempt
        if pick is not None and pick != running:
            running = pick

        # If CPU idle
        if running is None:
            duration = 1
            idle_energy = power_table["IDLE"] * duration / 1000.0
            timeline.append((current_time, "IDLE", "IDLE", duration, idle_energy))
            current_time += 1
            continue

        # Run selected job for 1 time unit
        freq = FREQUENCIES[running.task.freq_idx]   # 1188 or 918 or 648 or 384
        power = power_table[freq]

        running.remaining_time -= 1

        energy = power * 1 / 1000.0
        timeline.append((current_time, running.task.name, freq, 1, energy))

        current_time += 1

    return timeline

# print the job timeline
def print_timeline(timeline):
    if not timeline:
        return

    total_energy = 0
    idle_time = 0

    # Compress 1-second slices into longer intervals
    compressed = []
    
    # Start with first entry
    cur_start, cur_task, cur_freq, _, cur_energy = timeline[0]
    cur_duration = 1

    for i in range(1, len(timeline)):
        t, task, freq, dur, energy = timeline[i]

        # If same task + same freq and consecutive second then merge
        if task == cur_task and freq == cur_freq and t == (cur_start + cur_duration):
            cur_duration += 1
            cur_energy += energy
            
        else:
            # push previous interval
            compressed.append((cur_start, cur_task, cur_freq, cur_duration, cur_energy))

            # start new
            cur_start = t
            cur_task = task
            cur_freq = freq
            cur_duration = 1
            cur_energy = energy

    # push last interval
    compressed.append((cur_start, cur_task, cur_freq, cur_duration, cur_energy))

    # print final timeline
    for entry in compressed:
        start, task, freq, duration, energy = entry
        print(f"{start:<5} {task:<5} {freq:<5} {duration:<5} {energy:.3f}J")
        total_energy += energy
        if task == "IDLE":
            idle_time += duration

    # Summary
    total_time = compressed[-1][0] + compressed[-1][3]
    idle_percentage = (idle_time / total_time) * 100

    print("\n--- Summary ---")
    print(f"Total energy: {total_energy:.3f} J")
    print(f"Idle percentage: {idle_percentage:.2f}%")
    print(f"Total execution time: {total_time} s")

if __name__ == "__main__":
    input_file = sys.argv[1]
    mode = sys.argv[2]  # EDF or RM

    num_tasks, simulation_time, power_table, tasks = parse_input_file(input_file)

    # Optional EE flag
    ee_mode = (len(sys.argv) >= 4 and sys.argv[3].upper() == "EE")

    if ee_mode:
        select_frequencies_for_tasks(tasks, power_table, simulation_time, mode)
    else:
        # baseline with everyone at max freq
        for t in tasks:
            t.freq_idx = 0

    jobs = generate_jobs(tasks, simulation_time)

    timeline = run_schedule(simulation_time, jobs, power_table, mode)
    print_timeline(timeline)