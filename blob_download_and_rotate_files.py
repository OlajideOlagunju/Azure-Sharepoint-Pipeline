import os
import glob
import requests
from datetime import datetime, timezone
from time import sleep

# —— CONFIGURATION ——
BASE_URL   = os.environ["BASE_URL"]
BLOB_NAME  = os.environ["BLOB_NAME"]
SAS_TOKEN  = os.environ["SAS_TOKEN"]
TARGET_DIR = r"C:\VM_Folder"
MAX_FILES  = 90

# —— HELPERS ——
def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def download_blob(retries=3, delay=5):
    ensure_dir(TARGET_DIR)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # sanitize blob name for file system
    safe = BLOB_NAME.replace(" ", "_").replace(".", "_")
    fname = f"{safe}_{today}.csv"
    out_path = os.path.join(TARGET_DIR, fname)

    url = f"{BASE_URL}/{BLOB_NAME}?{SAS_TOKEN}"

    for attempt in range(1, retries + 1):
        resp = requests.get(url)
        if resp.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"[{datetime.now()}] Downloaded to {out_path}")
            return
        else:
            print(f"Attempt {attempt} failed (status {resp.status_code}), retrying in {delay}s…")
            sleep(delay)

    # if we get here, all retries failed
    resp.raise_for_status()

def rotate_files():
    pattern = os.path.join(TARGET_DIR, "*_????-??-??.csv")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for old in files[MAX_FILES:]:
        try:
            os.remove(old)
            print(f"[{datetime.now()}] Removed old file {old}")
        except Exception as e:
            print(f"Could not remove {old}: {e}")

if __name__ == "__main__":
    download_blob()
    rotate_files()