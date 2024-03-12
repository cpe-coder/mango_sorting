import cv2
import numpy as np
from pymongo import MongoClient

client = MongoClient('mongodb+srv://mango:mangosorting@cluster0.cfbv67j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  
db = client['test']
collection_ripe = db['ripe_mangoes']
collection_raw = db['raw_mangoes']

ripe_color_range = (np.array([15, 100, 100]), np.array([45, 255, 255]))  
raw_color_range = (np.array([45, 100, 100]), np.array([85, 255, 255]))   

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

previous_fruit_type = None
previous_fruit_size = None

def update_database(fruit_type, fruit_size):
    global previous_fruit_type, previous_fruit_size
    
    if fruit_type == "Unknown":
        print("Skipped updating database for unknown fruit type.")
        return 
    
    # Check if the current mango is the same as the previous one
    if fruit_type != previous_fruit_type or fruit_size != previous_fruit_size:
        document = {
            "fruit_type": fruit_type,
            "fruit_size": fruit_size
        }
        if fruit_type == "Ripe":
            collection_ripe.insert_one(document)
        elif fruit_type == "Raw":
            collection_raw.insert_one(document)
        
        # Update the previous fruit type and size
        previous_fruit_type = fruit_type
        previous_fruit_size = fruit_size

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

while True:
    ret, frame = cap.read()
    if not ret:
        break  

    hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Detect contours in the frame
    mask = cv2.inRange(hsvImage, ripe_color_range[0], ripe_color_range[1]) | cv2.inRange(hsvImage, raw_color_range[0], raw_color_range[1])
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Compute the bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2
        frame_height, frame_width = frame.shape[:2]

        # Check if the mango is centered in the frame
        if (frame_width * 0.4 < center_x < frame_width * 0.6) and (frame_height * 0.4 < center_y < frame_height * 0.6):
            area = cv2.contourArea(contour)
            if area > 1000:  
                fruit_type = classify_color(hsvImage[center_y, center_x])
                fruit_size = classify_size(area)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame,  f'{area:.1f} cm', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f'Status: {fruit_type}', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, f'Size: {fruit_size}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                update_database(fruit_type, fruit_size)

    cv2.imshow('Mango Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
