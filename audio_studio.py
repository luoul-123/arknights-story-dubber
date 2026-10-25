"""Explicit user-triggered WASAPI loopback recording and local clip preparation."""
from __future__ import annotations
import threading
import time
import uuid
import wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
RECORDINGS = ROOT / 'voice_profiles' / 'recordings'


class LoopbackRecorder:
    def __init__(self):
        self.active = False
        self.level = 0.0
        self.started = 0.0
        self.error = None
        self.device_name = ''
        self.stop_event = threading.Event()
        self.thread = None
        self.audio = None
        self.stream = None
        self.path = None

    @staticmethod
    def device():
        import pyaudiowpatch as pa
        audio = pa.PyAudio()
        try:
            return audio.get_default_wasapi_loopback()['name']
        finally:
            audio.terminate()

    def start(self):
        if self.active:
            raise RuntimeError('正在录音')
        import pyaudiowpatch as pa
        self.audio = pa.PyAudio()
        try:
            device = self.audio.get_default_wasapi_loopback()
            self.device_name = device['name']
            self.rate = int(device['defaultSampleRate'])
            self.channels = min(2, int(device['maxInputChannels']))
            self.stream = self.audio.open(format=pa.paInt16, channels=self.channels, rate=self.rate,
                input=True, input_device_index=device['index'], frames_per_buffer=2048)
        except Exception:
            self.audio.terminate()
            raise
        RECORDINGS.mkdir(parents=True, exist_ok=True)
        self.path = RECORDINGS / f'recording_{uuid.uuid4().hex}.wav'
        self.stop_event.clear()
        self.error = None
        self.active = True
        self.started = time.monotonic()
        self.thread = threading.Thread(target=self._capture, daemon=True)
        self.thread.start()
        return self.path

    def _capture(self):
        try:
            with wave.open(str(self.path), 'wb') as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(self.rate)
                while not self.stop_event.is_set() and time.monotonic()-self.started < 600:
                    raw = self.stream.read(2048, exception_on_overflow=False)
                    samples = np.frombuffer(raw, dtype='<i2').reshape(-1, self.channels).astype(np.float32).mean(axis=1)
                    self.level = float(np.sqrt(np.mean(samples*samples))/32768)
                    out.writeframesraw(samples.astype('<i2').tobytes())
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.stream.close()
            self.audio.terminate()
            self.active = False
            self.level = 0.0

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=4)
            if self.thread.is_alive():
                raise RuntimeError('录音设备未响应，请稍候再停止')
        if self.error:
            raise RuntimeError(self.error)
        return self.path


def slice_recording(path: Path, destination: Path):
    """Trim silence and split recordings into bounded reference utterances."""
    with wave.open(str(path), 'rb') as wav:
        rate = wav.getframerate()
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').astype(np.float32)/32768
    if len(data) < rate:
        raise ValueError('录音不足 1 秒，请播放完整角色语音后再停止')
    hop = max(1, int(rate*.02))
    padded = np.pad(data, (0, (-len(data)) % hop))
    rms = np.sqrt(np.mean(padded.reshape(-1, hop)**2, axis=1))
    threshold = max(.004, min(.025, float(np.percentile(rms, 85))*.15))
    active = np.flatnonzero(rms > threshold)
    if not len(active):
        raise ValueError('没有录到有效声音，请确认游戏使用当前系统输出设备')
    runs = []
    start = previous = int(active[0])
    for frame in active[1:]:
        if frame-previous > 25:
            runs.append((start, previous+1))
            start = int(frame)
        previous = int(frame)
    runs.append((start, previous+1))
    destination.mkdir(parents=True, exist_ok=True)
    clips = []
    for left, right in runs:
        begin = max(0, left*hop-int(.12*rate))
        end = min(len(data), right*hop+int(.16*rate))
        while end-begin > rate:
            boundary = min(end, begin+int(11.5*rate))
            if boundary < end:
                # Prefer a quiet point near the target cut, not the middle of a syllable.
                lo, hi = int((boundary-rate)/hop), int(boundary/hop)
                boundary = max(begin+rate, int((lo+np.argmin(rms[lo:hi]))*hop))
            chunk = data[begin:boundary]
            duration = len(chunk)/rate
            begin = boundary
            if duration < 1.2:
                continue
            peak = float(np.max(np.abs(chunk)))
            clipped = float(np.mean(np.abs(chunk) >= .99))
            gain = min(3.0, .9/max(peak, .001))
            chunk = np.clip(chunk*gain, -.98, .98)
            target = destination / f'clip_{uuid.uuid4().hex}.wav'
            with wave.open(str(target), 'wb') as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
                wav.writeframes((chunk*32767).astype('<i2').tobytes())
            clips.append({'id':target.stem, 'path':str(target), 'duration':round(duration, 2),
                          'text':'', 'clipped':clipped > .01, 'added_at':int(time.time())})
    if not clips:
        raise ValueError('有效片段太短；请录制几句完整语音')
    return clips
