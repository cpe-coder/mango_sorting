import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()

        # Initialize OpenCV video capture
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 450)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update frame every 30 ms
        
        # Load reference mango images
        self.raw_mango_image = cv2.imread('raw_mango.png')  # Adjust the file path as needed
        self.ripe_mango_image = cv2.imread('ripe_mango.png')  # Adjust the file path as needed

        # Initialize count for each status category
        self.raw_count = 0
        self.ripe_count = 0

    def initUI(self):
        self.setGeometry(50, 50, 640, 450)
        self.setWindowTitle('Mango Sorting')

        # Layout
        self.layout = QVBoxLayout()

        # Image label for OpenCV frames
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)  # Center align the image
        self.layout.addWidget(self.image_label)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)  # Two columns for status and counts
        self.table.setRowCount(2)  # Two rows for RAW and RIPE
        self.table.setHorizontalHeaderLabels(["STATUS", "COUNT"])

        # Fill table with initial counts
        self.table.setItem(0, 0, QTableWidgetItem("RAW"))
        self.table.setItem(1, 0, QTableWidgetItem("RIPE"))

        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert frame to format suitable for QtGui
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            step = channel * width
            q_img = QImage(frame.data, width, height, step, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Resize the pixmap while preserving aspect ratio and center align the image
            scaled_pixmap = pixmap.scaledToWidth(self.image_label.width(), Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

            # Detect mango fruit and determine its status (raw or ripe)
            status = self.detect_status(frame)
            if status == "RAW":
                self.raw_count += 1
            elif status == "RIPE":
                self.ripe_count += 1

            # Update the counts in the table
            self.table.setItem(0, 1, QTableWidgetItem(str(self.raw_count)))
            self.table.setItem(1, 1, QTableWidgetItem(str(self.ripe_count)))

    def detect_status(self, frame):
        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define range of ripe mango color in HSV
        lower_range = np.array([25, 100, 100])
        upper_range = np.array([35, 255, 255])

        # Threshold the HSV image to get only ripe mango color
        mask = cv2.inRange(hsv_frame, lower_range, upper_range)

        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(frame, frame, mask=mask)

        # Compare with reference images
        raw_similarity = self.compare_images(frame, self.raw_mango_image)
        ripe_similarity = self.compare_images(frame, self.ripe_mango_image)

        # Set a threshold to classify as ripe or raw based on similarity
        threshold = 0.8  # Adjust as needed
        if raw_similarity > threshold:
            return "RAW"
        elif ripe_similarity > threshold:
            return "RIPE"
        else:
            return "UNKNOWN"

    def compare_images(self, img1, img2):
        # Convert images to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Compute Structural Similarity Index (SSI)
        similarity = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)
        return np.max(similarity)

    def resizeEvent(self, event):
        # Ensure the image label is centered when the window is resized
        self.image_label.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.cap.release()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
