"""Stop only child processes belonging to the local launchers recorded by this setup."""
import json
from datetime import datetime
import psutil
from bot_environment import ROOT

for name in ('ui','bridge'):
    record_path=ROOT/'runtime'/f'{name}.pid.json'
    if not record_path.exists():
        continue
    record=json.loads(record_path.read_text('utf-8-sig'))
    try:
        proc=psutil.Process(record['pid'])
        expected=datetime.fromisoformat(record['created'].replace('Z','+00:00')).timestamp()
        if abs(proc.create_time()-expected)>1:
            continue
        if not any(record['script'].lower() in arg.lower() for arg in proc.cmdline()):
            continue
        children=proc.children(recursive=True)
        for child in reversed(children):
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        proc.terminate()
        psutil.wait_procs(children+[proc],timeout=5)
    except psutil.NoSuchProcess:
        pass
