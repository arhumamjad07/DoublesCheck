"""Rehearse the exact HTTP recording path against a fresh local app. Zero model calls.

Run from a new checkout/app profile after registration. This is real connected
SQL acceptance, not a substitute for checking the browser layout.
"""
import argparse
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse
import uuid
import requests


def verify(base):
    parsed=urlparse(base)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost'} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'}:
        raise ValueError('Use only the local DoublesCheck app origin.')
    base=base.rstrip('/')
    session=requests.Session();session.trust_env=False
    results=[]
    try:
        home=session.get(base+'/',timeout=10,allow_redirects=False)
        if home.status_code!=200:raise RuntimeError('Local homepage unavailable.')
        match=re.search(r"'X-DoublesCheck-Token':(\"[^\"]+\")",home.text)
        if not match:raise RuntimeError('Local form token was not found.')
        token=json.loads(match[1])
        for favourite,expected in [('Charizard','Torkoal'),('Pelipper','Archaludon')]:
            run=uuid.uuid4().hex;start=time.monotonic()
            response=session.post(base+'/build',json={'run_id':run,'favourites':[favourite],
                'avoided':None,'clear':True,'sample':False,'ai':False,'objective':'simple'},
                headers={'X-DoublesCheck-Token':token},timeout=150,allow_redirects=False)
            if response.status_code!=200:raise RuntimeError('Connected recording build failed; response body withheld.')
            report_path=response.json().get('report')
            if report_path!=f'/runs/{run}/report.html':raise RuntimeError('Unexpected local report path.')
            html=session.get(base+report_path,timeout=10,allow_redirects=False)
            doc=session.get(base+f'/runs/{run}/report.json',timeout=10,allow_redirects=False).json()
            lens=doc.get('evidence_lens',{})
            if html.status_code!=200 or 'ZETARIS EVIDENCE LENS' not in html.text:raise RuntimeError('Visible Evidence Lens missing.')
            if doc['mode']!='zetaris' or doc['model_calls']!=0 or not lens.get('sql_ranking'):raise RuntimeError('Incorrect connected execution mode.')
            if lens['favourites']!=[favourite] or lens['partners'][0]['species']!=expected:raise RuntimeError('Favourite-specific evidence mismatch.')
            if lens['candidate_count']!=356 or len(lens['partners'])!=48:raise RuntimeError('Partner query counts differ.')
            if favourite not in [m['species'] for m in doc['team']] or doc['legality']['status']!='passed_showdown_validator':raise RuntimeError('Locked favourite or legality failed.')
            if not set(m['species'] for m in doc['team'] if m['species']!=favourite)<=set(p['species'] for p in lens['partners']):raise RuntimeError('Automatic partner escaped the SQL pool.')
            progress=session.get(base+'/progress?run='+run,timeout=10,allow_redirects=False).json()
            if progress['status']!='complete' or 'ZETARIS EVIDENCE LENS' not in progress['evidence_html']:raise RuntimeError('App flow did not expose completed SQL evidence.')
            results.append({'favourite':favourite,'run_id':run,'seconds':round(time.monotonic()-start,3),
                'candidate_count':356,'rows_returned':48,'top_sql_partner':expected,
                'team':[m['species'] for m in doc['team']], 'query_ms':round(sum(r['duration_ms'] for r in lens['receipts']),2)})
        if results[0]['team']==results[1]['team']:raise RuntimeError('Changing favourite did not change the team.')
        saved=session.get(base+'/saved/reasoning-repair/report.html',timeout=10,allow_redirects=False)
        if saved.status_code!=200 or 'Saved genuine Demo 3 model run' not in saved.text or 'missing_seed_terrain' not in saved.text:
            raise RuntimeError('Clearly labelled saved reasoning repair is unavailable.')
        return {'status':'passed','execution':'real_local_zetaris','model_calls':0,'builds':results,
                'saved_repair':'available_and_labelled_saved','receipt_scope':'Application query measurement IDs, not server-issued audit IDs'}
    finally:session.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',default='http://127.0.0.1:8765')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    result=verify(args.base_url)
    public=json.dumps(result,indent=2)
    if args.output:args.output.write_text(public+'\n',encoding='utf-8')
    print(public)
