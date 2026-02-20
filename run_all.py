import subprocess
import time
import os

print("===================================================")
print("     STARTING AI SMART PARKING SYSTEM (FYP)")
print("===================================================")

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_AI_DIR = os.path.join(BASE_DIR, 'core_ai')
MAIN_PY_PATH = os.path.join(CORE_AI_DIR, 'main.py')

processes = []

try:
    # 1. Start the AI Manager
    print("[1/2] Starting AI Multi-Stream Engine...")
    p1 = subprocess.Popen(['python', 'manager.py'], cwd=CORE_AI_DIR)
    processes.append(p1)
    
    # Give the AI 5 seconds to warm up and load the YOLO models
    time.sleep(5)
    
    # 2. Start Streamlit
    print("[2/2] Launching Dashboard...")
    p2 = subprocess.Popen(['streamlit', 'run', MAIN_PY_PATH], cwd=BASE_DIR)
    processes.append(p2)

    print("\n✅ System is running! Press Ctrl+C in this terminal to shut everything down.")
    
    # Keep the script alive
    for p in processes:
        p.wait()

except KeyboardInterrupt:
    print("\n🛑 Shutting down AI Smart Parking System...")
    for p in processes:
        p.terminate()