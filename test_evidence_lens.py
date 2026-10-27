"""Evidence Lens contracts: real data equivalence, refusal and safe public receipts."""
import base64
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from catalogue import ROOT, load_catalogue
from evidence_lens import receipt, render_lens
from project_status import progress
from team import Trace


def registered_rows():
    def read(name):
        with (ROOT / 'data/zetaris' / name / 'data.csv').open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    usage = {r['name']: r['record_b64'] for r in read('vgc_usage')}
    rows = [[r['name'], r['record_b64'], usage.get(r['name'])] for r in read('pokedex')]
    return rows, [[read('reference')[0]['record_b64']]]


class LensTests(unittest.TestCase):
    def connected(self, rows=None, meta=None):
        original_rows, original_meta = registered_rows()
        api = Mock()
        api.query.side_effect = [original_rows if rows is None else rows, original_meta if meta is None else meta]
        with patch('catalogue.Zetaris', return_value=api):
            return load_catalogue(False)

    def test_connected_catalogue_equals_sample_and_receipts_are_real_measurements(self):
        data, _ = self.connected()
        lens = data.pop('evidence_lens')
        self.assertEqual(data, load_catalogue(True)[0])
        self.assertEqual((lens['catalogue_rows'], lens['usage_rows'], lens['set_options']), (1417, 358, 11376))
        self.assertEqual([r['returned_rows'] for r in lens['receipts']], [1417, 1])
        self.assertFalse(lens['sql_ranking'])

    def test_missing_duplicate_and_malformed_rows_refused(self):
        rows, _ = registered_rows()
        for corrupt in [rows[:-1], rows[:-1]+[rows[0]], [['bad', '%%%','%%%']]+rows[1:]]:
            with self.subTest(kind=len(corrupt)), self.assertRaises(RuntimeError): self.connected(rows=corrupt)

    def test_wrong_regulation_month_or_values_refused(self):
        rows, meta = registered_rows()
        doc = json.loads(base64.b64decode(meta[0][0]))
        for key, value in [('format_id', 'gen9ou'), ('statistics', {'number of battles': 1})]:
            bad = copy.deepcopy(doc); bad[key] = value
            encoded = base64.b64encode(json.dumps(bad).encode()).decode()
            with self.assertRaises(RuntimeError): self.connected(meta=[[encoded]])

    def test_receipt_accepts_no_transport_or_arbitrary_fields(self):
        good = receipt('catalogue_join', ['pokedex', 'vgc_usage'], 1417, '2026-10-27T15:00:00+00:00', 12.4)
        expected = {'query_id','purpose','tables','format_id','snapshot','cutoff','returned_rows','candidates_considered','started_at','duration_ms'}
        self.assertEqual(set(good), expected)
        for secret in ['nvapi-secret', 'Bearer secret', 'C:/private/.env', 'http://private?key=secret']:
            with self.assertRaises(ValueError): receipt(secret,['pokedex'],1,'2026-10-27T15:00:00+00:00',1)
            with self.assertRaises(ValueError): receipt('catalogue_join',[secret],1,'2026-10-27T15:00:00+00:00',1)
        with self.assertRaises(TypeError): receipt('catalogue_join',['pokedex'],1,'2026-10-27T15:00:00+00:00',1,authorization='secret')
        for value in [float('nan'),float('inf'),-1,'secret']:
            with self.assertRaises(ValueError): receipt('catalogue_join',['pokedex'],1,'2026-10-27T15:00:00+00:00',value)

    def test_report_and_build_progress_show_same_receipts(self):
        data,_ = self.connected(); lens=data['evidence_lens'];lens['favourites']=['Charizard']
        html=render_lens(lens)
        self.assertIn('965,304',html);self.assertIn('Charizard',html);self.assertIn('Sanitised query receipts',html)
        self.assertIn('still runs in Python',html)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);trace=Trace(root/'runs')
            trace.event('DataRetriever','zetaris_evidence',evidence_lens=lens)
            self.assertEqual(progress(trace.id,root)['evidence_html'],html)

    def test_offline_is_explicit_and_connected_failure_never_falls_back(self):
        self.assertIn('Offline sample',render_lens(None))
        with patch('catalogue.Zetaris',side_effect=RuntimeError('service stopped')),self.assertRaises(RuntimeError):
            load_catalogue(False)


if __name__ == '__main__': unittest.main()
