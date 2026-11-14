"""Resumable Kal'tsit voice rendering for the static GitHub Pages sample."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import server
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = str(ROOT.parent / 'engines/tools/ffmpeg.exe')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='Render only this many missing lines, for a smoke test')
    parser.add_argument('--section', help='Render one story section, skipping completed MP3 files')
    parser.add_argument('--shard-root', type=Path, default=ROOT / 'work/vot-audio-20261101', help='Local checkout of the audio Pages repository')
    args = parser.parse_args()
    lines = json.loads((ROOT / 'work/pages-lines.json').read_text('utf-8'))
    if args.section:
        lines = [line for line in lines if line['id'].startswith('activities/act55side/' + args.section + ':')]
        if not lines:
            raise ValueError('Unknown story section: ' + args.section)
    voice = next(c for c in server.read_store().values() if c.get('speaker') == '凯尔希' and c.get('published'))
    target_root = args.shard_root.resolve() / 'audio'
    manifest_path = ROOT / 'pages/audio-manifest.json'
    rendered = 0
    completed = 0
    failed = []
    started = time.monotonic()
    try:
        for number, line in enumerate(lines, 1):
            match = re.fullmatch(r'activities/act55side/(level_act55side_[a-z0-9_]+):(\d+)', line['id'])
            if not match:
                raise ValueError('Unexpected step id: ' + line['id'])
            section, index = match.groups()
            output = target_root / section / (index + '.mp3')
            if output.is_file() and output.stat().st_size > 1000:
                completed += 1
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(3):
                try:
                    wav = server.synthesize(voice['id'], line['text'], voice['published']['version'])
                    break
                except Exception as error:
                    print(f'RETRY {number}/{len(lines)} attempt {attempt + 1}: {error}', file=sys.stderr, flush=True)
                    server.stop_engine()
                    time.sleep(3)
            else:
                failed.append(line['id'])
                continue
            temporary = output.with_suffix('.tmp')
            command = [FFMPEG, '-nostdin', '-v', 'error', '-y',
                       '-f', 'wav', '-i', 'pipe:0', '-ac', '1', '-ar', '24000', '-b:a', '64k', '-f', 'mp3', str(temporary)]
            result = subprocess.run(command, input=wav, capture_output=True, timeout=90,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode or not temporary.is_file():
                raise RuntimeError('MP3 encoding failed: ' + result.stderr.decode('utf-8', 'replace')[-300:])
            temporary.replace(output)
            rendered += 1
            completed += 1
            if rendered % 20 == 0 or number == len(lines):
                elapsed = time.monotonic() - started
                print(f'{completed}/{len(lines)} ready; {rendered} new; {elapsed:.0f}s; {section}:{index}', flush=True)
            if args.limit and rendered >= args.limit:
                break
    finally:
        manifest = {}
        for section in target_root.iterdir() if target_root.exists() else []:
            if section.is_dir():
                manifest[section.name] = sorted(int(file.stem) for file in section.glob('*.mp3') if file.stem.isdigit() and file.stat().st_size > 1000)
        manifest_path.write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
        server.stop_engine()
        cache_dir = ROOT / '.voice-data/audio'
        cleared = 0
        if cache_dir.is_dir():
            for cached in cache_dir.glob('*.wav'):
                if cached.parent == cache_dir and not cached.is_symlink():
                    cached.unlink(missing_ok=True)
                    cleared += 1
        print(f'Cleared {cleared} generated WAV cache files', flush=True)
        print(f'Manifest: {sum(map(len, manifest.values()))} files', flush=True)
    if failed:
        raise RuntimeError(f'{len(failed)} lines failed: ' + ', '.join(failed[:10]))

if __name__ == '__main__':
    main()
