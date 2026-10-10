"""Interactive first-run settings wizard. No real data is embedded in the repository."""
import argparse
import json
import os
from pathlib import Path
from bot_environment import ROOT, SETTINGS, load_settings

def ask(prompt,default=''):
    suffix=f' [{default}]' if default else ''
    return input(prompt+suffix+': ').strip() or default

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--codex-cli-js',default='')
    args=parser.parse_args()
    if SETTINGS.exists():
        data=load_settings()
        if args.codex_cli_js:
            data['codex_cli_js']=args.codex_cli_js
        SETTINGS.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
        print('Using existing settings.local.json')
        return
    default=str(Path.home()/'Documents/xwechat_files')
    folder=Path(ask('微信设置中显示的 xwechat_files 数据目录',default)).expanduser().resolve()
    if not folder.is_dir():
        raise RuntimeError('Data directory does not exist. Open WeChat Settings > Storage and check the path.')
    accounts=sorted(p.name for p in folder.iterdir() if p.is_dir() and (p/'db_storage').is_dir())
    if not accounts:
        raise RuntimeError('No account with db_storage found in the selected directory')
    for i,account in enumerate(accounts,1):
        print(f'{i}. {account}')
    selected=int(ask('选择当前登录账号的序号','1'))
    if not 1<=selected<=len(accounts):
        raise ValueError('Invalid account selection')
    names=[]
    print('输入要启用的准确联系人备注名或群名；每次输入一个，空行结束。')
    while True:
        name=ask('聊天名称')
        if not name:
            break
        if name not in names:
            names.append(name)
    if not names:
        raise ValueError('At least one chat must be selected')
    model=ask('Codex 账号可使用的模型 ID','gpt-6.1-sol')
    SETTINGS.write_text(json.dumps({'wechat_db_dir':str(folder),'wechat_account':accounts[selected-1],
        'listen_names':names,'model':model,'codex_cli_js':args.codex_cli_js},ensure_ascii=False,indent=2),'utf8')
    load_settings()
    print('Local configuration saved. Installation does not start message sending.')

if __name__=='__main__':
    main()
