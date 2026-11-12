"""Start local development without printing or passing credentials in argv."""
import os, runpy
from pathlib import Path
base=Path(__file__).resolve().parent
for line in (base.parent/".dev.vars").read_text("utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        key,value=line.split("=",1)
        if key=="VOICE_BACKEND_TOKEN":os.environ[key]=value
runpy.run_path(str(base/"server.py"),run_name="__main__")
