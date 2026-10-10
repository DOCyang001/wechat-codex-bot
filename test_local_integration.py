import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import codex_bridge
from bot_environment import ROOT, configure
configure()

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client=codex_bridge.app.test_client()
        self.headers={'Authorization':'Bearer '+codex_bridge.settings()['key']}

    def test_authenticated_text_completion(self):
        with patch('codex_bridge.complete',return_value='好的') as generate:
            result=self.client.post('/v1/chat/completions',headers=self.headers,
                json={'model':codex_bridge.MODEL,'messages':[{'role':'user','content':'你好'}]})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json['choices'][0]['message']['content'],'好的')
        generate.assert_called_once()

    def test_disallows_unauthed_models_tools_and_images(self):
        base={'model':codex_bridge.MODEL,'messages':[{'role':'user','content':'x'}]}
        self.assertEqual(self.client.post('/v1/chat/completions',json=base).status_code,401)
        for changes in ({'model':'other'}, {'tools':[{'type':'function'}]}, {'stream':True},
                        {'messages':[{'role':'user','content':[{'type':'image_url'}]}]}):
            with patch('codex_bridge.complete') as generate:
                result=self.client.post('/v1/chat/completions',headers=self.headers,json=base|changes)
                self.assertEqual(result.status_code,400)
                generate.assert_not_called()

    def test_model_failure_does_not_produce_fallback(self):
        with patch('codex_bridge.complete',side_effect=RuntimeError('offline')):
            result=self.client.post('/v1/chat/completions',headers=self.headers,
                json={'model':codex_bridge.MODEL,'messages':[{'role':'user','content':'x'}]})
        self.assertEqual(result.status_code,502)
        self.assertNotIn('choices',result.json)

    def test_bot_suppresses_silence_and_other_contacts(self):
        tree=ast.parse((ROOT/'wechatbot-source/bot.py').read_text('utf8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='send_reply')
        module=ast.Module(body=[node],type_ignores=[])
        scope={'logger':unittest.mock.Mock(),'os':__import__('os'), 'json':json, 'LISTEN_LIST':[['Example Contact','我的语气']], 'is_sending_message':False}
        exec(compile(module,'send-only','exec'),scope)
        args=['Example Contact','peer','peer','incoming','[[[不回复]]]']
        with patch.dict(__import__('os').environ,{'LOCAL_ALLOWLIST_JSON':json.dumps(['Example Contact'])}):
            scope['send_reply'](*args)
            args[0]='not allowed'
            with self.assertRaises(ValueError):
                scope['send_reply'](*args)

    def test_context_refreshes_even_with_style_profile(self):
        tree=ast.parse((ROOT/'wechatbot-source/bot.py').read_text('utf8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inject_history_context')
        import threading
        read=unittest.mock.Mock(return_value='最新聊天')
        scope={'get_dynamic_config':lambda *args:True,'history_context_lock':threading.Lock(),
            'history_context_injected':set(),'history_context_block':read,'logger':unittest.mock.Mock()}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'context-only','exec'),scope)
        for _ in range(2):
            messages=[{'role':'system','content':'语气档案'}]
            scope['inject_history_context'](messages,'person','你好')
            self.assertIn('最新聊天',messages[0]['content'])
        self.assertEqual(read.call_count,2)
        self.assertTrue(all(c.kwargs['force'] for c in read.call_args_list))

    def test_health_identifies_this_deployment(self):
        self.assertEqual(self.client.get('/health').json['instance'],str(ROOT))

    def test_settings_reject_account_traversal_and_duplicate_targets(self):
        import bot_environment
        valid={'wechat_db_dir':'C:/example','wechat_account':'wxid_example',
            'listen_names':['Example Contact'],'model':'gpt-6.1-sol'}
        for changes in ({'wechat_account':'../other'}, {'wechat_account':'C:\\other'},
                        {'listen_names':['x','x']}, {'listen_names':[]}):
            with patch.object(Path,'exists',return_value=True), \
                 patch.object(Path,'read_text',return_value=json.dumps(valid|changes)):
                with self.assertRaises(ValueError):
                    bot_environment.load_settings()

    def test_registered_chat_type_never_opens_database_or_ui(self):
        from types import SimpleNamespace
        tree=ast.parse((ROOT/'wechatbot-source/wxbot.py').read_text('utf8'))
        owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WeChat')
        node=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='GetListenChatType')
        scope={}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'chat-type-only','exec'),scope)
        fail=unittest.mock.Mock(side_effect=AssertionError('Must not query UI or DB'))
        fixture=SimpleNamespace(listen={
            'peer':(SimpleNamespace(_wxid='wxid_example',ChatInfo=fail),None),
            'group':(SimpleNamespace(_wxid='123@chatroom',ChatInfo=fail),None)})
        self.assertEqual(scope['GetListenChatType'](fixture,'peer'),'friend')
        self.assertEqual(scope['GetListenChatType'](fixture,'group'),'group')
        self.assertIsNone(scope['GetListenChatType'](fixture,'missing'))
        fail.assert_not_called()

    def test_child_replaces_inherited_cache_before_wechat_init(self):
        import os,bot_environment
        tree=ast.parse((ROOT/'wechatbot-source/bot.py').read_text('utf8'))
        startup=next(n.lineno for n in tree.body if isinstance(n,ast.Expr)
            and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
            and n.value.func.id=='configure')
        interface=min(n.lineno for n in ast.walk(tree) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id=='WeChat')
        self.assertLess(startup,interface)
        with patch.dict(os.environ,{'LOCAL_WECHAT_CACHE':'inherited-parent-cache'}), \
             patch('os.getpid',return_value=9911):
            bot_environment.configure()
            self.assertEqual(Path(os.environ['LOCAL_WECHAT_CACHE']).name,'process-9911')

if __name__=='__main__':
    unittest.main()
