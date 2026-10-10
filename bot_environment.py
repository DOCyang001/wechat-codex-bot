import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SETTINGS=ROOT/'settings.local.json'

def load_settings():
    if not SETTINGS.exists():
        raise RuntimeError('Run install.cmd first, or create settings.local.json from settings.example.json')
    data=json.loads(SETTINGS.read_text('utf-8-sig'))
    names=data.get('listen_names')
    if not isinstance(names,list) or not names or any(not isinstance(n,str) or not n.strip() for n in names):
        raise ValueError('listen_names must contain exact chat display names')
    if len(names)!=len(set(names)):
        raise ValueError('listen_names contains duplicates')
    for key in ('wechat_db_dir','wechat_account','model'):
        if not isinstance(data.get(key),str) or not data[key].strip():
            raise ValueError('Missing setting: '+key)
    account=data['wechat_account']
    if Path(account).name!=account or '/' in account or '\\' in account or account in ('.','..'):
        raise ValueError('wechat_account must be a directory name, not a path')
    return data

def configure():
    config=load_settings()
    os.environ['PYTHONIOENCODING']='utf-8'
    os.environ['LOCAL_WECHAT_DB_DIR']=config['wechat_db_dir']
    os.environ['LOCAL_WECHAT_ACCOUNT']=config['wechat_account']
    os.environ['LOCAL_WECHAT_CACHE']=str(ROOT/'runtime/wechatdb'/f'process-{os.getpid()}')
    os.environ['WECHATAUTO_KEYS_DIR']=str(ROOT/'runtime/wechatdb/keys')
    os.environ['WECHATAUTO_RHYTHM']='natural'
    os.environ['LOCAL_REPLY_RULES']=str(ROOT/'runtime/reply_rules.txt')
    os.environ['LOCAL_ALLOWLIST_JSON']=json.dumps(config['listen_names'],ensure_ascii=False)
    existing=os.environ.get('NO_PROXY','')
    os.environ['NO_PROXY']=existing+',localhost,127.0.0.1,::1'

