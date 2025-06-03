import os
import json
import sys
import subprocess
from datetime import datetime
from moviepy.editor import VideoFileClip
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ---------- 1. 유틸 함수 ----------

def timestamp_to_seconds(ts: str) -> int:
    ts = ts.replace("-", ":")
    t = datetime.strptime(ts, "%H:%M:%S")
    return t.hour * 3600 + t.minute * 60 + t.second


def merge_jsons(emotion_path, speed_path, output_path):
    with open(emotion_path, 'r', encoding='utf-8') as f1:
        emotion_data = json.load(f1)
    with open(speed_path, 'r', encoding='utf-8') as f2:
        speed_data = json.load(f2)

    merged = []
    for idx, (e, s) in enumerate(zip(emotion_data, speed_data), start=1):
        start_sec = timestamp_to_seconds(e["start_time"])
        end_sec = timestamp_to_seconds(e["end_time"])
        duration = max(1, end_sec - start_sec)
        chat_speed = round(s["line_count"] / duration, 2)

        merged.append({
            "start_time": e["start_time"],
            "end_time": e["end_time"],
            "emotion": e["emotion"],
            "emotion_per": e.get("emotion_per", 70),
            "chat_speed": chat_speed
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


def generate_clips_and_thumbnails(video_path, json_input_path, output_dir="highlight_output"):
    os.makedirs(output_dir, exist_ok=True)
    video = VideoFileClip(video_path)

    with open(json_input_path, "r", encoding="utf-8") as f:
        highlights = json.load(f)

    enriched = []
    for idx, item in enumerate(highlights, start=1):
        start_sec = timestamp_to_seconds(item["start_time"])
        end_sec = timestamp_to_seconds(item["end_time"])

        clip = video.subclip(start_sec, end_sec)
        clip_path = os.path.join(output_dir, f"clip{idx}.mp4")
        clip.write_videofile(clip_path, codec="libx264", audio_codec="aac", logger=None)

        img_path = os.path.join(output_dir, f"highlight{idx}.png")
        clip.save_frame(img_path, t=0.5)

        item["clip"] = clip_path
        item["screenshot"] = img_path
        enriched.append(item)

    final_path = os.path.join(output_dir, "highlight_result.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    return final_path

# ---------- 2. QThread + 로딩 ----------

class HighlightWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, video_path, emotion_path, speed_path, merged_json_path, output_dir):
        super().__init__()
        self.video_path = video_path
        self.emotion_path = emotion_path
        self.speed_path = speed_path
        self.merged_json_path = merged_json_path
        self.output_dir = output_dir

    def run(self):
        merge_jsons(self.emotion_path, self.speed_path, self.merged_json_path)
        output_json = generate_clips_and_thumbnails(self.video_path, self.merged_json_path, self.output_dir)
        self.finished.emit(output_json)

class LoadingUI(QWidget):
    def __init__(self, video_path, emotion_path, speed_path, merged_json_path, output_dir):
        super().__init__()
        self.setWindowTitle("ScenePulsE - 하이라이트 생성 중")
        self.setGeometry(400, 300, 400, 150)
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()
        label = QLabel("⏳ 하이라이트 생성 중입니다...\n잠시만 기다려 주세요.")
        label.setStyleSheet("color: white; font-size: 30px;")
        label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)

        layout.addWidget(label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.worker = HighlightWorker(video_path, emotion_path, speed_path, merged_json_path, output_dir)
        self.worker.finished.connect(self.launch_viewer)
        self.worker.start()

    def launch_viewer(self, json_path):
        self.close()
        subprocess.run(["python", "highlight_viewer.py"])

# ---------- 3. json병합, 하이라이트 클립생성 실행 ----------

if __name__ == "__main__":
    image_output_folder = "frames_output"
    video_path = "capston.mp4"
    merged_json_path = "highlight_result.json"
    highlight_output_dir = "highlight_output"

    emotion_path = os.path.join(image_output_folder, "emotion_by_line.json")
    speed_path = os.path.join(image_output_folder, "speed_rankings.json")

    if not (os.path.exists(video_path) and os.path.exists(emotion_path) and os.path.exists(speed_path)):
        print("필요한 파일이 없습니다. 경로를 확인해주세요.")
        sys.exit(1)

    app = QApplication(sys.argv)
    loader = LoadingUI(video_path, emotion_path, speed_path, merged_json_path, highlight_output_dir)
    loader.show()
    sys.exit(app.exec_())
