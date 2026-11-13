"""Install fixed NLTK text resources through the host's network settings."""
from pathlib import Path
from urllib.request import urlopen
import io,zipfile
ROOT=Path(__file__).resolve().parents[2]
def install():
 target=ROOT/'engines/runtime/nltk_data';target.mkdir(parents=True,exist_ok=True)
 for kind,name in [('taggers','averaged_perceptron_tagger_eng'),('corpora','cmudict')]:
  destination=target/kind;destination.mkdir(exist_ok=True)
  url='https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/'+kind+'/'+name+'.zip'
  with urlopen(url,timeout=60) as response: data=response.read(20*1024*1024)
  with zipfile.ZipFile(io.BytesIO(data)) as archive:
   for entry in archive.infolist():
    if not (destination/entry.filename).resolve().is_relative_to(destination.resolve()):raise ValueError('Invalid archive path')
   archive.extractall(destination)
  print('Installed '+name,flush=True)
if __name__=='__main__':install()
