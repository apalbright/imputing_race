# ---------------------------------------------------------
# Main Master Script - PPP
# Created by: Weiran
# Date: 03/31/2026
# Description: PPP-specific counterpart to 03_NamePrism_predict.py
#              Runs PPP NamePrism race imputation scripts in sequence
# ---------------------------------------------------------

import os
import subprocess
import sys

# Set base directory (assumes you run from project root)
base_dir = os.getcwd()

# Define global paths
dta   = os.path.join(base_dir, "Data")
ans   = os.path.join(base_dir, "Results")
codes = os.path.join(base_dir, "src")

# Helper to run Python scripts
def run_script(path):
    print(f"Running: {path}")
    subprocess.run([sys.executable, path], check=True)

# Run scripts
run_script(os.path.join(codes, "sub", "PPP_NamePrism_predict.py"))
