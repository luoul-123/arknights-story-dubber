"""Persistent WinRT workers; no process startup on each frame or sentence."""
from __future__ import annotations
import json
import queue
import subprocess
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / '.demo_cache'
CACHE.mkdir(exist_ok=True)


class WindowsWorker:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        self.responses = queue.Queue()

    def _start(self):
        self.responses = queue.Queue()
        self.process = subprocess.Popen(
            ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'windows_worker.ps1')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            encoding='utf-8', bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        process, responses = self.process, self.responses
        def read():
            try:
                for line in process.stdout:
                    responses.put(json.loads(line))
            except Exception as exc:
                responses.put({'error': str(exc)})
            finally:
                responses.put({'error': 'Windows 语音/OCR 服务已退出'})
        threading.Thread(target=read, daemon=True).start()
        result = self.responses.get(timeout=20)
        if not result.get('ready'):
            raise RuntimeError(result.get('error', 'Windows 服务启动失败'))

    def call(self, op, **payload):
        with self.lock:
            try:
                if self.process is None or self.process.poll() is not None:
                    self._start()
                self.process.stdin.write(json.dumps({'op': op, **payload}, ensure_ascii=False) + '\n')
                self.process.stdin.flush()
                result = self.responses.get(timeout=25)
                if 'error' in result:
                    raise RuntimeError(result['error'])
                return result
            except (queue.Empty, BrokenPipeError):
                self.close()
                raise RuntimeError('Windows 服务超时，下次操作将重新连接')

    def ocr(self, image):
        path = CACHE / f'input_{uuid.uuid4().hex}.bmp'
        image.convert('RGB').save(path)
        try:
            return self.call('ocr', path=str(path))['lines']
        finally:
            path.unlink(missing_ok=True)

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
