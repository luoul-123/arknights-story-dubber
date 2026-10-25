"""Render the desktop UI without recording, playback, or interacting with the game."""
import argparse
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from app import MainWindow

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='生成桌面界面预览图')
    parser.add_argument('--image', type=Path, help='可选：使用指定的演示画面')
    args = parser.parse_args()
    sample = args.image or ROOT/'演示截图.png'
    if not sample.is_file() and args.image is None:
        subprocess.run([sys.executable, str(ROOT/'make_sample.py')], check=True)
    if not sample.is_file(): parser.error(f'找不到演示画面：{sample}')
    application = QApplication([])
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
    window = MainWindow(preview=True)
    window.timer.stop(); window.poll_timer.stop()
    window.ocr_init.result(timeout=40); window.tts_init.result(timeout=30)
    window.resize(1160, 780); window.show(); application.processEvents()
    with Image.open(sample) as frame: window.show_image(frame.convert('RGB'))
    report = ROOT/'.demo_cache/verification.json'
    if report.is_file():
        data = json.loads(report.read_text(encoding='utf-8'))
        window.speaker.setText(data['screenshots'][0]['speaker'])
        window.line.setPlainText(data['screenshots'][0]['text'])
        window.ocr_ms = data['screenshots'][0]['ocr_ms']; window.tts_ms = data['system_tts_ms']; window.metrics()
        window.live_badge.setText('截图测试'); window.confidence.setText('双引擎复核')
    else:
        window.speaker.setText('演示角色')
        window.line.setPlainText('你好，这是一段剧情配音演示。')
        window.live_badge.setText('演示画面'); window.confidence.setText('')
    window.set_status('截图识别示例 · 选择游戏窗口后即可开始自动配音')
    application.processEvents(); window.grab().save(str(ROOT/'界面预览.png'))
    window.navigate(1); window.set_status('等待录制第一段声音')
    window.resize(1160, 1040); application.processEvents()
    window.grab().save(str(ROOT/'录音室预览.png'))
    window.resize(940,780); window.navigate(2); application.processEvents()
    window.grab().save(str(ROOT/'设置预览.png'))
    window.close()


if __name__ == '__main__':
    main()
