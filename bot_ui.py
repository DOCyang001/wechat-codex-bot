"""Start the upstream editor without occupied-port termination or browser side effects."""
import os
import sys
from bot_environment import ROOT, configure
configure()
os.chdir(ROOT/'wechatbot-source')
sys.path.insert(0,str(ROOT/'wechatbot-source'))
import config_editor
import json
import psutil

@config_editor.app.get('/local_instance')
def local_instance():
    from flask import jsonify
    return jsonify(instance=str(ROOT))


@config_editor.app.get('/local_status')
def local_status():
    from flask import jsonify
    try:
        record=json.loads((ROOT/'runtime/bot_ready.json').read_text('utf8'))
        proc=psutil.Process(record['pid'])
        if not any(str(ROOT/'wechatbot-source/bot.py').lower().replace('\\','/')
            in arg.lower().replace('\\','/') for arg in proc.cmdline()):
            raise ValueError('Process changed')
        health=json.loads((ROOT/'runtime/bot_health.json').read_text('utf8'))
        import time
        if health['pid']!=record['pid'] or time.time()-health['updated_at']>15 \
            or not health['listener_alive'] or not health['reply_worker_alive']:
            raise ValueError('Critical bot threads are not ready')
        record.update(health)
        return jsonify(record)
    except (OSError,ValueError,psutil.Error):
        return jsonify(ready=False),503

if __name__ == '__main__':
    config_editor.validate_config()
    config_editor.app.run(host='127.0.0.1',port=8765,debug=False)

