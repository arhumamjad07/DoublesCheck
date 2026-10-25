"""Optional localhost integration check; model responses are explicitly simulated."""
import json
from pathlib import Path
import re
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
import uuid
from http.server import ThreadingHTTPServer

import app
import team
from catalogue import ROOT,load_catalogue
from test_ai_coach import ScriptedClient,approval
from test_reasoning_contracts import inspect
from nightshift_client import CoachError


class HTTPContinuationTests(unittest.TestCase):
    def test_pause_button_and_authenticated_continuation_complete_one_review(self):
        data,_=load_catalogue(True)
        client=ScriptedClient([inspect,CoachError('Upstream temporarily unavailable',code='gateway_stream_error',retryable=True),approval])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            for name in ['catalogue.json','sources.json']:shutil.copyfile(ROOT/'data'/name,root/'data'/name)
            real_execute=team.execute
            def build(*args,**kwargs):return real_execute(*args,**kwargs,ai_client=client)
            with patch('team.ROOT',root),patch('app.ROOT',root),patch('team.load_catalogue',return_value=(data,'simulated Zetaris HTTP fixture')),patch('app.execute',side_effect=build):
                server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
                with patch('app.PORT',server.server_port):
                    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                    try:
                        base='http://127.0.0.1:'+str(server.server_port)
                        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with opener.open(base+'/') as r:html=r.read().decode()
                        self.assertIn('Continue this review',html)
                        token=json.loads(re.search(r"'X-DoublesCheck-Token':(\"[^\"]+\")",html).group(1))
                        run_id=uuid.uuid4().hex
                        def post(path,body,key=token):
                            request=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-DoublesCheck-Token':key},method='POST')
                            return opener.open(request,timeout=60)
                        body={'run_id':run_id,'favourites':['Charizard'],'avoided':'Incineroar','clear':False,'sample':False,'ai':True,'objective':'simple'}
                        with self.assertRaises(urllib.error.HTTPError) as caught:post('/build',body)
                        self.assertEqual(caught.exception.code,503)
                        paused=json.loads(caught.exception.read())
                        self.assertTrue(paused['resume_available']);self.assertEqual(paused['remaining_model_calls'],6)
                        self.assertEqual(client.calls,2)
                        self.assertFalse((root/'runs'/run_id/'report.html').exists())
                        with self.assertRaises(urllib.error.HTTPError) as denied:post('/resume',{'run_id':run_id},'wrong-token')
                        self.assertEqual(denied.exception.code,403);self.assertEqual(client.calls,2)
                        with post('/resume',{'run_id':run_id}) as r:answer=json.load(r)
                        with opener.open(base+answer['report']) as r:report=r.read().decode()
                        self.assertIn('Execution:</b> simulated',report)
                        self.assertEqual(client.calls,3)
                        with opener.open(base+'/progress?run='+run_id) as r:progress=json.load(r)
                        self.assertEqual(progress['status'],'complete')
                        self.assertTrue(any(e['action']=='review_resumed' for e in progress['events']))
                        with self.assertRaises(urllib.error.HTTPError):post('/resume',{'run_id':run_id})
                        self.assertEqual(client.calls,3)
                    finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
