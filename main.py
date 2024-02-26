import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import pyfirmata

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()

        # Initialize OpenCV video capture
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update frame every 30 ms
        
        # Initialize count for each size category
        self.small_count = 0
        self.medium_count = 0
        self.large_count = 0
        self.defect_count = 0

        # Initialize Arduino board and servos
        self.board = self.initialize_arduino('COM3')
        self.servo1, self.servo2, self.servo3 = self.initialize_servos(self.board)

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Mango Sorting')

        # Layout
        self.layout = QVBoxLayout()

        # Image label for OpenCV frames
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setRowCount(1) 
        self.table.setHorizontalHeaderLabels(["SMALL", "MEDIUM", "LARGE", "DEFECT"])
        self.table.setItem(0, 0, QTableWidgetItem("COUNT"))
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def initialize_arduino(self, port='COM3'):
        board = pyfirmata.Arduino(port)
        iter8 = pyfirmata.util.Iterator(board)
        iter8.start()
        return board

    def initialize_servos(self, board):
        servo1 = board.get_pin('d:9:s')  # Servo for object height <= 3 inches
        servo2 = board.get_pin('d:10:s')  # Servo for 3 inches < object height <= 5 inches
        servo3 = board.get_pin('d:11:s')  # Servo for object height > 5 inches
        return servo1, servo2, servo3

    def move_servo(self, servo, angle):
        servo.write(angle)

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

            # Detect object using contour-based detection
            object_detected, object_height = self.detect_object(frame)

            # Move servo based on object height
            if object_detected:
                if object_height <= 3:
                    self.move_servo(self.servo1, 90)  # Adjust the angle as needed
                    self.move_servo(self.servo1, 0)   # Move back after rotation
                elif 3 < object_height <= 5:
                    self.move_servo(self.servo2, 90)  # Adjust the angle as needed
                    self.move_servo(self.servo2, 0)   # Move back after rotation
                elif object_height > 5:
                    self.move_servo(self.servo3, 90)  # Adjust the angle as needed
                    self.move_servo(self.servo3, 0)   # Move back after rotation

    def detect_object(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        _, threshold = cv2.threshold(edges, 30, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        object_detected = False
        object_height = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Adjust the threshold based on the size of objects you want to detect
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                object_height = h
                label = f"Object Height: {object_height:.2f} pixels"
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                object_detected = True

        return object_detected, object_height

    def resizeEvent(self, event):
        # Ensure the image label is centered when the window is resized
        self.image_label.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.cap.release()
        self.board.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
