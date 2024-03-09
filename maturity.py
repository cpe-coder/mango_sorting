import cv2
import numpy as np
from PIL import Image
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mangosorting-default-rtdb.firebaseio.com/'
})

ripe_color_range = (np.array([15, 100, 100]), np.array([45, 255, 255]))  # Yellow range in HSV
raw_color_range = (np.array([45, 100, 100]), np.array([85, 255, 255]))   # Green range in HSV

size_categories = ["small", "medium", "large"]

def classify_color(hsv_value):
    if (ripe_color_range[0][0] <= hsv_value[0] <= ripe_color_range[1][0]) or \
       (ripe_color_range[0][0] <= (hsv_value[0] + 180) <= ripe_color_range[1][0]):
        return "Ripe"
    elif (raw_color_range[0][0] <= hsv_value[0] <= raw_color_range[1][0]) or \
         (raw_color_range[0][0] <= (hsv_value[0] + 180) <= raw_color_range[1][0]):
        return "Raw"
    else:
        return "Unknown"

def classify_size(contour_area):
    if contour_area <= 7:
        return "small"
    elif 8 <= contour_area <= 12:
        return "medium"
    else:
        return "large"

# Calibration
def calibrate_conversion_factor(image_path, known_size_cm):
    img = cv2.imread(image_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)  # Adjust parameters as needed
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    widths = []
    heights = []
    
    # Loop over the contours
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 100:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        widths.append(w)
        heights.append(h)
    avg_width = np.mean(widths)
    avg_height = np.mean(heights)
    avg_reference_size_pixels = (avg_width + avg_height) / 2  # Use average width and height
    conversion_factor = known_size_cm / avg_reference_size_pixels
    
    return conversion_factor

conversion_factor = 0.1  # Placeholder value, replace with calibrated value

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

ref_status = db.reference('/mango/1/status')
ref_size = db.reference('/mango/1/size')

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to retrieve frame from video capture.")
        break

    hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    fruit_status = "Unknown"
    fruit_size = "Unknown"

    for color_range in [ripe_color_range, raw_color_range]:
        mask = cv2.inRange(hsvImage, color_range[0], color_range[1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum area threshold to consider
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    hsv_value = hsvImage[y + h // 2, x + w // 2]
                    fruit_status = classify_color(hsv_value)
                    fruit_size = classify_size(area)

                    object_size_cm = area * conversion_factor
                    cv2.putText(frame, f"{object_size_cm:.1f} cm", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    ref_status.set(fruit_status)
    ref_size.set(fruit_size)

    cv2.putText(frame, f"Status: {fruit_status}", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(frame, f"Size: {fruit_size}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()