"""User-supplied voice references and optional local GPT-SoVITS synthesis."""

from __future__ import annotations

import ctypes
import json
import shutil
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT / "voice_profiles"
INDEX = LIBRARY / "profiles.json"
LOCAL_TTS_URL = "http://127.0.0.1:9880/tts"
SUPPORTED_AUDIO = {".wav", ".mp3", ".flac"}


class ProfileStore:
    def __init__(self) -> None:
        LIBRARY.mkdir(exist_ok=True)
        self.data: dict[str, dict] = {}
        if INDEX.exists():
            loaded = json.loads(INDEX.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data = loaded

    def add_clip(self, speaker: str, source: Path, transcript: str, rights_confirmed: bool) -> dict:
        speaker = speaker.strip()
        if not speaker:
            raise ValueError("请填写角色名")
        if not rights_confirmed:
            raise ValueError("请先确认你有权使用该声音样本进行合成")
        if source.suffix.lower() not in SUPPORTED_AUDIO or not source.is_file():
            raise ValueError("只支持 WAV、MP3、FLAC 音频文件")
        if source.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("单个音频文件不能超过 100 MB")
        profile = self.data.setdefault(speaker, {"speaker": speaker, "clips": []})
        clip_id = uuid.uuid4().hex
        destination = LIBRARY / f"{clip_id}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        clip = {
            "id": clip_id,
            "path": str(destination),
            "text": transcript.strip(),
            "added_at": int(time.time()),
        }
        profile["clips"].append(clip)
        self.save()
        return clip

    def save(self) -> None:
        temporary = INDEX.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(INDEX)

    def bulk_import(self, folder: Path, rights_confirmed: bool) -> tuple[int, list[str]]:
        """Import folder/角色名/*.wav or 角色名_序号.wav without per-role clicks."""
        if not rights_confirmed:
            raise ValueError("请只导入已获得相应使用授权的音频")
        if not folder.is_dir():
            raise ValueError("所选目录不存在")
        if folder.resolve() == LIBRARY.resolve():
            raise ValueError("请选择来源目录，不要选择程序自己的声线库目录")
        audio_files = [
            p for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO and LIBRARY.resolve() not in p.resolve().parents
        ]
        if not audio_files:
            raise ValueError("目录中没有 WAV、MP3 或 FLAC 音频")
        added = 0
        skipped: list[str] = []
        for path in audio_files:
            if path.parent != folder:
                speaker = path.parent.name.strip()
            else:
                speaker = path.stem.split("_")[0].split("-")[0].strip()
            if not speaker or speaker.lower() in {"audio", "voice", "sample", "recording"}:
                skipped.append(path.name)
                continue
            try:
                transcript_file = path.with_suffix(".txt")
                transcript = transcript_file.read_text(encoding="utf-8-sig", errors="replace").strip() if transcript_file.exists() else ""
                self.add_clip(speaker, path, transcript, True)
                added += 1
            except (OSError, ValueError):
                skipped.append(path.name)
        return added, skipped

    def speakers(self) -> list[str]:
        return sorted(self.data)

    def reference(self, speaker: str) -> dict | None:
        profile = self.data.get(speaker)
        if not profile:
            return None
        clips = profile.get("clips", [])
        return next((clip for clip in reversed(clips) if Path(clip["path"]).is_file()), None)

    def export_training_list(self) -> Path:
        lines = []
        for speaker, profile in self.data.items():
            for clip in profile.get("clips", []):
                if clip.get("text") and Path(clip["path"]).is_file():
                    lines.append(f"{clip['path']}|{speaker}|zh|{clip['text']}")
        if not lines:
            raise ValueError("请先导入音频并填写与音频一致的原文")
        output = LIBRARY / "training.list"
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output


def clone_speech(text: str, reference: dict, output: Path) -> Path:
    payload = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": reference["path"],
        "prompt_text": reference.get("text", ""),
        "prompt_lang": "zh",
        "text_split_method": "cut5",
        "media_type": "wav",
        "streaming_mode": False,
    }
    request = Request(
        LOCAL_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            audio = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"本地语音引擎返回 {exc.code}：{detail}") from exc
    except URLError as exc:
        raise RuntimeError("未连接到本机 GPT-SoVITS 服务（127.0.0.1:9880）") from exc
    if not (audio.startswith(b"RIFF") and audio[8:12] == b"WAVE"):
        raise RuntimeError("本地语音引擎未返回 WAV 音频")
    output.write_bytes(audio)
    return output


class MciRecorder:
    """Record microphone audio with the Windows waveaudio device on user click."""

    def __init__(self) -> None:
        self.alias = f"voice_rec_{uuid.uuid4().hex[:8]}"
        self.active = False

    @staticmethod
    def command(value: str) -> None:
        winmm = ctypes.windll.winmm
        code = winmm.mciSendStringW(value, None, 0, None)
        if code:
            message = ctypes.create_unicode_buffer(256)
            winmm.mciGetErrorStringW(code, message, len(message))
            raise RuntimeError(message.value or f"录音设备错误 {code}")

    def start(self) -> None:
        if self.active:
            raise RuntimeError("正在录音")
        self.command(f"open new type waveaudio alias {self.alias}")
        try:
            self.command(f"set {self.alias} channels 1 bitspersample 16 samplespersec 16000")
            self.command(f"record {self.alias}")
            self.active = True
        except Exception:
            self.command(f"close {self.alias}")
            raise

    def stop(self) -> Path:
        if not self.active:
            raise RuntimeError("尚未开始录音")
        destination = LIBRARY / f"recording_{uuid.uuid4().hex}.wav"
        try:
            self.command(f"stop {self.alias}")
            self.command(f'save {self.alias} "{destination}"')
        finally:
            self.command(f"close {self.alias}")
            self.active = False
        return destination

    def close(self) -> None:
        if self.active:
            try:
                self.command(f"close {self.alias}")
            finally:
                self.active = False
