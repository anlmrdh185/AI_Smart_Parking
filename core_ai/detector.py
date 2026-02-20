import cv2
import pickle
import torch
import numpy as np
import time
import argparse
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

try:
    from backend.database import update_slot_status
    print("Successfully connected to Database Module.")
except ImportError as e:
    print(f"Error: {e}")
    print("CRITICAL: Could not find backend/database.py. System will crash on detection.")

# 1. ARGUMENT PARSER
parser = argparse.ArgumentParser()
parser.add_argument('--wing', type=str, default='W1', help='Wing ID (e.g., W1)')
args = parser.parse_args()
W_ID = args.wing

# 2. CONFIGURATION
WIDTH, HEIGHT = 240, 386 
weights_path = 'weights/best.pt'
yolo_repo = '../yolov5'
video_source = f'../dataset/{W_ID}.mp4'   
pickle_path = f'config/{W_ID}.pkl'        

# FSM Settings (Stability & Security)
FRAMES_TO_OCCUPY = 5
FRAMES_TO_VACATE = 30  # Increased for higher security against flickering

# 3. LOAD MODEL & DATA
print(f"[{W_ID}] Loading YOLOv5n Model...")
model = torch.hub.load(yolo_repo, 'custom', path=weights_path, source='local')
model.conf = 0.2

print(f"[{W_ID}] Loading Slot Config: {pickle_path}")
with open(pickle_path, 'rb') as f:
    pos_list = pickle.load(f)

# Track state for each slot
# status: Current confirmed state
# count: FSM counter for transition
slot_states = [{"count": 0, "status": "Vacant"} for _ in range(len(pos_list))]

cap = cv2.VideoCapture(video_source)
frame_counter = 0

print(f"[{W_ID}] Detection Started. Press 'Q' in the video window to stop.")

# ==========================================
# 4. MAIN LOOP
# ==========================================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    frame_counter += 1
    frame_resized = cv2.resize(frame, (WIDTH, HEIGHT))
    
    # Run AI Inference every 3rd frame to save CPU
    if frame_counter % 3 == 0:
        results = model(frame_resized)
        detections = results.xyxy[0].cpu().numpy()

        for i, pts in enumerate(pos_list):
            is_occupied_now = False
            for det in detections:
                xmin, ymin, xmax, ymax, conf, cls = det
                # Calculate center of the detected car
                cx, cy = int((xmin + xmax) / 2), int((ymin + ymax) / 2)
                
                # Check if car center is inside the specific ROI polygon
                if cv2.pointPolygonTest(np.array(pts, np.int32), (cx, cy), False) >= 0:
                    is_occupied_now = True
                    break
            
            # --- FSM LOGIC & DATABASE UPDATE ---
            state = slot_states[i]
            old_confirmed_status = state["status"]
            slot_label = f"{W_ID}-{i+1:02d}"

            if is_occupied_now:
                state["count"] = min(state["count"] + 1, FRAMES_TO_OCCUPY)
                if state["count"] >= FRAMES_TO_OCCUPY:
                    state["status"] = "Occupied"
            else:
                state["count"] = max(state["count"] - 1, -FRAMES_TO_VACATE)
                if state["count"] <= -FRAMES_TO_VACATE:
                    state["status"] = "Vacant"

            # Check if status has officially changed
            if old_confirmed_status != state["status"]:
                print(f"[{W_ID}] Slot {slot_label} changed to {state['status']}")
                # Update Database (Phase 8)
                update_slot_status(W_ID, slot_label, state['status'])

    # --- DRAWING (UI) ---
    # --- DRAWING (UI) ---
    for i, pts in enumerate(pos_list):
        # Red if Occupied, Green if Vacant
        color = (0, 0, 255) if slot_states[i]["status"] == "Occupied" else (0, 255, 0)
        cv2.polylines(frame_resized, [np.array(pts, np.int32)], True, color, 2)
        
        # Draw Slot ID
        cv2.putText(frame_resized, f"{i+1}", (int(pts[0][0]), int(pts[0][1])-5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # THESE ARE THE LINES THAT MAKE THE WINDOW POP UP!
    cv2.imshow(f"Monitoring - {W_ID}", frame_resized)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows() 