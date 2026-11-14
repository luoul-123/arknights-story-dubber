"""Render and publish one complete SideStory section at a time."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen, getproxies
from urllib.error import HTTPError, URLError

WEB=Path(__file__).resolve().parents[1]
ROOT=WEB.parent
SHARD=WEB/'work/vot-audio-20261101'
PAGE='https://luoul-123.github.io/vot-audio-20261101/'
SHARD_MAX_BYTES=800*1024*1024
PROXY=getproxies().get('https')
GIT=['git','-c','http.version=HTTP/1.1']+(['-c','http.proxy='+PROXY] if PROXY else [])

def say(*items):print(time.strftime('%Y-%m-%d %H:%M:%S'),*items,flush=True)
def run(args,cwd=ROOT,stream=False,check=True):
    say('RUN',*args)
    result=subprocess.run(args,cwd=cwd,text=True,stdout=None if stream else subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.stdout:print(result.stdout[-1200:],flush=True)
    if check and result.returncode:raise RuntimeError(f'{args[0]} failed ({result.returncode})')
    return result

def remote_sha(cwd=ROOT):
    output=run(GIT+['ls-remote','origin','refs/heads/main'],cwd).stdout.strip()
    if not output:raise RuntimeError('Remote main unavailable')
    return output.split()[0]

def push(cwd=ROOT):
    failures=0
    rebases=0
    while failures<5:
        result=run(GIT+['push','origin','main'],cwd,check=False)
        if result.returncode==0:return
        if 'fetch first' in result.stdout or 'non-fast-forward' in result.stdout:
            # The maintainer may edit README on GitHub while a section renders.
            # Replay only this unpublished local commit; never force-push.
            rebases+=1
            if rebases>3:raise RuntimeError('Remote main changed too often during push')
            run(GIT+['fetch','origin','main'],cwd)
            run(['git','rebase','origin/main'],cwd)
            continue
        failures+=1
        say('Push retry',failures,'/5')
        time.sleep(15)
    raise RuntimeError('Git push failed after five attempts')

def expected_lines(lines,slug):
    prefix='activities/act55side/'+slug+':'
    return [int(item['id'].split(':')[-1]) for item in lines if item['id'].startswith(prefix)]

def write_release_state(slugs,lines):
    manifest={}
    for slug in slugs:
        indices=expected_lines(lines,slug)
        if not indices:raise RuntimeError('No lines in '+slug)
        for index in indices:
            file=SHARD/'audio'/slug/(str(index)+'.mp3')
            if not file.is_file() or file.stat().st_size<1000:raise RuntimeError('Audio missing: '+str(file))
        manifest[slug]=indices
    (WEB/'pages/audio-manifest.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
    (WEB/'pages/voiced-chapters.json').write_text(json.dumps(slugs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def wait_live(slug,last_index):
    url=PAGE+'audio/'+slug+'/'+str(last_index)+'.mp3'
    for attempt in range(50):
        try:
            with urlopen(Request(url,method='HEAD',headers={'User-Agent':'VoiceOfTerra'}),timeout=15) as response:
                if response.status==200:
                    say('PUBLISHED',slug,url)
                    return
        except (HTTPError,URLError,TimeoutError):pass
        time.sleep(15)
    raise RuntimeError('Pages did not publish '+slug+' within 13 minutes')

def main(once=False):
    catalog=json.loads((WEB/'pages/catalog.json').read_text('utf-8'))
    chapters=next(group for group in catalog if group['id']=='act55side')['chapters']
    slugs=[chapter['id'].split('/')[-1] for chapter in chapters]
    lines=json.loads((WEB/'work/pages-lines.json').read_text('utf-8'))
    released=json.loads(run(['git','show','HEAD:web/pages/voiced-chapters.json']).stdout)
    if released!=slugs[:len(released)]:raise RuntimeError('Released sections are not a catalog prefix')
    if run(['git','diff','--cached','--quiet'],check=False).returncode:raise RuntimeError('Git index has unrelated staged changes')
    if remote_sha()!=run(['git','rev-parse','HEAD']).stdout.strip():raise RuntimeError('Remote main differs from local HEAD')
    if remote_sha(SHARD)!=run(['git','rev-parse','HEAD'],SHARD).stdout.strip():raise RuntimeError('Remote audio shard differs from local HEAD')
    for position in range(len(released),len(slugs)):
        slug=slugs[position]
        say('SECTION',position+1,'/24',slug)
        run([sys.executable,'scripts/generate-pages-audio.py','--section',slug],WEB,stream=True)
        shard_bytes=sum(file.stat().st_size for file in (SHARD/'audio').rglob('*.mp3'))
        if shard_bytes>SHARD_MAX_BYTES:raise RuntimeError('Audio shard exceeds 800 MiB safety budget')
        run(['git','add','--','audio/'+slug],SHARD)
        run(['git','diff','--cached','--check','--','audio/'+slug],SHARD)
        run(['git','commit','--only','-m',f'Publish Kaltsit audio section {position+1}/24: {slug}','--','audio/'+slug],SHARD)
        push(SHARD)
        wait_live(slug,max(expected_lines(lines,slug)))
        current=slugs[:position+1]
        write_release_state(current,lines)
        run(['node','scripts/verify-pages.mjs','--allow-extra-local-audio'],WEB)
        files=['web/pages/audio-manifest.json','web/pages/voiced-chapters.json']
        run(['git','add','--']+files)
        run(['git','diff','--cached','--check','--']+files)
        run(['git','commit','--only','-m',f'Publish Kaltsit voice section {position+1}/24: {slug}','--']+files)
        push()
        if once:break

if __name__=='__main__':
    args=argparse.ArgumentParser()
    args.add_argument('--once',action='store_true')
    try:main(args.parse_args().once)
    except Exception as error:
        say('FAILED',repr(error))
        raise
