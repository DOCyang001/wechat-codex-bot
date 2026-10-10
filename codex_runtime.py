from pathlib import Path
import json, os, shutil, subprocess, tempfile, winreg
ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT/'runtime/model'

def command():
    node = shutil.which('node') or shutil.which('node.exe')
    from bot_environment import load_settings
    configured=load_settings().get('codex_cli_js','')
    cli = Path(configured) if configured else Path(os.environ['APPDATA'])/'npm/node_modules/@openai/codex/bin/codex.js'
    if not node or not cli.exists():
        raise RuntimeError('Codex CLI or Node.js is missing')
    return [node,str(cli)]

def environment():
    env = os.environ.copy()
    env['PYTHONIOENCODING']='utf-8'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as k:
            enabled=winreg.QueryValueEx(k,'ProxyEnable')[0]
            proxy=winreg.QueryValueEx(k,'ProxyServer')[0]
        if enabled and proxy and '=' not in proxy:
            env.setdefault('HTTPS_PROXY','http://'+proxy)
            env.setdefault('HTTP_PROXY','http://'+proxy)
    except OSError:
        pass
    return env

