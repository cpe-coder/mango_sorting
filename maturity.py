import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mangosorting-default-rtdb.firebaseio.com/'
})

ripe_color_range = (np.array([15, 100, 100]), np.array([45, 255, 255]))  # Yellow range in HSV
raw_color_range = (np.array([45, 100, 100]), np.array([85, 255, 255]))   # Green range in HSV

def classify_color(hsv_value):
    if ripe_color_range[0][0] <= hsv_value[0] <= ripe_color_range[1][0]:
        return "Ripe"
    elif raw_color_range[0][0] <= hsv_value[0] <= raw_color_range[1][0]:
        return "Raw"
    return "Unknown"

def classify_size(contour_area):
    if contour_area < 10000:
        return "small"
    elif 10000 <= contour_area <= 30000:
        return "medium"
    else:
        return "large"

def update_database(fruit_type, fruit_size):
    if fruit_type == "Unknown":
        print("Skipped updating database for unknown fruit type.")
        return 
    maturity_status = {"Ripe": True, "Raw": False} if fruit_type == "Ripe" else {"Ripe": False, "Raw": True}
    db.reference('/mango/1/ripe/maturity').set(maturity_status["Ripe"])
    db.reference('/mango/1/raw/maturity').set(maturity_status["Raw"])
    if maturity_status[fruit_type]:
        size_path = f'/mango/1/{fruit_type.lower()}/size'
        db.reference(size_path).set(fruit_size)

valid_camera = False
for camera_index in range(4):
    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        valid_camera = True
        print(f"Using camera index: {camera_index}")
        break
if not valid_camera:
    print("Error: Could not find a valid camera index.")
    exit()

previous_fruit_type = None
previous_fruit_size = None

while True:
    ret, frame = cap.read()
    if not ret:
        break  # Break the loop if we can't get a frame

    hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    for color_range, label in zip([ripe_color_range, raw_color_range], ["Ripe", "Raw"]):
        mask = cv2.inRange(hsvImage, color_range[0], color_range[1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Filter out too small areas
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                frame_height, frame_width = frame.shape[:2]

                if (frame_width * 0.4 < center_x < frame_width * 0.6) and (frame_height * 0.4 < center_y < frame_height * 0.6):
                    fruit_type = classify_color(hsvImage[center_y, center_x])
                    fruit_size = classify_size(area)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                   
                    cv2.putText(frame,  f'{area:.1f} cm', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f'Status: {fruit_type}', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(frame, f'Size: {fruit_size}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if fruit_type != previous_fruit_type or fruit_size != previous_fruit_size:
                        update_database(fruit_type, fruit_size)
                        previous_fruit_type = fruit_type
                        previous_fruit_size = fruit_size

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
