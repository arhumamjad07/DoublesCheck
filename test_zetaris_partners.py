"""Relational SQL and decision-boundary tests. SQLite is a local fixture, not live proof."""
import copy
import csv
import json
import sqlite3
import unittest
from unittest.mock import Mock, patch

from catalogue import ROOT, load_catalogue
from team_builder import build_team
from zetaris_partners import checked_partners, id_literal, partner_sql, retrieve_partners, verify_tables
from zetaris_schema import FIELDS, DATABASE, project


class SQLFixture:
    def __init__(self):
        self.db=sqlite3.connect(':memory:')
        self.db.create_function('CONCAT',-1,lambda *parts:''.join(str(p) for p in parts))
        self.db.execute("ATTACH DATABASE ':memory:' AS " + DATABASE)
        self.session=Mock()
        self.queries=[]
        for table,columns in FIELDS.items():
            self.db.execute(f"CREATE TABLE {DATABASE}.{table} ("+','.join(c+' TEXT' for c in columns)+')')
            with (ROOT/'data/zetaris-lens'/table/'data.csv').open(encoding='utf-8',newline='') as f:
                reader=csv.reader(f);next(reader)
                self.db.executemany(f'INSERT INTO {DATABASE}.{table} VALUES ('+','.join('?' for c in columns)+')',reader)
    def query(self,sql,limit=2000):
        self.queries.append(sql)
        return [list(r) for r in self.db.execute(sql).fetchall()[:limit]]
    def close(self): self.db.close()


class PartnerSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=load_catalogue(True)[0]
        cls.fixture=SQLFixture()
    @classmethod
    def tearDownClass(cls): cls.fixture.close()
    def data(self):
        data=copy.deepcopy(self.base)
        data['evidence_lens']={'receipts':[],'catalogue_rows':1417,'usage_rows':358,'set_options':11376,'sql_ranking':False}
        return data
    def retrieve(self,names=['Charizard'],avoid=[]):
        data=self.data()
        with patch('zetaris_partners.Zetaris',return_value=self.fixture):
            choices=retrieve_partners(data,names,avoid)
        return data,choices

    def test_query_ranking_equals_independent_sample_projection(self):
        for favourites in [['Charizard'],['Pelipper'],['Charizard','Sneasler']]:
            data,rows=self.retrieve(favourites,['Incineroar'])
            eligible=[m for n,m in self.base['species'].items() if m['eligible_species'] and m['sets'] and n not in favourites+['Incineroar']]
            expected=sorted(eligible,key=lambda m:(-sum(self.base['species'][n]['teammate_weights'].get(m['name'],0) for n in favourites),-m['usage'],m['name']))[:48]
            self.assertEqual([r['species'] for r in rows],[m['name'] for m in expected])
            self.assertEqual(data['evidence_lens']['candidate_count'],len(eligible))
            self.assertTrue(data['evidence_lens']['sql_ranking'])
            self.assertEqual(data['evidence_lens']['receipts'][-1]['returned_rows'],48)

    def test_changing_favourite_changes_sql_inputs_evidence_and_result(self):
        a,ar=self.retrieve(['Charizard']);a_sql=self.fixture.queries[-1]
        b,br=self.retrieve(['Pelipper']);b_sql=self.fixture.queries[-1]
        self.assertNotEqual(a_sql,b_sql);self.assertIn("'charizard'",a_sql);self.assertIn("'pelipper'",b_sql)
        self.assertNotEqual(ar,br);self.assertNotEqual(ar[0]['species'],br[0]['species'])

    def test_all_five_tables_have_exact_unique_keys_and_metadata(self):
        verify_tables(self.fixture,[])
        manifest=json.loads((ROOT/'data/zetaris-lens/manifest.json').read_text(encoding='utf-8'))
        projected=project(self.base)
        for table,values in projected.items():
            self.assertEqual(len(values),manifest['tables'][table]['rows'])
            with (ROOT/'data/zetaris-lens'/table/'data.csv').open(encoding='utf-8',newline='') as f:
                reader=csv.reader(f);self.assertEqual(next(reader),FIELDS[table])
                self.assertEqual(list(reader),[[str(v) for v in row] for row in values])

    def test_missing_and_duplicate_table_rows_refused(self):
        good=self.fixture.query("SELECT 'pokemon_facts',COUNT(*),COUNT(DISTINCT name) FROM DOUBLES_CHECK_LENS.pokemon_facts")
        for rows in [good, [['pokemon_facts',1417,1416]]*5]:
            api=Mock();api.query.return_value=rows
            with self.assertRaises(RuntimeError):verify_tables(api,[])

    def test_regulation_month_cutoff_or_hash_mismatch_refused(self):
        rows=self.fixture.query(' UNION ALL '.join(f"SELECT '{t}',COUNT(*),COUNT(DISTINCT "+({'teammate_relationships':"CONCAT(favourite_id,'|',partner)",'source_metadata':'format_id','sourced_sets':'set_id'}.get(t,'name'))+f') FROM {DATABASE}.{t}' for t in FIELDS))
        meta=self.fixture.query('SELECT '+','.join(FIELDS['source_metadata'])+' FROM '+DATABASE+'.source_metadata')
        for index,value in [(1,'gen9ou'),(2,'2024-10'),(3,'0'),(5,'wronghash')]:
            corrupt=copy.deepcopy(meta);corrupt[0][index]=value
            api=Mock();api.query.side_effect=[rows,corrupt]
            with self.assertRaises(RuntimeError):verify_tables(api,[])

    def test_sql_values_are_validated_ids_never_raw_user_input(self):
        for invalid in ["charizard'); DROP TABLE x; --",'a\\b',"farfetch'd",'a\n',None,1,'é']:
            with self.assertRaises(ValueError):id_literal(invalid)
        for invalid in ["Charizard'); DROP TABLE x; --",'Charizard\\',"<script>"]:
            with self.assertRaises(ValueError):partner_sql(self.base,[invalid],[])
        self.assertEqual(id_literal('charizard'),"'charizard'")

    def test_missing_duplicate_and_malformed_partner_rows_refused(self):
        sql,names,avoid=partner_sql(self.base,['Charizard'],[])
        rows=self.fixture.query(sql)
        for bad in [rows[:-1],rows[:-1]+[rows[0]],[['bad']]+rows[1:]]:
            with self.assertRaises(RuntimeError):checked_partners(self.base,bad,names,avoid)
        for index,value in [(0,'Miraidon'),(1,'NaN'),(1,2),(2,'Inf'),(3,0),(4,0),(1,'Bearer private')]:
            bad=copy.deepcopy(rows);bad[0][index]=value
            with self.assertRaises(RuntimeError):checked_partners(self.base,bad,names,avoid)

    def test_sql_failure_has_no_local_or_sample_fallback(self):
        data=self.data();api=Mock();api.query.side_effect=RuntimeError('Zetaris unavailable')
        with patch('zetaris_partners.Zetaris',return_value=api),self.assertRaises(RuntimeError):
            retrieve_partners(data,['Charizard'],[])
        self.assertNotIn('zetaris_partner_pool',data)
        self.assertFalse(data['evidence_lens']['sql_ranking'])
        api.session.close.assert_called_once()

    def test_receipts_cannot_copy_credentials_from_transport_or_sql(self):
        data,rows=self.retrieve()
        public=json.dumps(data['evidence_lens']['receipts'])
        for forbidden in ['Authorization','Bearer','ZETARIS_API_KEY','.env','C:/','SELECT ','http://']:
            self.assertNotIn(forbidden,public)
        self.assertEqual(set(data['evidence_lens']['receipts'][-1]),{'query_id','purpose','tables','format_id','snapshot','cutoff','returned_rows','candidates_considered','started_at','duration_ms'})

    def test_connected_and_equivalent_sample_pool_produce_same_valid_team(self):
        connected,_=self.retrieve()
        offline=copy.deepcopy(self.base);offline['zetaris_partner_pool']=list(connected['zetaris_partner_pool'])
        a,check,_=build_team(connected,['Charizard'])
        b,_,_=build_team(offline,['Charizard'])
        self.assertEqual(a,b);self.assertTrue(check['valid'])
        self.assertTrue(set(m['species'] for m in a[1:])<=set(connected['zetaris_partner_pool']))

    def test_changing_returned_candidate_pool_changes_actual_recommendation(self):
        # Controlled result boundary, not fabricated live evidence: each five-row
        # source pool forces its own legal partners into the final six.
        a,_,_=build_team(self.base,['Charizard'])
        b,_,_=build_team(self.base,['Charizard'],[a[-1]['species']])
        results=[]
        for team in [a,b]:
            data=copy.deepcopy(self.base)
            data['zetaris_partner_pool']=[m['species'] for m in team if m['species']!='Charizard']
            actual,check,_=build_team(data,['Charizard'])
            self.assertTrue(check['valid']);results.append({m['species'] for m in actual})
        self.assertNotEqual(*results)


if __name__=='__main__':unittest.main()
