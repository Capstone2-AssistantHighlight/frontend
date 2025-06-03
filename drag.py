import cv2
import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QFont, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QRect

class DraggableImageLabel(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.start_pos = None
        self.end_pos = None
        self.selection_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            self.end_pos = event.pos()
            self.selection_rect = QRect(self.start_pos, self.end_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_pos:
            self.end_pos = event.pos()
            self.selection_rect = QRect(self.start_pos, self.end_pos)
            self.start_pos = None
            self.end_pos = None
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.selection_rect:
            painter = QPainter(self)
            painter.setPen(QColor(255, 0, 0))
            painter.drawRect(self.selection_rect)

class ChatDragWindow(QWidget):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ScenePulsE - Drag Chat Window')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")

        self.label = QLabel('댓글 창을 드래그 해주세요', self)
        self.label.setStyleSheet("color: white;")
        self.label.setFont(QFont('Arial', 16))
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.frame, self.pixmap = self.capture_middle_frame(self.video_path)
        if self.pixmap:
            self.image_label = DraggableImageLabel(self.pixmap.scaled(900, 600, Qt.KeepAspectRatio))
            self.image_label.setAlignment(Qt.AlignCenter)
        else:
            self.image_label = QLabel('영상 불러오기 실패', self)
            self.image_label.setStyleSheet("color: red;")

        self.select_btn = QPushButton('선택', self)
        self.select_btn.setStyleSheet("color: red; font-weight: bold; font-size: 20px;")
        self.select_btn.clicked.connect(self.extract_cropped_frames)

        self.next_btn = QPushButton('NEXT', self)
        self.next_btn.setStyleSheet("color: white; font-weight: bold; font-size: 30px;")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.go_to_highlight)

        self.logo_label = QLabel('ScenePulsE', self)
        self.logo_label.setStyleSheet("color: white;")
        self.logo_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label, alignment=Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.image_label, alignment=Qt.AlignHCenter)
        layout.addWidget(self.select_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.next_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.logo_label, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

    def capture_middle_frame(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Cannot open video")
            return None, None

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame_num = total_frames // 2

        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_num)
        ret, frame = cap.read()
        cap.release()

        if ret:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            return frame, QPixmap.fromImage(qimg)
        else:
            return None, None

    def extract_cropped_frames(self):
        if not hasattr(self.image_label, 'selection_rect') or self.image_label.selection_rect is None:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("드래그 영역을 먼저 선택해주세요!")
            msg_box.setStyleSheet("QLabel{color: white;} QMessageBox{background-color: black;}")
            msg_box.exec_()

            return

        rect = self.image_label.selection_rect
        display_size = self.image_label.size()

        x_ratio = self.frame.shape[1] / display_size.width()
        y_ratio = self.frame.shape[0] / display_size.height()

        crop_x = int(rect.x() * x_ratio)
        crop_y = int(rect.y() * y_ratio)
        crop_w = int(rect.width() * x_ratio)
        crop_h = int(rect.height() * y_ratio)

        output_dir = os.path.join(os.getcwd(), "frames")
        os.makedirs(output_dir, exist_ok=True)

        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)

        for sec in range(duration):
            cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
            ret, frame = cap.read()
            if not ret:
                continue

            crop_frame = frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            timestamp = f"{h:02d}-{m:02d}-{s:02d}"
            output_path = os.path.join(output_dir, f"{timestamp}.png")
            cv2.imwrite(output_path, crop_frame)

        cap.release()
        QMessageBox.information(self, "완료", f"{output_dir}에 프레임 저장 완료!")
        self.next_btn.setEnabled(True)
        self.next_btn.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")

    def go_to_highlight(self):
        subprocess.Popen([sys.executable, "highlight.py", self.video_path])
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    video_path = sys.argv[1] if len(sys.argv) > 1 else ''
    window = ChatDragWindow(video_path)
    window.show()
    sys.exit(app.exec_())
