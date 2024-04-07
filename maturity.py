import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mangosorting-default-rtdb.firebaseio.com/'
})

# Initialize MongoDB client and database
# mongo_client = MongoClient('mongodb+srv://mango:mangosorting@cluster0.cfbv67j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
# mongo_db = mongo_client['test']
# mongo_collection_ripe = mongo_db['ripe_mangoes']
# mongo_collection_raw = mongo_db['raw_mangoes']

# Define color ranges
ripe_color_range = (np.array([15, 100, 100]), np.array([45, 255, 255]))  # Yellow range in HSV
raw_color_range = (np.array([45, 100, 100]), np.array([85, 255, 255]))   # Green range in HSV

# Function to classify color based on HSV value
def classify_color(hsv_value):
    if ripe_color_range[0][0] <= hsv_value[0] <= ripe_color_range[1][0]:
        return "Ripe"
    elif raw_color_range[0][0] <= hsv_value[0] <= raw_color_range[1][0]:
        return "Raw"
    return "Unknown"


# Function to save data to MongoDB
# def save_to_mongodb(collection, data):
    # collection.insert_one(data)

# Function to save data to Firebase Realtime Database
def save_to_firebase(fruit_type):
    if fruit_type == "Unknown":
        print("Skipped updating database for unknown fruit type.")
        return 
    maturity_status = {"Ripe": True, "Raw": False} if fruit_type == "Ripe" else {"Ripe": False, "Raw": True}
    db.reference('/mango/1/ripe').set(maturity_status["Ripe"])
    db.reference('/mango/1/raw').set(maturity_status["Raw"])

# Check camera availability
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

# Main loop
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

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f'Status: {fruit_type}', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if fruit_type != previous_fruit_type:
                        # save_to_mongodb(mongo_collection_ripe if fruit_type == "Ripe" else mongo_collection_raw, {"fruit_type": fruit_type, "fruit_size": fruit_size})
                        save_to_firebase(fruit_type)
                        previous_fruit_type = fruit_type
    cv2.imshow('Mango Maturity', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
