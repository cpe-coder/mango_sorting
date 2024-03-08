from scipy.spatial.distance import euclidean
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2

# Function to calculate distance in inches
def calculate_distance(ref_height, focal_length, pixel_height):
    # Calculate distance to the object in inches using the formula: distance = (ref_height * focal_length) / pixel_height
    distance_inches = (ref_height * focal_length) / pixel_height
    return distance_inches

# Capture video from camera
cap = cv2.VideoCapture(0)

# Reference object height in inches (e.g., a standard credit card's height)
ref_height_inches = 3.37007874  # Standard credit card height in inches

# Known distance from camera to object (in inches) when reference object's height was measured
known_distance = 12  # 1 foot (12 inches)

# Known object's width in the same units as ref_height_inches (inches)
known_width = 2.125  # Standard credit card width in inches

while True:
    # Read frame from camera
    ret, frame = cap.read()
    
    if not ret:
        print("Error reading frame from camera.")
        break
    
    # Preprocess frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    edged = cv2.Canny(blur, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # Find contours
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # Ensure at least one contour is found
    if cnts:
        # Sort contours by area in descending order
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        largest_contour = cnts[0]

        # Get bounding box of the largest contour
        box = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(box)
        box = np.array(box, dtype="int")
        box = perspective.order_points(box)
        (tl, tr, br, bl) = box

        # Calculate height of the object in pixels
        pixel_height = euclidean(tl, bl)

        # Calculate focal length (in pixels) using the known distance and width of the reference object
        focal_length = (known_distance * pixel_height) / known_width

        # Calculate distance to the object in inches
        distance_inches = calculate_distance(ref_height_inches, focal_length, pixel_height)

        # Draw bounding box and display height on the image
        cv2.drawContours(frame, [box.astype("int")], -1, (0, 0, 255), 2)
        mid_pt_vertical = (tr[0] + int(abs(tr[0] - br[0]) / 2), tr[1] + int(abs(tr[1] - br[1]) / 2))
        cv2.putText(frame, "{:.1f} inches".format(distance_inches), (int(mid_pt_vertical[0] + 10), int(mid_pt_vertical[1])),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    # Display the frame
    cv2.imshow("Frame", frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()
