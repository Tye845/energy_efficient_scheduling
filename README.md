# PA3: Real-Time Scheduling Algorithms

## Overview
This assignment implements and evaluates four real-time CPU scheduling algorithms:

1. **Earliest Deadline First (EDF)**  
2. **Earliest Deadline First – Energy Efficient (EDF EE)**  
3. **Rate Monotonic (RM)**  
4. **Rate Monotonic – Energy Efficient (RM EE)**  

Each scheduler simulates task execution over a defined time period using the input workload description provided in `input1.txt` or `input2.txt`. The program records scheduling events, completion times, and any missed deadlines.

## Files
- `pa3.py` – Main program implementing all four scheduling algorithms.  
- `input1.txt`, `input2.txt` – Sample input workloads.  
- `run_all.py` – Convenience script that runs `pa3.py` with every required combination of inputs and modes, printing and saving the output to separate files.  
- `out_input*_*.txt` – Generated simulation results.  
- `out_input*_*.stderr.txt` – Optional error logs (only created if a run outputs to stderr).

## Usage
### Using the `run_all.py` Wrapper
This script automatically runs every combination of:

- Inputs: `input1.txt`, `input2.txt`  
- Modes: `RM`, `EDF`  
- Flags: with and without `EE`  

Run it using:

```bash
python run_all.py
```

This prints all output to the console, as well as produces eight output files:

- `out_input1_RM.txt`  
- `out_input1_RM_EE.txt`  
- `out_input1_EDF.txt`  
- `out_input1_EDF_EE.txt`  
- `out_input2_RM.txt`  
- `out_input2_RM_EE.txt`  
- `out_input2_EDF.txt`  
- `out_input2_EDF_EE.txt`  
### Running `pa3.py` Directly
To execute a specific mode, run:

```bash
python pa3.py <input_file> <mode> [EE]
```

#### Arguments
- `<input_file>`: The input file (e.g., `input1.txt`, `input2.txt`)  
- `<mode>`: Either `RM` or `EDF`  
- `[EE]`: Optional flag for Energy Efficient mode  

#### Examples
```bash
python pa3.py input1.txt RM
python pa3.py input1.txt EDF EE
```

## Output
Each output file contains a chronological log of scheduling decisions, task execution segments, and any deadline misses detected during simulation.

If the program outputs diagnostic messages or exceptions, those are captured in `.stderr.txt` files.
