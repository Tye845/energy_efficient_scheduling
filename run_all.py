import subprocess
import sys
from pathlib import Path

# Combinations of inputs, modes, and flags
inputs = ["input1.txt", "input2.txt"]
modes = ["rm", "edf"]
flags = ["", "ee"]

# Create output directory if it doesn't exist
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Iterate over all combinations and run pa3.py
for inp in inputs:
    for mode in modes:
        for flag in flags:
            args = [sys.executable, "pa3.py", inp, mode]

            if flag:
                args.append(flag)

            print("Running:", " ".join(args))
            result = subprocess.run(args, capture_output=True, text=True)
            
            # Save output file
            out_name = f"out_{inp.split('.')[0]}_{mode}{'_' + flag if flag else ''}.txt"
            with open(output_dir / out_name, "w") as f:
                f.write(result.stdout)

            # Save stderr if any to file
            if result.stderr:
                with open(output_dir / out_name.replace(".txt", "_stderr.txt"), "w") as f:
                    f.write(result.stderr)