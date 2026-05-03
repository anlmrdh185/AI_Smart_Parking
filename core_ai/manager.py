import subprocess
import time

wings = ["W1", "W5", "W3A", "W7", "W8", "M10"]
processes = []

print("--- AI Smart Parking Multi-Stream Engine ---")
print(f"Launching {len(wings)} wings...")

for wing_id in wings:
    # Decide which detector to use
    if wing_id == "M10":
        script = "detector_m.py"
    else:
        script = "detector.py"

    # Run the correct script
    p = subprocess.Popen(['python', script, '--wing', wing_id])
    processes.append(p)

    print(f"Started {script} for {wing_id}")
    time.sleep(2)

print("\nAll systems active. Press Ctrl+C to stop all.")

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down all streams...")
    for p in processes:
        p.terminate()
