"""Render and publish a story to its GitHub Pages audio shard, one section at a time."""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, getproxies, urlopen

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
SHARD_MAX_BYTES = 800 * 1024 * 1024
PROXY = getproxies().get('https')
GIT = ['git', '-c', 'http.version=HTTP/1.1'] + (['-c', 'http.proxy=' + PROXY] if PROXY else [])


def say(*items):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), *items, flush=True)


def run(args, cwd=ROOT, stream=False, check=True):
    say('RUN', *args)
    result = subprocess.run(args, cwd=cwd, text=True,
                            stdout=None if stream else subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout[-1200:], flush=True)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode})')
    return result


def remote_sha(cwd):
    output = run(GIT + ['ls-remote', 'origin', 'refs/heads/main'], cwd).stdout.strip()
    if not output:
        raise RuntimeError('Remote main unavailable')
    return output.split()[0]


def push(cwd):
    failures = 0
    rebases = 0
    while failures < 5:
        result = run(GIT + ['push', 'origin', 'main'], cwd, check=False)
        if result.returncode == 0:
            return
        if 'fetch first' in result.stdout or 'non-fast-forward' in result.stdout:
            rebases += 1
            if rebases > 3:
                raise RuntimeError('Remote main changed too often during push')
            run(GIT + ['fetch', 'origin', 'main'], cwd)
            run(['git', '-c', 'rebase.autoStash=true', 'rebase', 'origin/main'], cwd)
            continue
        failures += 1
        say('Push retry', failures, '/5')
        time.sleep(15)
    raise RuntimeError('Git push failed after five attempts')


def key_for(group_id, chapter):
    # The first published story used bare slugs. New stories use full IDs so
    # chapter names from other stories can never collide.
    return chapter['id'].split('/')[-1] if group_id == 'act55side' else chapter['id']


def expected_lines(lines, chapter_id):
    prefix = chapter_id + ':'
    return [int(item['id'].split(':')[-1]) for item in lines if item['id'].startswith(prefix)]


