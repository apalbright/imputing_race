### Python
#conda create --name myenv6 python=3.12
#conda activate myenv6


#pip install numpy pandas requests time


import pandas as pd
import requests
import time
import os
from urllib.parse import quote

# Path setup
# __file__ gives the current script location (main/src/sub)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Go up two levels: from sub -> src -> main
project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))

# Data folder lives at main/Data
data_dir = os.path.join(project_root, "Data")


# Prepare
# Replace your API key here
apiKey = "9b2777f6e63e7fd8"
dataname = "PPP_NamePrism.csv"
colname = "fullname"

def load_data():
    data_test = pd.read_csv(os.path.join(data_dir, dataname))
    return data_test[colname]

x_test = load_data()

print(f"Loaded {len(x_test)} names")

output_file = os.path.join(data_dir, "PPP_NamePrism_res.csv")
delay = 0.5         # Delay in seconds between API requests
max_retries = 3
flush_every = 500   # Flush partial results to disk every N successful records

# Resume from any existing partial output so a restart doesn't redo finished work
results_list = []
done_idx = set()
if os.path.exists(output_file):
    try:
        existing = pd.read_csv(output_file)
        if "A" in existing.columns:
            results_list = existing.to_dict("records")
            done_idx = set(existing["A"].astype(int).tolist())
            print(f"Resuming: {len(done_idx)} records already in {output_file}")
    except Exception as e:
        print(f"Could not read existing {output_file}, starting fresh: {e}")

def flush_to_disk():
    pd.DataFrame(results_list).to_csv(output_file, index=False)

start_time = time.time()
# Predict race
for i, name in enumerate(x_test):
    if i in done_idx:
        continue

    # Pre-filter blanks / NaN so they don't crash the request path
    if not isinstance(name, str) or not name.strip():
        print(f"Skipping index {i}: empty/NaN name", flush=True)
        continue

    elapsed = time.time() - start_time
    print(f"Processing index {i}, name: {name}, elapsed: {elapsed:.2f}s", flush=True)

    parts = name.split()
    if len(parts) >= 2:
        firstname, lastname = parts[0], " ".join(parts[1:])
    else:
        firstname, lastname = parts[0], ""

    # URL-encode the name so apostrophes / accents / ampersands / slashes don't break the path
    fullname_q = quote(f"{firstname} {lastname}".strip(), safe="")
    url = f"http://www.name-prism.com/api_token/eth/csv/{apiKey}/{fullname_q}"

    # Retry transient failures so one hiccup over a multi-day run doesn't drop a record
    response = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                break
            print(f"Status {response.status_code} for {name} (attempt {attempt+1})")
        except Exception as e:
            print(f"Request error for {name} (attempt {attempt+1}): {e}")
        time.sleep(1 + attempt)

    if response is None or response.status_code != 200:
        print(f"Giving up on {name} after {max_retries} attempts")
        time.sleep(delay)
        continue

    # splitlines() handles CRLF; strip() removes any stray whitespace that would break Stata destring
    lines = [ln.strip() for ln in response.text.splitlines() if ln.strip()]
    if len(lines) < 6:
        print(f"Unexpected response format for {name}: {response.text!r}")
        time.sleep(delay)
        continue

    results_list.append({
        'A': i,
        'B': lines[0],
        'C': lines[1],
        'D': lines[2],
        'E': lines[3],
        'F': lines[4],
        'G': lines[5],
    })

    # Periodic flush so a crash at hour 50 doesn't lose progress
    if len(results_list) % flush_every == 0:
        flush_to_disk()
        print(f"Flushed {len(results_list)} records to {output_file}", flush=True)

    time.sleep(delay)

# Final save
flush_to_disk()
print(f"Results saved to {output_file}")
