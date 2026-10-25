"""Arknights screen-only dubbing and recorded-character voice studio."""
from __future__ import annotations
import copy
import ctypes
from ctypes import wintypes
import math
import sys
import time
import winsound
import wave
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import win32gui
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QTimer, QAbstractNativeEventFilter
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QStackedWidget, QScrollArea, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QSizePolicy,
)
from recognition import Recognizer, StableDialogue, CapturePaused, visible_windows, is_foreground, text_key
from speech_engine import SpeechEngine
from audio_studio import LoopbackRecorder, slice_recording
from streaming_dialogue import IncrementalDialogue
from training import CharacterStore, Transcriber, TrainingJob, ProcessJob, settings, save_settings, check_engine, training_clips

ROOT=Path(__file__).resolve().parent

from ui_theme import STYLE


def label(text, name=None, wrap=False):
    widget=QLabel(text)
    if name: widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def button(text, callback, name=None):
    widget=QPushButton(text)
    if name: widget.setObjectName(name)
    widget.clicked.connect(callback)
    return widget


def card():
    frame=QFrame(); frame.setObjectName('card')
    layout=QVBoxLayout(frame); layout.setContentsMargins(20,18,20,18); layout.setSpacing(12)
    return frame,layout


def mascot(name, size=72):
    widget=QLabel()
    pixmap=QPixmap(str(ROOT/'assets'/f'{name}.png'))
    widget.setFixedSize(size,size)
    widget.setPixmap(pixmap.scaled(size,size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    widget.setToolTip('米米子 · 阿米娅' if name=='amiya' else '凯尔希炭')
    return widget


def disclosure(title, content):
    container=QWidget(); layout=QVBoxLayout(container); layout.setContentsMargins(0,0,0,0); layout.setSpacing(6)
    toggle=QPushButton('＋  '+title); toggle.setObjectName('disclosure'); toggle.setCheckable(True)
    content.setVisible(False)
    def expand(checked):
        content.setVisible(checked); toggle.setText(('－  ' if checked else '＋  ')+title)
    toggle.toggled.connect(expand); layout.addWidget(toggle); layout.addWidget(content)
    return container


def friendly_error(error, has_models=False):
    message=str(error)
    if 'resampy' in message or 'No module named' in message:
        return ('模型已保存，试听暂时不可用。' if has_models else '声音引擎缺少依赖。')+'请在“设置与帮助”点击“修复声音依赖”，不用重录。'
    if '取消' in message: return '任务已取消，录音和已保存的模型仍然保留。'
    if '角色引擎' in message or '预热' in message:
        return ('已有训练结果保留。' if has_models else '')+'声音准备失败，请重试“准备角色声音”；详情可展开日志查看。'
    return message[:180]


class Waveform(QWidget):
    def __init__(self):
        super().__init__()
        self.values=deque([0.0]*70,maxlen=70)
        self.setMinimumHeight(86)
        self.recording=False

    def update_level(self,value,recording):
        self.recording=recording
        self.values.append(min(1.0,value*5))
        self.update()

    def paintEvent(self,event):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width=self.width()/len(self.values)
        painter.setPen(QPen(QColor('#c58065' if self.recording else '#a3bc90'),max(2,width*.42),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        for index,value in enumerate(self.values):
            height=max(2,value*(self.height()-12))
            x=int((index+.5)*width); y=self.height()//2
            painter.drawLine(x,int(y-height/2),x,int(y+height/2))


class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self,window):
        super().__init__(); self.window=window; self.ids=[]
        for key,vk in ((801,0x77),(802,0x78)):
            if ctypes.windll.user32.RegisterHotKey(None,key,0x4000,vk): self.ids.append(key)

    def nativeEventFilter(self,event_type,message):
        msg=wintypes.MSG.from_address(int(message))
        if msg.message==0x312 and msg.wParam in self.ids:
            if msg.wParam==801: self.window.toggle_auto()
            else: self.window.toggle_recording()
            return True,0
        return False,0

    def close(self):
        for key in self.ids: ctypes.windll.user32.UnregisterHotKey(None,key)


class MainWindow(QMainWindow):
    def __init__(self,preview=False):
        super().__init__()
        self.setWindowTitle('舟声 · 明日方舟剧情配音')
        screen=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1160,screen.width()-60),min(780,screen.height()-60))
        self.setMinimumSize(940,640)
        self.setStyleSheet(STYLE)
        self.ocr_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='ocr')
        self.tts_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='speech')
        self.studio_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='studio')
        self.recognizer=Recognizer(); self.speech=SpeechEngine(); self.tracker=IncrementalDialogue()
        self.store=CharacterStore(); self.recorder=LoopbackRecorder(); self.transcriber=Transcriber()
        self.auto_mode=False; self.image_path=None; self.session=0; self.speech_token=0
        self.scan_future=None; self.speech_future=None; self.pending_speech=None
        self.speech_queue=deque(); self.audio_queue=deque(); self.playback_until=0.0
        self.studio_future=None; self.studio_callback=None; self.job=None; self.closed=False
        self.ocr_ready=False; self.speech_ready=False; self.last_image=None; self.recording_name=None
        self.last_source=None; self.current_reading=None
        self.finishing_record_name=None
        self.auto_connect_pending=not preview
        self.voice_preparing=False
        self.job_started=None
        self.build_ui()
        self.refresh_windows(); self.refresh_characters(); self.refresh_engine_status()
        self.live_badge.setText('引擎准备中')
        self.timer=QTimer(self); self.timer.setInterval(220); self.timer.timeout.connect(self.auto_tick); self.timer.start()
        self.poll_timer=QTimer(self); self.poll_timer.setInterval(50); self.poll_timer.timeout.connect(self.poll); self.poll_timer.start()
        self.hotkeys=Hotkeys(self) if not preview else None
        if self.hotkeys: QApplication.instance().installNativeEventFilter(self.hotkeys)
        self.ocr_init=self.ocr_pool.submit(self.recognizer.warmup)
        self.tts_init=self.tts_pool.submit(self.speech.warmup)

    def build_ui(self):
        shell=QWidget(); shell.setObjectName('shell'); self.setCentralWidget(shell)
        outer=QHBoxLayout(shell); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar=QFrame(); sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(178)
        nav=QVBoxLayout(sidebar); nav.setContentsMargins(20,28,18,22); nav.setSpacing(10)
        nav.addWidget(label('舟 声','brand')); nav.addWidget(label('ARKNIGHTS · VOICE','eyebrow'))
        nav.addSpacing(22)
        self.nav_buttons=[]
        for index,text in enumerate(['01  听剧情','02  录角色声音','03  设置与帮助']):
            item=button(text,lambda checked=False,i=index:self.navigate(i),'nav'); item.setCheckable(True)
            nav.addWidget(item); self.nav_buttons.append(item)
        nav.addStretch()
        nav.addWidget(mascot('amiya',104),0,Qt.AlignmentFlag.AlignHCenter)
        nav.addWidget(label('博士，今天听什么故事？','muted',True))
        nav.addSpacing(14)
        self.side_state=label('●  本地运行','eyebrow'); nav.addWidget(self.side_state)
        nav.addWidget(label('只读取选定窗口画面\n录音保存在你的电脑','muted',True))
        nav.addSpacing(12); nav.addWidget(label('F8  开始 / 暂停配音\nF9  开始 / 停止录音','muted',True))
        outer.addWidget(sidebar)
        right=QVBoxLayout(); right.setContentsMargins(0,0,0,0); right.setSpacing(0)
        self.pages=QStackedWidget(); right.addWidget(self.pages,1)
        self.build_live(); self.build_studio(); self.build_settings()
        footer=QFrame(); footer.setObjectName('footer'); footer_layout=QHBoxLayout(footer); footer_layout.setContentsMargins(24,13,24,13)
        self.status=label('正在预热识别和配音引擎…','muted',True); footer_layout.addWidget(self.status,1)
        self.latency=label('识别 —   /   生成 —','metric'); footer_layout.addWidget(self.latency)
        right.addWidget(footer); outer.addLayout(right,1)
        self.ocr_ms=None; self.tts_ms=None; self.navigate(0)

    def page(self,title,subtitle):
        page=QWidget(); page.setObjectName('page')
        layout=QVBoxLayout(page); layout.setContentsMargins(26,24,26,20); layout.setSpacing(16)
        head=QHBoxLayout(); titles=QVBoxLayout(); titles.setSpacing(5)
        titles.addWidget(label(title,'heading')); titles.addWidget(label(subtitle,'muted',True)); head.addLayout(titles,1)
        layout.addLayout(head)
        self.pages.addWidget(page)
        return page,layout,head

    def build_live(self):
        _,layout,head=self.page('博士，来听一段故事吧','选好游戏窗口，点击开始；回到游戏后自动朗读。')
        self.live_badge=label('引擎准备中','badge'); head.addWidget(self.live_badge); head.addWidget(mascot('kaltsit',58))
        source_card,source_layout=card(); row=QHBoxLayout()
        row.addWidget(label('剧情窗口','cardTitle'))
        self.source=QComboBox(); self.source.setMinimumWidth(220); self.source.currentIndexChanged.connect(self.source_changed)
        row.addWidget(self.source,1); row.addWidget(button('刷新',self.refresh_windows)); row.addWidget(button('用截图测试',self.choose_image))
        source_layout.addLayout(row); layout.addWidget(source_card)
        body=QHBoxLayout(); body.setSpacing(16)
        monitor,monitor_layout=card(); monitor_layout.addWidget(label('画面监看','cardTitle'))
        self.preview=label('选择游戏窗口后开始配音\n\n也可以载入截图测试识别效果','preview',True)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(300,230)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        monitor_layout.addWidget(self.preview,1)
        monitor_layout.addWidget(label('边识别边朗读 · 短句就绪即播，后文继续识别','muted',True))
        controls=QHBoxLayout()
        self.auto_button=button('开始自动配音',self.toggle_auto,'primary'); controls.addWidget(self.auto_button,1)
        self.once_button=button('识别一次',self.scan_once); controls.addWidget(self.once_button)
        monitor_layout.addLayout(controls)
        body.addWidget(monitor,6)
        transcript,transcript_layout=card(); title_row=QHBoxLayout(); title_row.addWidget(label('正在讲述','cardTitle')); title_row.addStretch()
        self.confidence=label('等待台词','muted'); title_row.addWidget(self.confidence); transcript_layout.addLayout(title_row)
        self.speaker=QLineEdit(); self.speaker.setPlaceholderText('角色 / 旁白'); transcript_layout.addWidget(self.speaker)
        self.line=QTextEdit(); self.line.setObjectName('transcript'); self.line.setPlaceholderText('剧情台词会显示在这里。\n\n识别有误时，可直接修改并重新朗读。'); self.line.setMinimumHeight(155)
        transcript_layout.addWidget(self.line,1)
        self.voice_label=label('声线随角色自动匹配','muted',True); transcript_layout.addWidget(self.voice_label)
        actions=QHBoxLayout(); actions.addWidget(button('重新朗读',self.speak_edited)); actions.addWidget(button('停止声音',self.stop_audio)); transcript_layout.addLayout(actions)
        body.addWidget(transcript,5); layout.addLayout(body,1)
        history,history_layout=card(); history_layout.setContentsMargins(18,12,18,12)
        history_layout.addWidget(label('最近的台词','muted'))
        self.history=QListWidget(); self.history.setMaximumHeight(76); self.history.setMinimumHeight(45); history_layout.addWidget(self.history)
        layout.addWidget(history)

    def build_studio(self):
        _,layout,head=self.page('把熟悉的声音，留在故事里','录几句 → 核对文字 → 直接试听。训练可以稍后再做。')
        head.addWidget(mascot('amiya',64))
        self.studio_status=label('先选择一个角色，或填写新角色的名字。','task',True)
        status_row=QHBoxLayout(); status_row.addWidget(self.studio_status,1)
        status_row.addWidget(button('试听当前角色',self.audition_character)); layout.addLayout(status_row)
        self.studio_progress=QProgressBar(); self.studio_progress.setTextVisible(False); self.studio_progress.setValue(0); layout.addWidget(self.studio_progress)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); layout.addWidget(scroll,1)
        content=QWidget(); content.setObjectName('page'); form=QVBoxLayout(content); form.setContentsMargins(0,0,0,0); form.setSpacing(16); scroll.setWidget(content)
        profile,profile_layout=card(); row=QHBoxLayout()
        row.addWidget(label('谁的声音？','cardTitle'))
        self.characters=QComboBox(); self.characters.setMinimumWidth(140); self.characters.currentTextChanged.connect(self.select_character); row.addWidget(self.characters)
        self.role_name=QLineEdit(); self.role_name.setPlaceholderText('新角色名称，例如 阿米娅'); row.addWidget(self.role_name,1)
        self.language=QComboBox(); self.language.addItem('中文语音','zh'); self.language.addItem('日语语音','ja'); row.addWidget(self.language)
        profile_layout.addLayout(row)
        profile_layout.addWidget(label('填写剧情中显示的角色名字。已有角色可以直接继续录音。','muted',True)); form.addWidget(profile)
        recording,record_layout=card(); row=QHBoxLayout(); row.addWidget(label('01   录制角色语音','cardTitle')); row.addStretch()
        self.record_time=label('00:00','badge'); row.addWidget(self.record_time); record_layout.addLayout(row)
        self.waveform=Waveform(); self.waveform.setMinimumHeight(42); self.waveform.setMaximumHeight(48); record_layout.addWidget(self.waveform)
        self.device_label=label('采集当前扬声器 / 耳机播放的声音','muted',True); record_layout.addWidget(self.device_label)
        record_layout.addWidget(label('关闭背景音乐，在游戏里播放几句语音；按 F9 停止。先录约 30 秒就好。','muted',True))
        controls=QHBoxLayout(); self.record_button=button('●  开始录音',self.toggle_recording,'record'); controls.addWidget(self.record_button)
        self.record_stats=label('录 3–10 秒可试听 · 30 秒有效语音可快速训练','muted',True); controls.addWidget(self.record_stats,1); record_layout.addLayout(controls); form.addWidget(recording)
        samples,sample_layout=card(); row=QHBoxLayout(); row.addWidget(label('02   核对语音片段','cardTitle')); row.addStretch()
        self.transcribe_button=button('自动转写',self.transcribe); row.addWidget(self.transcribe_button); row.addWidget(button('试听选中片段',self.play_clip)); sample_layout.addLayout(row)
        self.clips=QTableWidget(0,3); self.clips.setHorizontalHeaderLabels(['片段','时长','语音原文 · 双击可修改'])
        self.clips.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.clips.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        self.clips.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.clips.verticalHeader().hide(); self.clips.setMinimumHeight(120); self.clips.setMaximumHeight(160); self.clips.itemChanged.connect(self.save_transcript)
        sample_layout.addWidget(label('停止录音后自动转写。双击原文可修改错字，清空文字的片段不会用于训练。','muted',True))
        sample_layout.addWidget(self.clips); form.addWidget(samples)
        training,train_layout=card(); row=QHBoxLayout(); row.addWidget(label('03   听听效果','cardTitle')); row.addStretch(); row.addWidget(label('无需先训练','badge')); train_layout.addLayout(row)
        self.training_hint=label('有一段 3–10 秒的清晰录音，就可以先试听。','muted',True); train_layout.addWidget(self.training_hint)
        row=QHBoxLayout(); self.audition=QLineEdit('博士，准备好继续我们的旅程了吗？'); row.addWidget(self.audition,1)
        self.audition_button=button('直接试听',self.audition_character,'primary'); row.addWidget(self.audition_button); train_layout.addLayout(row)
        advanced=QWidget(); extra=QVBoxLayout(advanced); extra.setContentsMargins(0,5,0,0)
        extra.addWidget(label('想进一步调整音色？累计 30 秒有效语音后可选快速训练。短样本效果因录音而异。','muted',True))
        row=QHBoxLayout(); self.training_mode=QComboBox(); self.training_mode.addItem('快速 · 2 轮（推荐先试）',2); self.training_mode.addItem('完整 · 8 轮（更久）',8)
        row.addWidget(self.training_mode,1); self.train_button=button('开始训练',self.train_character); row.addWidget(self.train_button); extra.addLayout(row)
        extra.addWidget(button('取消当前任务',self.cancel_job))
        train_layout.addWidget(disclosure('可选：进一步训练角色',advanced)); form.addWidget(training)
        form.addStretch()

    def build_settings(self):
        _,layout,head=self.page('让小助手准备好','平时无需调整。遇到声音问题，可以先修复依赖。')
        head.addWidget(mascot('kaltsit',64))
        scroll=QScrollArea(); scroll.setWidgetResizable(True); layout.addWidget(scroll,1)
        content=QWidget(); content.setObjectName('page'); form=QVBoxLayout(content); form.setContentsMargins(0,0,0,0); form.setSpacing(16); scroll.setWidget(content)
        layout=form
        info,info_layout=card(); info_layout.addWidget(label('本地引擎','cardTitle'))
        self.engine_status=label('检查中…','muted',True); info_layout.addWidget(self.engine_status)
        buttons=QHBoxLayout(); buttons.addWidget(button('准备角色声音',self.connect_engine,'primary')); buttons.addWidget(button('修复声音依赖',self.repair_audio)); info_layout.addLayout(buttons)
        info_layout.addWidget(label('模型训练成功但试听失败时，只需修复声音依赖，不用重新训练。','muted',True))
        layout.addWidget(info)
        paths,paths_layout=card(); paths_layout.addWidget(label('安装与引擎路径','cardTitle'))
        buttons=QHBoxLayout(); buttons.addWidget(button('完整安装 / 补全模型',self.install_engine)); buttons.addWidget(button('仅下载转写模型',lambda:self.install_engine(True))); paths_layout.addLayout(buttons)
        config=settings(); self.engine_path=QLineEdit(config['engine_root']); self.python_path=QLineEdit(config['engine_python'])
        paths_layout.addWidget(label('引擎目录','muted')); paths_layout.addWidget(self.engine_path)
        paths_layout.addWidget(label('引擎的 Python 程序','muted')); paths_layout.addWidget(self.python_path)
        paths_layout.addWidget(button('保存并检查',self.apply_settings)); layout.addWidget(disclosure('高级设置：安装与路径',paths))
        logs,logs_layout=card(); row=QHBoxLayout(); row.addWidget(label('任务进度','cardTitle')); row.addStretch(); row.addWidget(button('取消任务',self.cancel_job)); logs_layout.addLayout(row)
        self.task_summary=label('暂无任务。录音和训练结果会保存在本机。','task',True); logs_layout.addWidget(self.task_summary)
        self.task_elapsed=label('','muted'); logs_layout.addWidget(self.task_elapsed)
        self.settings_progress=QProgressBar(); self.settings_progress.setTextVisible(False); self.settings_progress.setValue(0); logs_layout.addWidget(self.settings_progress)
        self.logs=QTextEdit(); self.logs.setReadOnly(True); self.logs.setMinimumHeight(160); self.logs.setMaximumHeight(200); self.logs.document().setMaximumBlockCount(180)
        logs_layout.addWidget(disclosure('查看详细日志',self.logs)); layout.addWidget(logs)
        help_card,help_layout=card(); help_layout.addWidget(label('先试听，再决定要不要训练','cardTitle'))
        help_layout.addWidget(label('3–10 秒参考录音：直接克隆试听。\n30 秒有效语音：可做 2 轮快速训练。\n训练完成与声音引擎就绪是两个状态；试听报错不会删除已训练模型。','muted',True))
        source=label('兔兔与猫猫素材：<a href="https://wiki.biligame.com/arknights/头像一览">明日方舟 Wiki · 米米子 / 凯尔希炭</a>','muted',True); source.setOpenExternalLinks(True); help_layout.addWidget(source)
        layout.addWidget(help_card); layout.addStretch()

    def navigate(self,index):
        self.pages.setCurrentIndex(index)
        for i,item in enumerate(self.nav_buttons): item.setChecked(i==index)

    def set_status(self,message):
        self.status.setText(message)

    def refresh_windows(self):
        current=self.source.currentData(); self.source.blockSignals(True); self.source.clear()
        self.source.addItem('选择剧情窗口',None)
        for hwnd,title in visible_windows():
            if hwnd!=int(self.winId()) and not title.startswith('舟声'): self.source.addItem(title,hwnd)
        index=self.source.findData(current) if current else -1
        if index<0: index=next((i for i in range(1,self.source.count()) if self.source.itemText(i)=='明日方舟'),0)
        self.source.setCurrentIndex(index); self.source.blockSignals(False)
        if self.last_source!=self.source.currentData(): self.source_changed()

    def source_changed(self,*_):
        self.stop_auto(); self.image_path=None; self.last_source=self.source.currentData(); self.tracker.reset()
        self.speaker.clear(); self.line.clear(); self.last_image=None; self.preview.setText('窗口已选择\n点击“开始自动配音”')

    def choose_image(self):
        path,_=QFileDialog.getOpenFileName(self,'选择剧情截图',str(ROOT),'图片 (*.png *.jpg *.jpeg *.bmp)')
        if path:
            self.stop_auto(); self.image_path=Path(path); self.set_status('已载入截图，点击“识别一次”')
            with Image.open(path) as image: self.show_image(image.convert('RGB'))

    def stop_auto(self):
        self.auto_mode=False; self.session+=1; self.stop_audio(); self.tracker.reset()
        self.auto_button.setText('开始自动配音'); self.live_badge.setText('已暂停')

    def toggle_auto(self):
        if self.auto_mode:
            self.stop_auto(); self.set_status('自动配音已停止'); return
        if self.recorder.active: self.set_status('请先停止角色录音'); return
        if self.voice_preparing: self.set_status('角色声线正在预热，完成后即可开始配音'); return
        if self.studio_future and isinstance(self.job,TrainingJob): self.set_status('正在训练角色，完成后即可继续剧情配音'); return
        if not self.ocr_ready or not self.speech_ready: self.set_status('引擎正在准备，请稍候'); return
        hwnd=self.source.currentData()
        if not hwnd: self.set_status('请先选择剧情窗口'); return
        self.image_path=None; self.session+=1; self.auto_mode=True; self.tracker.reset()
        self.auto_button.setText('暂停自动配音'); self.live_badge.setText('正在识别')
        self.activate_game(hwnd); self.showMinimized(); self.set_status('配音已开启 · F8 暂停')

    @staticmethod
    def activate_game(hwnd):
        try:
            if hwnd and not is_foreground(hwnd): win32gui.SetForegroundWindow(hwnd)
        except Exception: pass

    def auto_tick(self):
        if self.auto_mode and self.ocr_ready and self.scan_future is None:
            hwnd=self.source.currentData()
            if hwnd and is_foreground(hwnd): self.submit_scan(False)
            else:
                self.live_badge.setText('等待游戏'); self.set_status('回到游戏窗口后，自动配音会继续')

    def scan_once(self):
        if self.recorder.active or (self.studio_future and isinstance(self.job,TrainingJob)):
            self.set_status('录音或训练完成后即可继续配音'); return
        if not self.ocr_ready or self.scan_future: return
        self.stop_auto(); self.tracker.reset(); epoch=self.session
        if self.image_path: self.submit_scan(True)
        elif self.source.currentData():
            self.activate_game(self.source.currentData()); self.showMinimized()
            QTimer.singleShot(350,lambda:self.submit_scan(True) if self.session==epoch else None)
        else: self.set_status('选择剧情窗口或载入截图')

    def submit_scan(self,manual):
        if self.scan_future: return
        self.scan_epoch=self.session; self.scan_manual=manual
        if self.image_path:
            with Image.open(self.image_path) as source: image=source.convert('RGB')
            self.scan_future=self.ocr_pool.submit(self.recognizer.scan,image,str(self.image_path))
        else: self.scan_future=self.ocr_pool.submit(self.recognizer.scan_window,self.source.currentData())

    def show_image(self,image):
        self.last_image=image
        pix=QPixmap.fromImage(ImageQt(image).copy())
        self.preview.setPixmap(pix.scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if getattr(self,'last_image',None) is not None: self.show_image(self.last_image)

    def stop_audio(self):
        self.speech_token+=1; self.pending_speech=None
        self.speech_queue.clear(); self.audio_queue.clear(); self.playback_until=0.0
        winsound.PlaySound(None,winsound.SND_ASYNC)

    def request_speech(self,speaker,text,append=False):
        if self.voice_preparing: self.set_status('角色声线正在预热，请稍候'); return
        if self.recorder.active or (self.studio_future and isinstance(self.job,TrainingJob)):
            self.set_status('录音或训练期间暂停播放配音'); return
        if not text.strip() or not self.speech_ready: return
        if not append: self.stop_audio()
        reference=self.store.reference(speaker)
        self.speech_queue.append((self.speech_token,speaker,text,reference,time.monotonic()))
        self.pump_speech()

    def pump_speech(self):
        # Prefetch at most two audio chunks while the current one plays.
        if self.speech_future is None and self.speech_queue and len(self.audio_queue)<2:
            self.speech_request=self.speech_queue.popleft()
            token,speaker,text,reference,started=self.speech_request
            self.speech_future=self.tts_pool.submit(self.speech.synthesize,text,reference)

    def play_next_phrase(self):
        if time.monotonic()<self.playback_until or not self.audio_queue: return
        token,path,mode,speaker,text=self.audio_queue.popleft()
        if token!=self.speech_token: return
        try:
            with wave.open(str(path),'rb') as audio: duration=audio.getnframes()/audio.getframerate()
            winsound.PlaySound(str(path),winsound.SND_FILENAME|winsound.SND_ASYNC)
            self.playback_until=time.monotonic()+duration+.025
            self.voice_label.setText(mode)
            self.history.insertItem(0,f'{speaker}  ·  {text[:75]}')
            while self.history.count()>6: self.history.takeItem(6)
            self.set_status(f'正在朗读 · {speaker} · 后续台词继续识别中' if self.auto_mode else f'正在朗读 · {speaker} · {mode}')
        except Exception as exc: self.set_status('播放失败：'+str(exc))

    def speak_edited(self):
        self.request_speech(self.speaker.text().strip() or '旁白',self.line.toPlainText())

    def metrics(self):
        self.latency.setText(f'识别 {self.ocr_ms if self.ocr_ms is not None else "—"} ms   /   生成 {self.tts_ms if self.tts_ms is not None else "—"} ms')

    def poll(self):
        if self.closed: return
        for attr,kind in (('ocr_init','ocr'),('tts_init','tts')):
            future=getattr(self,attr,None)
            if future and future.done():
                setattr(self,attr,None)
                try:
                    result=future.result()
                    if kind=='ocr': self.ocr_ready=True
                    else: self.speech_ready=True
                    self.set_status(result)
                except Exception as exc: self.set_status(str(exc))
        if self.ocr_ready and self.speech_ready and self.live_badge.text()=='引擎准备中':
            self.live_badge.setText('准备就绪'); self.set_status('选择游戏窗口，即可开始配音')
        if self.auto_connect_pending and self.speech_ready:
            self.auto_connect_pending=False
            if (not self.studio_future and not self.recorder.active and not self.auto_mode
                    and not check_engine() and any(self.store.reference(name) for name in self.store.data)):
                self.connect_engine()
        if self.scan_future and self.scan_future.done():
            future=self.scan_future; self.scan_future=None
            if self.scan_manual and self.scan_epoch==self.session: self.showNormal()
            if self.scan_epoch==self.session:
                try:
                    reading=future.result(); self.current_reading=reading
                    if not reading.cached: self.show_image(reading.image); self.ocr_ms=reading.elapsed_ms; self.metrics()
                    self.speaker.setText(reading.speaker); self.line.setPlainText(reading.text)
                    self.confidence.setText('画面无台词' if not reading.text else ('双引擎复核' if reading.confidence>=.85 else '建议核对'))
                    if reading.text:
                        self.live_badge.setText('识别正常')
                        if self.scan_manual: self.request_speech(reading.speaker,reading.text)
                    elif self.scan_manual: self.set_status('没有找到剧情台词，已忽略标题和界面按钮')
                    if not self.scan_manual:
                        changed,chunks=self.tracker.observe(reading)
                        if changed: self.stop_audio()
                        for chunk in chunks: self.request_speech(reading.speaker,chunk,append=True)
                except CapturePaused as exc: self.live_badge.setText('等待游戏'); self.set_status(str(exc))
                except Exception as exc: self.set_status('识别失败：'+str(exc))
        if self.speech_future and self.speech_future.done():
            future=self.speech_future; self.speech_future=None
            token,speaker,text,reference,started=self.speech_request
            try:
                path,mode,elapsed=future.result()
                if token==self.speech_token:
                    self.tts_ms=elapsed; self.metrics()
                    self.audio_queue.append((token,path,mode,speaker,text))
                    if self.speech.last_error and '未就绪' in mode:
                        self.logs.append('角色配音回退原因：'+self.speech.last_error)
            except Exception as exc:
                if token==self.speech_token: self.set_status('配音失败：'+str(exc))
            self.pump_speech()
        self.play_next_phrase(); self.pump_speech()
        if self.job:
            for _ in range(30):
                if self.job.messages.empty(): break
                message,percent=self.job.messages.get_nowait()
                self.logs.append(message)
                if percent>=0:
                    self.studio_status.setText(message[-200:]); self.task_summary.setText(message[-200:]); self.studio_progress.setValue(percent); self.settings_progress.setValue(percent)
        if self.studio_future and self.job_started:
            seconds=int(time.monotonic()-self.job_started)
            self.task_elapsed.setText(f'已用时 {seconds//60:02d}:{seconds%60:02d} · 可切换页面，任务会继续')
        if self.studio_future and self.studio_future.done():
            future=self.studio_future; callback=self.studio_callback
            self.studio_future=None; self.studio_callback=None
            try:
                result=future.result()
                self.studio_progress.setValue(100); self.settings_progress.setValue(100)
                if callback: callback(result)
                if self.studio_future is None: self.task_summary.setText(self.studio_status.text())
            except Exception as exc:
                self.finishing_record_name=None
                message=friendly_error(exc,bool(self.store.data.get(self.selected_role(),{}).get('models')))
                self.studio_status.setText(message); self.task_summary.setText(message); self.set_status(message); self.logs.append(str(exc))
                self.studio_progress.setValue(0); self.settings_progress.setValue(0)
            self.refresh_engine_status(); self.update_studio_buttons()
        if self.recorder.active:
            seconds=int(time.monotonic()-self.recorder.started); self.record_time.setText(f'{seconds//60:02d}:{seconds%60:02d}')
            self.waveform.update_level(self.recorder.level,True)
        else:
            self.waveform.update_level(0,False)
            if self.recording_name and not self.studio_future: self.finish_recording()

    def selected_role(self):
        return self.role_name.text().strip()

    def refresh_characters(self,select=None):
        name=select or self.selected_role()
        self.characters.blockSignals(True); self.characters.clear(); self.characters.addItem('新建角色')
        self.characters.addItems(sorted(self.store.data)); index=self.characters.findText(name)
        self.characters.setCurrentIndex(max(0,index)); self.characters.blockSignals(False)
        if name in self.store.data: self.role_name.setText(name)
        self.refresh_clips()

    def select_character(self,name):
        if name in self.store.data:
            self.role_name.setText(name); profile=self.store.data[name]
            self.language.setCurrentIndex(max(0,self.language.findData(profile.get('language','zh'))))
        else: self.role_name.clear()
        self.refresh_clips()

    def refresh_clips(self):
        profile=self.store.data.get(self.selected_role(),{})
        clips=profile.get('clips',[]); self.clips.blockSignals(True); self.clips.setRowCount(len(clips))
        for row,clip in enumerate(clips):
            for column,value in enumerate((f'{row+1:02d}',f'{clip.get("duration",0):.1f}s',clip.get('text',''))):
                item=QTableWidgetItem(value)
                if column<2: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.clips.setItem(row,column,item)
        self.clips.blockSignals(False)
        self.refresh_record_stats()

    def refresh_record_stats(self):
        profile=self.store.data.get(self.selected_role(),{})
        clips=profile.get('clips',[])
        seconds=sum(c.get('duration',0) for c in clips if c.get('text','').strip() and not c.get('clipped') and Path(c['path']).exists())
        self.record_stats.setText(f'{len(clips)} 段录音 · {seconds:.1f} / 30 秒有效语音'+(' · 可快速训练' if seconds>=30 else ''))
        self.training_hint.setText('模型已保存 · 可直接试听，也会自动用于同名剧情角色。' if profile.get('models') else '先用一段 3–10 秒清晰录音试听；无需等待训练。')

    def save_transcript(self,item):
        if item.column()!=2: return
        profile=self.store.data.get(self.selected_role())
        if profile and item.row()<len(profile['clips']):
            profile['clips'][item.row()]['text']=item.text().strip(); self.store.save()
            self.refresh_record_stats()

    def update_studio_buttons(self):
        busy=self.studio_future is not None
        self.clips.setEnabled(not busy)
        self.record_button.setEnabled(not busy or self.recorder.active)
        self.transcribe_button.setEnabled(not busy and not self.recorder.active)
        self.train_button.setEnabled(not busy and not self.recorder.active)
        self.audition_button.setEnabled(not busy and not self.recorder.active)
        self.training_mode.setEnabled(not busy)
        locked=bool(self.recording_name) or busy
        self.role_name.setEnabled(not locked); self.characters.setEnabled(not locked); self.language.setEnabled(not locked)

    def toggle_recording(self):
        if self.recorder.active: self.finish_recording(); return
        if self.studio_future: self.set_status('请等待当前录音室任务完成'); return
        name=self.selected_role()
        if not name:
            self.navigate(1); self.showNormal(); self.role_name.setFocus(); self.set_status('先填写要录制的角色名称'); return
        try:
            self.store.ensure(name,self.language.currentData()); self.stop_auto()
            self.recorder.start(); self.recording_name=name; self.recording_language=self.language.currentData()
            self.setWindowTitle('正在录制 · '+name+' · 舟声')
            self.record_button.setText('■  停止录音'); self.side_state.setText('●  正在录制')
            self.device_label.setText('当前设备：'+self.recorder.device_name)
            self.set_status('录音中：回到游戏播放角色语音，按 F9 停止'); self.update_studio_buttons()
            hwnd=self.source.currentData()
            if hwnd: self.activate_game(hwnd); self.showMinimized()
        except Exception as exc: self.set_status('无法开始录音：'+str(exc))

    def finish_recording(self):
        if not self.recording_name or self.studio_future: return
        name=self.recording_name; self.recording_name=None
        self.finishing_record_name=name
        self.setWindowTitle('舟声 · 明日方舟剧情配音')
        folder=self.store.folder(name)/'clips'
        self.record_button.setText('●  开始录音'); self.side_state.setText('●  本地运行')
        def finish():
            path=self.recorder.stop()
            return slice_recording(path,folder)
        def complete(clips):
            self.finishing_record_name=None
            profile=self.store.ensure(name,self.recording_language); profile['clips'].extend(clips)
            profile['language']=self.recording_language; profile['status']='已录制'; self.store.save(); self.refresh_characters(name)
            self.studio_status.setText(f'已保存 {len(clips)} 个语音片段')
            if (ROOT/'models/faster-whisper-small/model.bin').exists(): self.transcribe()
            else: self.set_status('录音已保存；请在运行设置下载转写模型，之后可自动转写')
        self.start_job(finish,complete,'正在去除静音并切分录音…')

    def start_job(self,fn,callback,message,job=None):
        if self.studio_future: self.set_status('已有任务正在进行'); return False
        self.job=job or ProcessJob(); self.studio_callback=callback
        self.job_started=time.monotonic(); self.task_summary.setText(message)
        self.studio_progress.setValue(0); self.settings_progress.setValue(0)
        self.studio_status.setText(message); self.set_status(message); self.logs.append(message)
        self.studio_future=self.studio_pool.submit(fn); self.update_studio_buttons(); return True

    def transcribe(self):
        name=self.selected_role(); profile=self.store.data.get(name)
        if not profile or not profile['clips']: self.set_status('请先录制角色语音'); return
        clips=copy.deepcopy(profile['clips']); job=ProcessJob()
        def complete(result):
            self.store.data[name]['clips']=result; self.store.save(); self.refresh_clips()
            self.studio_status.setText('转写完成。核对原文后，点击“直接试听”即可。'); self.studio_progress.setValue(100)
        self.start_job(lambda:self.transcriber.run(clips,profile.get('language','zh'),job.progress),complete,'正在自动转写…',job)

    def train_character(self):
        if self.studio_future: self.set_status('当前任务还在进行，请等待或取消'); return
        name=self.selected_role(); profile=self.store.data.get(name)
        if not profile: self.set_status('请先录制角色语音'); return
        try: training_clips(profile)
        except ValueError as exc: self.studio_status.setText(str(exc)); return
        epochs=self.training_mode.currentData()
        self.stop_auto(); job=TrainingJob(); snapshot=copy.deepcopy(profile)
        def complete(models):
            self.store.data[name]['models']=models; self.store.data[name]['status']='已训练'; self.store.save(); self.refresh_clips()
            self.studio_status.setText('训练完成，正在准备试听引擎'); self.connect_engine()
        def train():
            self.speech.release_character()
            return job.train(snapshot,self.store.folder(name),epochs=epochs)
        self.start_job(train,complete,'正在检查训练样本…',job)

    def play_clip(self):
        if self.recorder.active: self.set_status('请先停止录音，再试听片段'); return
        profile=self.store.data.get(self.selected_role(),{}); row=self.clips.currentRow()
        if row<0 or row>=len(profile.get('clips',[])): self.set_status('先选中一个语音片段'); return
        self.stop_audio(); winsound.PlaySound(profile['clips'][row]['path'],winsound.SND_FILENAME|winsound.SND_ASYNC)

    def audition_character(self):
        name=self.selected_role()
        if not self.store.reference(name): self.set_status('需要至少一段 3–10 秒、已有原文的录音'); return
        if not self.speech.character_ready:
            text=self.audition.text()
            self.connect_engine(after_ready=lambda:self.request_speech(name,text)); return
        self.request_speech(name,self.audition.text())

    def repair_audio(self):
        if self.recorder.active or self.speech_future: self.set_status('请先停止录音或等待当前配音生成完毕'); return
        job=ProcessJob(); python=settings()['engine_python']
        def repair():
            self.speech.release_character()
            job.progress('正在补齐声音处理依赖…',15)
            job.run_process([sys.executable,'-m','uv','pip','install','--python',python,'resampy==0.4.3','av<17'])
            job.progress('正在验证 48 kHz 录音重采样…',85)
            job.run_process([python,'-c','import resampy,librosa,numpy as np; librosa.resample(np.zeros(48000,dtype=np.float32),orig_sr=48000,target_sr=16000,res_type="kaiser_fast"); print("音频依赖检查通过")'])
        def complete(_):
            self.studio_status.setText('声音依赖已修复。点击“直接试听”即可，已有模型不需要重训。'); self.set_status(self.studio_status.text())
        self.start_job(repair,complete,'准备修复声音依赖…',job)

    def install_engine(self,asr_only=False):
        if self.recorder.active: self.set_status('请先停止角色录音'); return
        self.stop_auto(); job=ProcessJob()
        args=[sys.executable,ROOT/'setup_voice_engine.py']
        if asr_only: args.append('--asr-only')
        def complete(_):
            self.set_status('本地模型已准备好'); self.settings_progress.setValue(100); self.refresh_engine_status()
        self.start_job(lambda:job.run_process(args),complete,'开始下载本地模型，请查看任务进度…',job)

    def apply_settings(self):
        save_settings({'engine_root':self.engine_path.text().strip(),'engine_python':self.python_path.text().strip()})
        self.refresh_engine_status(); self.set_status('配置已保存')

    def refresh_engine_status(self):
        missing=check_engine()
        asr=(ROOT/'models/faster-whisper-small/model.bin').is_file()
        self.engine_status.setText('中文识别：双引擎本地运行\n转写模型：'+('已准备' if asr else '尚未下载')+'\n角色训练：'+('环境文件已就绪' if not missing else f'尚未准备完整 · 缺少 {len(missing)} 个必要文件'))

    def connect_engine(self,after_ready=None):
        if self.recorder.active: self.set_status('请先停止角色录音'); return
        if self.studio_future: self.set_status('请等待当前录音室任务完成'); return
        if self.speech_future: self.set_status('请等待当前配音结束后连接'); return
        self.stop_auto()
        job=ProcessJob()
        reference=self.store.reference(self.selected_role())
        if not reference:
            reference=next((r for name in self.store.data if (r:=self.store.reference(name))),None)
        def prepare():
            try:
                message=self.speech.start_server(cancel_event=job.cancelled)
                if reference:
                    job.progress('正在预热角色声线，首次需要稍等片刻',70)
                    _,mode,_=self.speech.synthesize('准备好继续阅读故事了。',reference,use_cache=False)
                    if mode!='角色声线': raise RuntimeError(self.speech.last_error or '角色声线预热失败')
                    job.progress('角色声线已准备好',100)
                    message='角色声线已预热，可以开始配音或试听'
                return message
            finally:
                self.voice_preparing=False
                if job.cancelled.is_set(): self.speech.release_character()
        def complete(message):
            self.set_status(message); self.studio_status.setText(message)
            if callable(after_ready): after_ready()
        self.voice_preparing=True
        self.start_job(prepare,complete,'正在加载角色配音引擎…',job)

    def cancel_job(self):
        if self.job: self.job.cancel(); self.set_status('已请求取消，录音和已下载文件保留')

    def closeEvent(self,event):
        self.closed=True; self.timer.stop(); self.poll_timer.stop(); self.stop_audio()
        if self.hotkeys: self.hotkeys.close()
        if self.job: self.job.cancel()
        if self.recording_name:
            try:
                path=self.recorder.stop()
                clips=slice_recording(path,self.store.folder(self.recording_name)/'clips')
                self.store.ensure(self.recording_name,self.recording_language)['clips'].extend(clips)
                self.store.save()
            except Exception: pass  # The original WAV is still retained in recordings/.
        elif self.finishing_record_name and self.studio_future:
            try:
                clips=self.studio_future.result(timeout=5)
                self.store.ensure(self.finishing_record_name,self.recording_language)['clips'].extend(clips)
                self.store.save()
            except Exception: pass
        self.recognizer.close(); self.speech.close()
        for pool in (self.ocr_pool,self.tts_pool,self.studio_pool): pool.shutdown(wait=False,cancel_futures=True)
        super().closeEvent(event)


def main():
    app=QApplication(sys.argv); app.setFont(QFont('Microsoft YaHei UI',10))
    window=MainWindow(); window.show()
    return app.exec()


if __name__=='__main__':
    raise SystemExit(main())
