import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QComboBox
)
from PyQt5.QtGui import QPixmap, QFont, QCursor
from PyQt5.QtCore import Qt

EMOJI_MAP = {
    "기쁨": "😄", "슬픔": "😢", "화남": "😡", "중립": "😐"
}

class HighlightCard(QFrame):
    def __init__(self, image_path, start_time, end_time, emotion, emotion_per, chat_speed, clip_path):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 10px;")
        self.setFixedHeight(220)

        img_label = QLabel()
        img_label.setPixmap(QPixmap(image_path).scaled(300, 180, Qt.KeepAspectRatio))
        img_label.setCursor(QCursor(Qt.PointingHandCursor))
        img_label.mousePressEvent = lambda event: os.startfile(clip_path)

        info_label = QLabel(
            f"⏱️ {start_time} ~ {end_time}\n"
            f"{EMOJI_MAP.get(emotion, '❔')} {emotion} ({emotion_per}%)\n"
            f"💬 채팅속도: {chat_speed}"
        )
        info_label.setStyleSheet("color: white;")
        info_label.setFont(QFont("Arial", 15))
        info_label.setWordWrap(True)

        layout = QHBoxLayout()
        layout.addWidget(img_label)
        layout.addWidget(info_label)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

class HighlightOutputWindow(QWidget):
    def __init__(self, json_path):
        super().__init__()
        self.json_path = json_path
        self.setWindowTitle("ScenePulsE - 하이라이트 결과")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # 상단 드롭다운 메뉴 오른쪽 정렬
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        self.combo = QComboBox()
        self.combo.setFixedWidth(160)
        self.combo.setStyleSheet("background-color: gray; color: black; font-size: 14px;")
        self.combo.addItem("전체")
        self.combo.addItems(["기쁨", "슬픔", "화남", "중립"])
        self.combo.currentTextChanged.connect(self.update_display)
        top_bar.addWidget(self.combo)

        self.main_layout.addLayout(top_bar)

        # 스크롤 가능한 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # 하단 로고
        self.logo = QLabel("ScenePulsE")
        self.logo.setFont(QFont("Arial", 20, QFont.Bold))
        self.logo.setStyleSheet("color: white;")
        self.logo.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.logo)

        self.load_data()
        self.update_display("전체")

    def load_data(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.highlights = json.load(f)

    def update_display(self, selected_emotion):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)  # 항상 위부터 정렬됨

        for item in self.highlights:
            if selected_emotion == "전체" or item["emotion"] == selected_emotion:
                card = HighlightCard(
                    image_path=item["screenshot"],
                    start_time=item["start_time"],
                    end_time=item["end_time"],
                    emotion=item["emotion"],
                    emotion_per=item.get("emotion_per", 0),
                    chat_speed=item.get("chat_speed", 0),
                    clip_path=item["clip"]
                )
                content_layout.addWidget(card)

        self.scroll_area.setWidget(content_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    json_path = "highlight_output/highlight_result.json"

    if not os.path.exists(json_path):
        print("highlight_result.json 파일이 존재하지 않습니다.")
        sys.exit(1)

    window = HighlightOutputWindow(json_path)
    window.show()
    sys.exit(app.exec_())
