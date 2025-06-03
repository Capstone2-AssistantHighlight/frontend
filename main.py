import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QProgressBar
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import moviepy.editor as mp
from drag import ChatDragWindow
import subprocess


class AudioExtractionThread(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            video = mp.VideoFileClip(self.video_path)
            audio_path = os.path.splitext(self.video_path)[0] + ".wav"
            # 진행 표시 예시
            for i in range(0, 80, 20):
                self.sleep(1)
                self.progress.emit(i)
            video.audio.write_audiofile(audio_path, logger=None)
            self.progress.emit(100)
            self.done.emit(audio_path)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.audio_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ScenePulsE - 영상 업로드')
        self.setGeometry(100, 100, 600, 450)
        self.setStyleSheet("background-color: black;")

        self.label = QLabel('영상을 삽입해주세요', self)
        self.label.setStyleSheet("color: white;")
        self.label.setFont(QFont('Arial', 16))
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.upload_btn = QPushButton(self)
        self.upload_btn.setFixedSize(800, 450)
        self.upload_btn.setText("+")
        self.upload_btn.setFont(QFont('Arial', 150))
        self.upload_btn.setStyleSheet("background-color: white; color: black; border-radius: 50px;")
        self.upload_btn.clicked.connect(self.openFileNameDialog)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("color: white; text-align: center;")
        self.progress_bar.setTextVisible(True)

        self.next_btn = QPushButton('NEXT', self)
        self.next_btn.setStyleSheet("color: white; font-weight: bold; font-size: 30px;")
        self.next_btn.clicked.connect(self.openDragWindow)

        self.logo_label = QLabel('ScenePulsE', self)
        self.logo_label.setStyleSheet("color: white;")
        self.logo_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label, alignment=Qt.AlignLeft | Qt.AlignTop)
        layout.addStretch()
        layout.addWidget(self.upload_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        layout.addWidget(self.next_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.logo_label, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

    def openFileNameDialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Video files (*.mp4 *.avi *.mov)')
        if fname:
            self.video_path = fname
            print(f"Selected file: {self.video_path}")
            self.start_audio_extraction()

    def start_audio_extraction(self):
        self.progress_bar.setValue(0)
        self.thread = AudioExtractionThread(self.video_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.done.connect(self.on_extraction_done)
        self.thread.error.connect(self.on_extraction_error)
        self.thread.start()

    def on_extraction_done(self, audio_path):
        self.audio_path = audio_path
        self.show_message("Success", f"오디오 추출 완료")

    def on_extraction_error(self, error):
        self.show_message("Error", f"오디오 추출 실패 다시 비디오를 넣어주세요", error=True)

    def show_message(self, title, text, error=False):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet("QLabel { color: white; } QPushButton { color: black; }")
        msg.setStandardButtons(QMessageBox.Ok)
        if error:
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def openDragWindow(self):
        if self.video_path:
            self.hide()
            self.drag_window = ChatDragWindow(self.video_path)
            self.drag_window.show()
        else:
            self.show_message("경고", "먼저 영상을 업로드해주세요!", error=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
    subprocess.Popen(["python", "drag.py", self.video_path])