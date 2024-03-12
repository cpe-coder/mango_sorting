import cv2
import numpy as np
from pymongo import MongoClient

client = MongoClient('mongodb+srv://mango:mangosorting@cluster0.cfbv67j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  
db = client['test']
collection = db['mango_records']

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
        collection.insert_one(document)
        
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

    for color_range, label in zip([ripe_color_range, raw_color_range], ["Ripe", "Raw"]):
        mask = cv2.inRange(hsvImage, color_range[0], color_range[1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  
                x, y, w, h = cv2.boundingRect(contour)
                fruit_type = classify_color(hsvImage[y + h // 2, x + w // 2])
                fruit_size = classify_size(area)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
               
                cv2.putText(frame,  f'{area:.1f} cm', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f'Status: {fruit_type}', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, f'Size: {fruit_size}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                update_database(fruit_type, fruit_size)

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
