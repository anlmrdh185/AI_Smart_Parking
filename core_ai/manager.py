import subprocess
import time

# List of your 5 wings
wings = ["W3A", "W5", "W1", "W7", "W8"]

processes = []

print("--- AI Smart Parking Multi-Stream Engine ---")
print(f"Launching {len(wings)} wings...")

for wing_id in wings:
    # Launches detector.py with the wing argument
    # 'python' might need to be 'python3' depending on your OS
    p = subprocess.Popen(['python', 'detector.py', '--wing', wing_id])
    processes.append(p)
    print(f"Started stream for {wing_id}")
    time.sleep(2) # Short delay to prevent CPU spike during loading

print("\nAll systems active. Press Ctrl+C in this terminal to stop all.")

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down all streams...")
    for p in processes:
        p.terminate()