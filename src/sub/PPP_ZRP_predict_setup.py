# ---------------------------------------------------------
# Sub ZRP Script - PPP
# Created by: Weiran
# Date: 03/31/2026
# Description: Called by 03_ZRP_PPP.ipynb. Runs PPP ZRP setup scripts
# ---------------------------------------------------------

import os
import subprocess
import sys

# Set base directory (assumes you run from project root)
base_dir = os.getcwd()

# Define project paths
data  = os.path.join(base_dir, "Data")
ans   = os.path.join(base_dir, "Results")
codes = os.path.join(base_dir, "src")

# Helper to run Python scripts
def run_script(path):
    print(f"Running: {path}")
    subprocess.run(["python", path], check=True)

# Run scripts
run_script(os.path.join(codes, "sub", "PPP_ZRP_predict.py"))