def write_release_state(group_id, chapters, lines, shard):
    manifest_path = WEB / 'pages/audio-manifest.json'
    voiced_path = WEB / 'pages/voiced-chapters.json'
    manifest = json.loads(manifest_path.read_text('utf-8'))
    voiced = json.loads(voiced_path.read_text('utf-8'))
    for chapter in chapters:
        slug = chapter['id'].split('/')[-1]
        key = key_for(group_id, chapter)
        indices = expected_lines(lines, chapter['id'])
        if not indices:
            raise RuntimeError('No lines in ' + chapter['id'])
        for index in indices:
            file = shard / 'audio' / slug / (str(index) + '.mp3')
            if not file.is_file() or file.stat().st_size < 1000:
                raise RuntimeError('Audio missing: ' + str(file))
        manifest[key] = indices
        if key not in voiced:
            voiced.append(key)
    manifest_path.write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
    voiced_path.write_text(json.dumps(voiced, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def wait_live(page, slug, last_index):
    url = page + 'audio/' + slug + '/' + str(last_index) + '.mp3'
    for _ in range(50):
        try:
            with urlopen(Request(url, method='HEAD', headers={'User-Agent': 'VoiceOfTerra'}), timeout=15) as response:
                if response.status == 200:
                    say('PUBLISHED', slug, url)
                    return
        except (HTTPError, URLError, TimeoutError):
            pass
        time.sleep(15)
    raise RuntimeError('Pages did not publish ' + slug + ' within 13 minutes')


def main(group_id, shard_name, once):
    if not re.fullmatch(r'[a-z0-9_]+', group_id):
        raise ValueError('Invalid group id')
    if not re.fullmatch(r'vot-audio-\d{8}', shard_name):
        raise ValueError('Invalid shard name')
    page = f'https://luoul-123.github.io/{shard_name}/'
    sites = json.loads((WEB / 'pages/audio-sites.json').read_text('utf-8'))
    if sites['prefixes'].get(f'activities/{group_id}/') != page:
        raise RuntimeError('Audio site mapping does not match this story and shard')
    catalog = json.loads((WEB / 'pages/catalog.json').read_text('utf-8'))
    group = next((item for item in catalog if item['id'] == group_id), None)
    if not group or not group['chapters']:
        raise RuntimeError('Story group missing from catalog')
    chapters = group['chapters']
    lines_name = 'pages-lines.json' if group_id == 'act55side' else f'pages-lines-{group_id}.json'
    lines_file = WEB / 'work' / lines_name
    lines = json.loads(lines_file.read_text('utf-8'))
    shard = WEB / 'work' / shard_name
    if not (shard / '.git').is_dir():
        raise RuntimeError('Audio shard checkout missing: ' + str(shard))

    all_voiced = json.loads((WEB / 'pages/voiced-chapters.json').read_text('utf-8'))
    keys = [key_for(group_id, chapter) for chapter in chapters]
    released = [key for key in all_voiced if key in keys]
    if released != keys[:len(released)]:
        raise RuntimeError('Released sections are not a catalog prefix')
    if run(['git', 'diff', '--cached', '--quiet'], check=False).returncode:
        raise RuntimeError('Git index has unrelated staged changes')
    if remote_sha(ROOT) != run(['git', 'rev-parse', 'HEAD']).stdout.strip():
        raise RuntimeError('Remote main differs from local HEAD')
    if remote_sha(shard) != run(['git', 'rev-parse', 'HEAD'], shard).stdout.strip():
        raise RuntimeError('Remote audio shard differs from local HEAD')

    for position in range(len(released), len(chapters)):
        chapter = chapters[position]
        slug = chapter['id'].split('/')[-1]
        say('SECTION', position + 1, '/', len(chapters), slug)
        run([sys.executable, 'scripts/generate-pages-audio.py', '--group', group_id,
             '--section', slug, '--shard-root', str(shard)], WEB, stream=True)
        indices = expected_lines(lines, chapter['id'])
        if not indices:
            raise RuntimeError('No lines in ' + chapter['id'])
        shard_bytes = sum(file.stat().st_size for file in (shard / 'audio').rglob('*.mp3'))
        if shard_bytes > SHARD_MAX_BYTES:
            raise RuntimeError('Audio shard exceeds 800 MiB safety budget')
        run(['git', 'add', '--', 'audio/' + slug], shard)
        run(['git', 'diff', '--cached', '--check', '--', 'audio/' + slug], shard)
        if run(['git', 'diff', '--cached', '--quiet'], shard, check=False).returncode:
            run(['git', 'commit', '--only', '-m',
                 f'Publish Kaltsit audio {group_id} section {position + 1}/{len(chapters)}: {slug}',
                 '--', 'audio/' + slug], shard)
            push(shard)
        wait_live(page, slug, max(indices))
        write_release_state(group_id, [chapter], lines, shard)
        run(['node', 'scripts/verify-pages.mjs', '--allow-extra-local-audio'], WEB)
        files = ['web/pages/audio-manifest.json', 'web/pages/voiced-chapters.json']
        run(['git', 'add', '--'] + files)
        run(['git', 'diff', '--cached', '--check', '--'] + files)
        if run(['git', 'diff', '--cached', '--quiet'], check=False).returncode:
            run(['git', 'commit', '--only', '-m',
                 f'Publish Kaltsit voice {group_id} section {position + 1}/{len(chapters)}: {slug}',
                 '--'] + files)
            push(ROOT)
        if once:
            break
    say('DONE', group_id, len(chapters), 'sections')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', default='act55side')
    parser.add_argument('--shard', default='vot-audio-20261101')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    try:
        main(args.group, args.shard, args.once)
    except Exception as error:
        say('FAILED', repr(error))
        raise
