"""Download or prepare the Kal'tsit production voice dataset."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
from urllib.parse import urldefrag
from urllib.request import Request, urlopen
import imageio_ffmpeg

BASE = Path(__file__).resolve().parent
WEB = BASE.parent
SOURCES = BASE / 'curated-voice-sources.json'
NAMES = ['凯尔希']


def prepare():
    people = json.loads(SOURCES.read_text('utf-8'))
    folder = WEB / 'work' / 'curated-network'
    folder.mkdir(parents=True, exist_ok=True)
    for person in people:
        for clip in person['clips']:
            url = urldefrag(clip['source'])[0]
            original = folder / (hashlib.sha256(url.encode()).hexdigest() + '.mp3')
            if not original.exists():
                request = Request(url, headers={'User-Agent': 'TerraVoice/1.0'})
                with urlopen(request, timeout=60) as response:
                    data = response.read(20 * 1024 * 1024 + 1)
                if not data or len(data) > 20 * 1024 * 1024:
                    raise ValueError('音频为空或超过 20 MB：' + url)
                temporary = original.with_suffix('.tmp')
                temporary.write_bytes(data)
                temporary.replace(original)
            target = folder / (hashlib.sha256(clip['source'].encode()).hexdigest() + '.wav')
            command = [imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-v', 'error', '-y', '-i', str(original)]
            if clip.get('trimSeconds'):
                command += ['-t', str(clip['trimSeconds'])]
            subprocess.run(command + ['-vn', '-ac', '1', '-ar', '32000', '-c:a', 'pcm_s16le', str(target)], check=True, timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            clip['path'] = str(target)
        print(person['speaker'] + ' 素材已准备', flush=True)
    manifest = folder / 'manifest.json'
    manifest.write_text(json.dumps(people, ensure_ascii=False, indent=2), 'utf-8')
    print('导入清单：' + str(manifest))


def call(endpoint, data=None):
    config = {}
    env_file = WEB / '.dev.vars'
    if env_file.exists():
        config = dict(line.split('=', 1) for line in env_file.read_text('utf-8').splitlines() if '=' in line and not line.startswith('#'))
    token = os.environ.get('VOICE_BACKEND_TOKEN') or config.get('VOICE_BACKEND_TOKEN')
    base = os.environ.get('VOICE_BACKEND_URL') or config.get('VOICE_BACKEND_URL', 'http://127.0.0.1:9881')
    if not token:
        raise ValueError('先配置 VOICE_BACKEND_TOKEN')
    request = Request(base.rstrip('/') + '/' + endpoint, data=json.dumps(data, ensure_ascii=False).encode() if data is not None else None, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def profiles():
    found = {c['speaker']: c for c in call('admin/characters')['characters'] if c['speaker'] in NAMES}
    if set(found) != set(NAMES):
        raise ValueError('请先准备并导入凯尔希的网络素材')
    return [found[name] for name in NAMES]


def train(epochs):
    for person in profiles():
        if person['models']:
            print(person['speaker'] + ' 已有新模型，跳过训练', flush=True)
            continue
        job = call('admin/train', {'id': person['id'], 'epochs': epochs})
        last = None
        while True:
            state = call('admin/jobs/' + job['id'])
            if state['message'] != last:
                print(person['speaker'] + '：' + state['message'], flush=True)
                last = state['message']
            if state['state'] == 'done':
                break
            if state['state'] not in ('queued', 'running'):
                raise RuntimeError(state['message'])
            time.sleep(3)


def publish():
    people = profiles()
    if not all(c['models'] for c in people):
        raise ValueError('凯尔希模型尚未完成训练')
    for person in people:
        call('admin/publish', {'id': person['id'], 'mode': 'trained'})
        print(person['speaker'] + ' 已发布', flush=True)
    ids = {c['speaker']: c['id'] for c in people}
    call('admin/defaults', {'female': ids['凯尔希'], 'male': ids['凯尔希'], 'narrator': ids['凯尔希']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'train', 'publish'])
    parser.add_argument('--epochs', type=int, default=8, choices=range(1, 21))
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'train':
        train(args.epochs)
    else:
        publish()
