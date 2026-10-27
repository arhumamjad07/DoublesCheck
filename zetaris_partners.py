"""Bounded favourite-specific SQL shortlist. No sample fallback and no model calls."""
import json
import math
import re

from catalogue import ROOT, Zetaris
from evidence_lens import FORMAT, MONTH, CUTOFF, BATTLES, measured_query
from zetaris_schema import DATABASE, FIELDS

POOL_SIZE = 48


def id_literal(value):
    # SQL values come only from pinned Showdown IDs. Arbitrary names never become SQL.
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9]{1,40}", value):
        raise ValueError("Unsafe species identifier; no SQL was sent.")
    return "'" + value + "'"


def scope(alias):
    return f"{alias}.format_id = '{FORMAT}' AND {alias}.snapshot_month = '{MONTH}' AND CAST({alias}.cutoff AS INT) = {CUTOFF}"


def verify_tables(api, receipts, manifest=None):
    manifest = manifest or json.loads((ROOT / 'data/zetaris-lens/manifest.json').read_text(encoding='utf-8'))
    keys = {'pokemon_facts':'name', 'usage_snapshots':'name',
            'teammate_relationships':"CONCAT(favourite_id, '|', partner)", 'sourced_sets':'set_id', 'source_metadata':'format_id'}
    sql = ' UNION ALL '.join(f"SELECT '{t}', COUNT(*), COUNT(DISTINCT {keys[t]}) FROM {DATABASE}.{t}" for t in FIELDS)
    rows = measured_query(api,sql,'normalised_integrity',list(FIELDS),receipts,limit=6)
    if len(rows) != len(FIELDS) or {r[0] for r in rows} != set(FIELDS):
        raise RuntimeError('Normalised Zetaris tables are incomplete; result withheld.')
    for table, count, unique in rows:
        if type(count) not in (int,float,str) or str(count) != str(manifest['tables'][table]['rows']) or str(unique) != str(count):
            raise RuntimeError('Normalised Zetaris row counts or unique keys differ; refresh registration.')
    meta = measured_query(api,f'SELECT schema_version, format_id, snapshot_month, cutoff, battles, catalogue_sha256, usage_sha256, showdown_version FROM {DATABASE}.source_metadata',
                          'historical_reference',['source_metadata'],receipts,limit=2)
    expected = [str(manifest['schema_version']), FORMAT, MONTH, str(CUTOFF), str(BATTLES),
                manifest['catalogue_sha256'],manifest['usage_sha256'],'0.11.11']
    if len(meta) != 1 or [str(v) for v in meta[0]] != expected:
        raise RuntimeError('Zetaris historical format, snapshot or source hashes differ; result withheld.')


def partner_sql(data, favourites, avoided, limit=POOL_SIZE):
    from team_builder import resolve_names
    names = resolve_names(favourites,data)
    avoid = resolve_names(avoided,data) if avoided else []
    if names != favourites or avoid != avoided:
        raise ValueError('Partner SQL requires canonical catalogue names; no SQL was sent.')
    if not 1 <= len(names) <= 6 or type(limit) is not int or not 5 <= limit <= POOL_SIZE:
        raise ValueError('Partner query requires one to six favourites and a bounded pool.')
    ids = ','.join(id_literal(data['species'][n]['id']) for n in names)
    excluded = ','.join(id_literal(data['species'][n]['id']) for n in sorted(set(names+avoid)))
    sql = f'''SELECT p.name, CAST(u.usage AS DOUBLE) AS usage_rate,
          COALESCE(SUM(CAST(t.association_weight AS DOUBLE)), 0) AS association_weight,
          CAST(p.set_count AS INT) AS set_count, COUNT(*) OVER() AS candidate_count
        FROM {DATABASE}.pokemon_facts p
        JOIN {DATABASE}.usage_snapshots u ON p.name = u.name AND {scope('u')}
        JOIN {DATABASE}.source_metadata m ON u.format_id = m.format_id AND u.snapshot_month = m.snapshot_month AND u.cutoff = m.cutoff
        JOIN (SELECT name, COUNT(*) AS choice_count FROM {DATABASE}.sourced_sets s WHERE {scope('s')} GROUP BY name) c
          ON p.name = c.name AND CAST(p.set_count AS INT) = c.choice_count
        LEFT JOIN {DATABASE}.teammate_relationships t ON t.partner = p.name AND t.favourite_id IN ({ids}) AND {scope('t')}
        WHERE CAST(p.eligible AS INT) = 1 AND CAST(p.set_count AS INT) > 0 AND p.species_id NOT IN ({excluded})
        GROUP BY p.name, u.usage, p.set_count
        ORDER BY association_weight DESC, usage_rate DESC, p.name ASC LIMIT {limit}'''
    return sql, names, avoid


def checked_partners(data, rows, favourites, avoided, limit=POOL_SIZE):
    eligible = {n for n,m in data['species'].items() if m['eligible_species'] and m['sets'] and n not in set(favourites+avoided)}
    if len(rows) != min(limit,len(eligible)):
        raise RuntimeError('Zetaris partner shortlist is incomplete; no local replacement was used.')
    result, seen = [], set()
    for row in rows:
        if not isinstance(row,(list,tuple)) or len(row) != 5:
            raise RuntimeError('Malformed Zetaris partner evidence; result withheld.')
        name, usage, weight, count, total = row
        if not isinstance(name,str) or name not in eligible or name in seen:
            raise RuntimeError('Unknown, excluded or duplicate Zetaris partner; result withheld.')
        seen.add(name)
        try:
            u,w = float(usage),float(weight)
            if isinstance(usage,bool) or isinstance(weight,bool) or not math.isfinite(u) or not math.isfinite(w) or u<0 or u>1 or w<0:
                raise ValueError()
            if str(count) != str(len(data['species'][name]['sets'])) or str(total) != str(len(eligible)): raise ValueError()
        except (ValueError,TypeError,OverflowError):
            raise RuntimeError('Invalid numeric Zetaris partner evidence; result withheld.') from None
        expected_weight = sum(data['species'][n]['teammate_weights'].get(name,0) for n in favourites)
        if not math.isclose(u,data['species'][name]['usage'],rel_tol=1e-10,abs_tol=1e-12) or not math.isclose(w,expected_weight,rel_tol=1e-10,abs_tol=1e-8):
            raise RuntimeError('Zetaris partner evidence differs from the pinned source; result withheld.')
        result.append({'species':name,'usage':u,'association':w,'set_options':int(count)})
    if result != sorted(result,key=lambda r:(-r['association'],-r['usage'],r['species'])):
        raise RuntimeError('Zetaris partner rows are not in the requested SQL order.')
    return result,len(eligible)


def retrieve_partners(data, favourites, avoided, env_file=None):
    sql,names,avoid = partner_sql(data,favourites,avoided)
    if set(names)&set(avoid): raise ValueError('A locked favourite cannot also be avoided.')
    api = Zetaris(env_file)
    receipts = data['evidence_lens']['receipts']
    try:
        verify_tables(api,receipts)
        rows = measured_query(api,sql,'partner_ranking',list(FIELDS),receipts,limit=POOL_SIZE+1)
        partners,total = checked_partners(data,rows,names,avoid)
        receipts[-1]['candidates_considered'] = total
        data['zetaris_partner_pool'] = [r['species'] for r in partners]
        data['evidence_lens'].update({'sql_ranking':True,'favourites':names,'partners':partners,'candidate_count':total})
        return partners
    finally: api.session.close()
