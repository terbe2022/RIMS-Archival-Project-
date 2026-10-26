"""Synthetic boundary regressions. No models, network, or accession data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from workbench import relevance, stage04, vision


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdentitySensitivity(unittest.TestCase):
    def rows(self):
        return [dict(file_uid=uid, accession_uid=acc, filename='same.jpg',
                     path_norm=path, path_raw='/source/' + acc + '/' + path)
                for uid, acc, path in [('a', 'A', 'one/same.jpg'),
                                       ('b', 'A', 'two/same.jpg'),
                                       ('c', 'B', 'one/same.jpg')]]

    def ingest(self, rows, **identity):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.jsonl'
            path.write_text(json.dumps(dict(identity, output={'title': 'Fictional image',
                'description': 'A synthetic test image.', 'readable': True})) + '\n')
            return vision.ingest_jsonl(rows, path)

    def test_uid_assigns_only_its_file(self):
        rows = self.rows()
        result = self.ingest(rows, file_uid='a', image_path='/old/layout/same.jpg')
        self.assertEqual(['a'], [r['file_uid'] for r in rows if r.get('dc_title')])
        self.assertEqual(1, result['matched'])

    def test_ambiguous_legacy_basename_is_rejected(self):
        rows = self.rows()
        result = self.ingest(rows, image_path='same.jpg')
        self.assertFalse(any(r.get('dc_title') for r in rows))
        self.assertEqual(1, result['identity_ambiguous'])

    def test_unknown_uid_does_not_fall_back(self):
        rows = self.rows()[:1]
        result = self.ingest(rows, file_uid='missing', image_path='same.jpg')
        self.assertFalse(rows[0].get('dc_title'))
        self.assertEqual(1, result['unmatched_in_jsonl'])

    def test_scoped_relative_path_and_windows_separators(self):
        rows = self.rows()
        self.ingest(rows, accession_uid='A', image_path='one\\same.jpg')
        self.assertEqual(['a'], [r['file_uid'] for r in rows if r.get('dc_title')])

    def test_full_source_path_disambiguates(self):
        rows = self.rows()
        self.ingest(rows, image_path='/source/A/two/same.jpg')
        self.assertEqual(['b'], [r['file_uid'] for r in rows if r.get('dc_title')])

    def test_wrong_full_path_does_not_fall_back_to_basename(self):
        rows = self.rows()[:1]
        self.ingest(rows, image_path='/wrong/same.jpg')
        self.assertFalse(rows[0].get('dc_title'))

    def test_unique_legacy_basename_still_supported(self):
        rows = self.rows()[:1]
        self.assertEqual(1, self.ingest(rows, image_path='same.jpg')['matched'])

    def test_uid_with_wrong_accession_is_rejected(self):
        rows = self.rows()
        self.ingest(rows, file_uid='a', accession_uid='B')
        self.assertFalse(any(r.get('dc_title') for r in rows))

    def test_folder_association_stays_in_full_path_and_accession(self):
        rows = [dict(file_uid=str(i), accession_uid=acc, path_norm=path,
                     parent_folder='reports', s02_file_score=score)
                for i, (acc, path, score) in enumerate([
                    ('A', 'one/reports/a', .9), ('A', 'one/reports/b', .8),
                    ('A', 'one/reports/c', 0), ('A', 'two/reports/d', 0),
                    ('B', 'one/reports/e', 0)])]
        relevance.score_folders(rows)
        self.assertTrue(rows[2].get('retained_by_association'))
        self.assertFalse(rows[3].get('retained_by_association'))
        self.assertFalse(rows[4].get('retained_by_association'))

    def test_missing_folder_identity_does_not_infer_association(self):
        rows = [dict(parent_folder='reports', s02_file_score=s) for s in [.9, .8, 0]]
        relevance.score_folders(rows)
        self.assertFalse(any(r.get('retained_by_association') for r in rows))

    def test_vision_evidence_survives_manifest_and_private_export(self):
        import pandas as pd
        import pyarrow.parquet as pq
        from schema import manifest
        parsed = vision.parse_output({'offensive': True, 'offense_category': 'hate symbols',
            'offense_evidence': 'Fictional symbol on the upper left banner',
            'offense_reason': 'Synthetic locating evidence', 'confidence': .8})
        row = dict(file_uid='a', accession_uid='A', record_series='9999999',
                   path_raw='synthetic.jpg', path_norm='synthetic.jpg',
                   **vision.to_manifest(parsed))
        evidence = json.loads(row['s04_sensitivity_scores_json'])
        self.assertEqual(parsed['offense_evidence'], evidence['evidence'])
        exporter = script('export_review')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.parquet'
            pq.write_table(manifest.enforce(pd.DataFrame([row])), path)
            loaded = exporter.load(path)
        private = exporter.build(loaded, None, False)
        self.assertEqual(row['s04_sensitivity_scores_json'],
                         private['items'][0]['s04_sensitivity_scores_json'])
        public = exporter.build([row], None, True)
        self.assertNotIn('upper left banner', json.dumps(public))
        self.assertEqual([], exporter.audit(public))

    def test_pii_locations_survive_without_values(self):
        text = 'Fictional contact: 217-555-0100.'
        rows = [dict(file_uid='a', _text=text, layer=1)]
        with tempfile.TemporaryDirectory() as tmp:
            stage04.run(rows, {'accession_uid': 'synthetic'}, tmp, name_detector='heuristic')
        entities = json.loads(rows[0]['s04_pii_entities_json'])
        phone = next(e for e in entities if e['type'] == 'phone')
        self.assertEqual('217-555-0100', text[phone['start']:phone['end']])
        self.assertNotIn('value', phone)
        self.assertEqual('original_extracted_text', phone['coordinate_space'])

    def test_prototype_retains_all_categories_and_evidence(self):
        exporter = script('export_prototype')
        row = dict(file_uid='a', accession_uid='A', s03_lane='image',
                   s04_sensitivity_flags=list(vision.CATEGORIES),
                   s04_sensitivity_scores_json='{"evidence":"synthetic location"}')
        _, records = exporter.build([row], {}, {}, 100)
        self.assertEqual(list(vision.CATEGORIES), records[0]['sensitivityFlags'])
        self.assertEqual('synthetic location', records[0]['sensitivityEvidence']['evidence'])

    def test_malformed_private_evidence_is_visible_not_a_crash(self):
        exporter = script('export_prototype')
        _, records = exporter.build([dict(file_uid='a', accession_uid='A',
            s04_sensitivity_flags=['other sensitive categories'],
            s04_sensitivity_scores_json='synthetic broken JSON')], {}, {}, 100)
        self.assertIn('error', records[0]['sensitivityEvidence'])
        self.assertEqual(['other sensitive categories'], records[0]['sensitivityFlags'])

    def test_workbench_private_evidence_survives_public_evidence_does_not(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'manifest.parquet'
            pq.write_table(pa.Table.from_pylist([dict(file_uid='a', accession_uid='A',
                s04_sensitivity_flags=['hate symbols'],
                s04_sensitivity_scores_json='{"evidence":"synthetic private location"}',
                s04_pii_entities_json='[]')]), path)
            for public in [False, True]:
                out = root / str(public)
                args = [sys.executable, '-B', str(ROOT/'scripts/export_workbench.py'),
                        str(path), '--intake', str(root/'empty'), '--out', str(out)]
                if public:
                    args.append('--public')
                proc = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(0, proc.returncode, proc.stderr)
                payload = json.loads((out/'workbench-data.json').read_text())
                self.assertEqual(not public, 'synthetic private location' in json.dumps(payload))

    def test_pages_release_and_bulk_hold_all_sensitivity_categories(self):
        js = r'''
const fs=require('fs'),assert=require('assert');
const s=fs.readFileSync('docs/app.html','utf8');
const names=['held','destination','releaseRecords','bulkDecide'];
function take(name,source=s){const start=source.indexOf('function '+name+'(');let i=source.indexOf('{',start),depth=1,j=i+1;for(;depth;j++){if(source[j]==='{')depth++;if(source[j]==='}')depth--;}return (source.slice(start-6,start)==='async '?'async ':'')+source.slice(start,j);}
const ctx={records:[],sel:new Set(),view:'test'};
let changed=0;const body=names.map(name=>take(name)).join('\n');
const run=new Function('S','recordDecision','render','toast',body+';return {held,releaseRecords,bulkDecide};');
const api=run(ctx,async()=>{changed++;return true;},()=>{},()=>{});
(async()=>{for(const category of JSON.parse(process.argv[1])){
 const r={id:'synthetic',dispo:'selected',flags:[category],entities:[]};
 assert(api.held(r),category);ctx.records=[r];assert.equal(api.releaseRecords().length,0);
 await api.bulkDecide([r],'selected');assert.equal(changed,0);
}
assert(api.held({flags:[],sensitivityFlags:['future category']}));
assert(api.held({flags:['unrecognised:new category']}));
assert(!api.held({flags:['kept by association','not read'],entities:[]}));
ctx.records=[{id:'clean',dispo:'selected',flags:[],entities:[],keywords:[]}];
assert.equal(api.releaseRecords('original').length,1);
const legacy=fs.readFileSync('web/accession-workbench.html','utf8');
const isHeld=new Function(take('isHeld',legacy)+';return isHeld;')();
for(const category of JSON.parse(process.argv[1]))assert(isHeld({flags:[category]}),category);
let exported;const exportData=new Function('S','dl','Box','isHeld',take('exportDataset',legacy)+';return exportDataset;');
const runExport=exportData({records:[{dispo:'selected',flags:['hate symbols']}],jobs:[]},(name,data)=>{exported=JSON.parse(data);},{},isHeld);
runExport();assert.equal(exported.records.length,0);
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        result = subprocess.run(['node', '-e', js, json.dumps(list(vision.CATEGORIES))],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
