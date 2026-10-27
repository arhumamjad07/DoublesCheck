"""HTTP evidence contracts with explicit service fixtures, no live provider calls."""
import json
from pathlib import Path
import re
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import uuid
from http.server import ThreadingHTTPServer

import app
from catalogue import ROOT
from test_evidence_lens import registered_rows
from test_zetaris_partners import SQLFixture


class EvidenceAPI(SQLFixture):
    def query(self,sql,limit=2000):
        if 'FROM DOUBLES_CHECK.pokedex' in sql:return registered_rows()[0]
        if 'FROM DOUBLES_CHECK.reference' in sql:return registered_rows()[1]
        return super().query(sql,limit)


class HTTPEvidenceTests(unittest.TestCase):
    def with_server(self, callback):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();(root/'examples/reasoning-repair').mkdir(parents=True)
            for n in ['catalogue.json','sources.json']:shutil.copyfile(ROOT/'data'/n,root/'data'/n)
            shutil.copyfile(ROOT/'examples/reasoning-repair/report.html',root/'examples/reasoning-repair/report.html')
            api=EvidenceAPI()
            with patch('app.ROOT',root),patch('team.ROOT',root),patch('catalogue.Zetaris',return_value=api),patch('zetaris_partners.Zetaris',return_value=api):
                server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
                with patch('app.PORT',server.server_port):
                    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                    try:
                        base='http://127.0.0.1:'+str(server.server_port)
                        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with opener.open(base+'/') as r:home=r.read().decode()
                        token=json.loads(re.search(r"'X-DoublesCheck-Token':(\"[^\"]+\")",home).group(1))
                        def post(body):
                            return opener.open(urllib.request.Request(base+'/build',data=json.dumps(body).encode(),
                                headers={'Content-Type':'application/json','X-DoublesCheck-Token':token}),timeout=90)
                        callback(base,opener,post,root,api)
                    finally:server.shutdown();server.server_close();api.close()

    def test_connected_sql_failure_withholds_report_and_never_uses_sample(self):
        def check(base,opener,post,root,api):
            original=api.query
            def failing(sql,limit=2000):
                if 'DOUBLES_CHECK_LENS' in sql:raise RuntimeError('Connected evidence query unavailable; result withheld.')
                return original(sql,limit)
            api.query=failing
            run=uuid.uuid4().hex
            with patch('team.build_team') as builder:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    post({'run_id':run,'favourites':['Charizard'],'sample':False,'clear':True,'ai':False})
                self.assertEqual(error.exception.code,400)
                self.assertIn('withheld',json.loads(error.exception.read())['error'])
                builder.assert_not_called()
            self.assertFalse((root/'runs'/run/'report.html').exists())
        self.with_server(check)

    def test_offline_report_and_saved_repair_have_honest_labels(self):
        def check(base,opener,post,root,api):
            api.query=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('Offline mode made a service request'))
            with post({'favourites':['Charizard'],'sample':True,'clear':True,'ai':False}) as r:answer=json.load(r)
            with opener.open(base+answer['report']) as r:html=r.read().decode()
            self.assertIn('Offline sample',html);self.assertNotIn('Live Zetaris queries completed',html)
            with opener.open(base+'/saved/reasoning-repair/report.html') as r:saved=r.read().decode()
            self.assertIn('Saved genuine Demo 3 model run',saved)
            self.assertIn('Recovery evidence only',saved)
            self.assertIn('missing_seed_terrain',saved)
        self.with_server(check)


if __name__=='__main__':unittest.main()
