import cv2
import pickle
import numpy as np
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Resolution matches your training data/detector.py
WIDTH, HEIGHT = 240, 386  

# Change these for each wing (W1, W2, etc.)
image_path = '../dataset/train/W8.jpg' 
pos_file = 'config/W8.pkl'

MICRO_STEP = 10 

# ==========================================
# 2. STATE VARIABLES
# ==========================================
scale = 1.0
pan_x, pan_y = 0, 0
is_dragging = False
drag_start = (0, 0)

current_points = []
mouse_pos_raw = (0, 0)
pos_list = []

# Load existing data if it exists
if os.path.exists(pos_file):
    with open(pos_file, 'rb') as f:
        try:
            pos_list = pickle.load(f)
            print(f"Loaded {len(pos_list)} slots from {pos_file}")
        except: 
            pos_list = []

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def draw_ruler(img, s, px, py):
    color = (200, 200, 200)
    # Horizontal
    cv2.line(img, (0, 20), (WIDTH, 20), color, 1)
    for x in range(0, WIDTH, 50):
        pos = int(x * s + px)
        cv2.line(img, (pos, 15), (pos, 25), color, 1)
        # Use smaller font for small resolution
        cv2.putText(img, str(x), (pos, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    # Vertical
    cv2.line(img, (20, 0), (20, HEIGHT), color, 1)
    for y in range(0, HEIGHT, 50):
        pos = int(y * s + py)
        cv2.line(img, (15, pos), (25, pos), color, 1)
        cv2.putText(img, str(y), (2, pos + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

def mouse_click(event, x, y, flags, param):
    global current_points, mouse_pos_raw, pos_list, scale, pan_x, pan_y, is_dragging, drag_start
    
    # Convert Screen Coords -> Image Coords
    img_x = int((x - pan_x) / scale)
    img_y = int((y - pan_y) / scale)
    mouse_pos_raw = (img_x, img_y)

    # ZOOM
    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0: scale *= 1.1
        else: scale /= 1.1

    # PAN
    elif event == cv2.EVENT_MBUTTONDOWN:
        is_dragging = True
        drag_start = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE:
        if is_dragging:
            pan_x += (x - drag_start[0])
            pan_y += (y - drag_start[1])
            drag_start = (x, y)
    elif event == cv2.EVENT_MBUTTONUP:
        is_dragging = False

    # DRAW (Left Click)
    elif event == cv2.EVENT_LBUTTONDOWN and not is_dragging:
        current_points.append((img_x, img_y))
        
    # FINISH SLOT (Double Click)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        if len(current_points) >= 3:
            pos_list.append(current_points) 
            current_points = []
            print(f"Slot {len(pos_list)} saved!")
            
    # REMOVE SLOT (Right Click)
    elif event == cv2.EVENT_RBUTTONDOWN:
        if current_points: 
            current_points.pop() # Undo last point
        else:
            # Check if clicked inside a completed box
            for i, pts_list in enumerate(pos_list):
                pts = np.array(pts_list, np.int32)
                if cv2.pointPolygonTest(pts, (img_x, img_y), False) >= 0:
                    pos_list.pop(i)
                    print(f"Removed Slot {i+1}. Renumbering...")
                    break

# ==========================================
# 4. MAIN LOOP
# ==========================================
cv2.namedWindow("Picker 240x386", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Picker 240x386", 800, 600) # Window size for your monitor
cv2.setMouseCallback("Picker 240x386", mouse_click)

print("--- CONTROLS ---")
print("Left Click: Add Point")
print("Double Click: Finish Box")
print("Right Click: Remove Box / Undo Point")
print("Scroll Wheel: Zoom")
print("Middle Click + Drag: Pan")
print("S: Save")
print("Q: Quit")

while True:
    img_base = cv2.imread(image_path)
    if img_base is None:
        # Create black canvas if image not found
        img_base = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
        cv2.putText(img_base, "Img Not Found", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
    
    # 1. Resize Image to Project Resolution
    workspace = cv2.resize(img_base, (WIDTH, HEIGHT))
    
    # Draw Grid
    for x in range(0, WIDTH, MICRO_STEP):
        cv2.line(workspace, (x, 0), (x, HEIGHT), (40, 40, 40), 1)
    for y in range(0, HEIGHT, MICRO_STEP):
        cv2.line(workspace, (0, y), (WIDTH, y), (40, 40, 40), 1)

    # 2. Draw Completed Slots with Numbers
    for i, pts_list in enumerate(pos_list):
        pts = np.array(pts_list, np.int32)
        cv2.polylines(workspace, [pts], True, (0, 255, 0), 1)
        
        # Calculate Center
        M = cv2.moments(pts)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = pts[0]
            
        # Draw Number
        label = str(i + 1)
        # Black border for contrast
        cv2.putText(workspace, label, (cx-5, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2)
        # White text
        cv2.putText(workspace, label, (cx-5, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 3. Draw Active Drawing
    if current_points:
        cv2.polylines(workspace, [np.array(current_points, np.int32)], False, (0, 255, 255), 1)
        cv2.line(workspace, current_points[-1], mouse_pos_raw, (0, 255, 255), 1)

    # 4. Apply Zoom & Pan
    M_mat = np.float32([[scale, 0, pan_x], [0, scale, pan_y]])
    display_img = cv2.warpAffine(workspace, M_mat, (WIDTH, HEIGHT))

    # Overlays
    draw_ruler(display_img, scale, pan_x, pan_y)
    cv2.putText(display_img, f"Slots: {len(pos_list)} | {WIDTH}x{HEIGHT}", 
                (10, HEIGHT-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    cv2.imshow("Picker 240x386", display_img)
    
    key = cv2.waitKey(1)
    if key == ord('s'):
        with open(pos_file, 'wb') as f:
            pickle.dump(pos_list, f)
        print(f"Saved {len(pos_list)} slots to {pos_file}")
    elif key == ord('r'): # Reset View
        scale, pan_x, pan_y = 1.0, 0, 0
    elif key == ord('q'):
        break

cv2.destroyAllWindows()