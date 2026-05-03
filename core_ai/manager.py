import subprocess
import time
from database import initialize_slots

wings = ["W1", "W5", "W3A", "W7", "W8", "M10"]
processes = []

print("--- AI Smart Parking Multi-Stream Engine ---")
print(f"Launching {len(wings)} wings...")

# =========================================
# 🚀 STEP 1: INITIALIZE ALL SLOTS
# =========================================
print("\n🚀 Initializing all parking slots...")

# Define how many slots each wing has
wing_slots = {
    "W1": 10,
    "W5": 15,
    "W3A": 12,
    "W7": 8,
    "W8": 10,
    "M10": 10
}

for wing_id in wings:
    total = wing_slots.get(wing_id, 10)  # default 10 if not defined
    initialize_slots(wing_id, total)

print("✅ All slots initialized!\n")

# =========================================
# 🚀 STEP 2: START DETECTORS
# =========================================
for wing_id in wings:

    if wing_id == "M10":
        script = "detector_m.py"
    else:
        script = "detector.py"

    p = subprocess.Popen(['python', script, '--wing', wing_id])
    processes.append(p)

    print(f"Started {script} for {wing_id}")
    time.sleep(2)

print("\nAll systems active. Press Ctrl+C to stop all.")

# =========================================
# 🛑 STOP HANDLING
# =========================================
try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down all streams...")
    for p in processes:
        p.terminate()
