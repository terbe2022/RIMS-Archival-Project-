"""Offline regression checks; uses synthetic data and a stub caller only."""
import ast
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from workbench import evaluate as E, fixtures as F


class RecoveryTests(unittest.TestCase):
    def test_fixture_coverage_and_labels(self):
        corpus = F.build_corpus()
        self.assertEqual(54, len(corpus))
        cases = E.build_cases(corpus, n_real=len(corpus))
        self.assertEqual(54, len(cases))
        self.assertEqual(16, sum(c.expects_abstention for c in cases))
        self.assertEqual(corpus, F.build_corpus())

    def test_repeated_attempts_reach_grading_sheet(self):
        cases = [E.Case('fixture-0', text='Complete synthetic source.')]
        attempts = E.run_model('stub', lambda c: json.dumps({
            'title': 'Source', 'description': 'Supported description.', 'readable': True}),
            cases, repeats=2)
        sheet = E.grading_sheet({'stub': attempts}, cases)
        self.assertEqual(1, len(sheet[0]['candidates']))
        self.assertEqual(cases[0].text, sheet[0]['input_text'])

    def test_failed_parses_are_not_consistent(self):
        cases = [E.Case('a')]
        attempts = E.run_model('stub', lambda c: 'not JSON', cases, repeats=2)
        self.assertEqual(0, E.score(attempts, cases)['consistency']['identical_across_repeats'])

    def test_description_changes_break_consistency(self):
        cases = [E.Case('a')]
        attempts = [E.Attempt('stub', 'a#0', parsed={'title': 'Same', 'description': 'One'}),
                    E.Attempt('stub', 'a#1', parsed={'title': 'Same', 'description': 'Two'})]
        self.assertEqual(0, E.score(attempts, cases)['consistency']['identical_across_repeats'])

    def test_explicit_abstention_and_required_types(self):
        self.assertTrue(E.abstained({'readable': False}))
        self.assertFalse(E.abstained({'description': 'The report discusses unclear results.'}))
        self.assertFalse(E.Attempt('stub', 'a', parsed={'title': 12, 'description': []}).has_required)
        self.assertFalse(E.abstained({}))

    def test_empty_metrics_are_not_zero(self):
        score = E.score([], [])
        self.assertIn('NA', E.comparison_table([score]))
        self.assertIsNone(score['schema']['parsed'])

    def test_unknown_cases_are_rejected(self):
        with self.assertRaises(ValueError):
            E.score([E.Attempt('stub', 'unknown')], [E.Case('known')])

    def test_notebook_sources_and_outputs(self):
        # Govern exactly the two recovered notebooks, not legacy POC notebooks.
        for name in ('model-evaluation.ipynb', 'colab-model-evaluation.ipynb'):
            path = ROOT / 'notebooks' / name
            self.assertTrue(path.is_file(), f'Missing recovered notebook: {name}')
            notebook = json.loads(path.read_text(encoding='utf-8'))
            for cell in notebook['cells']:
                if cell['cell_type'] != 'code':
                    continue
                self.assertEqual([], cell['outputs'])
                self.assertIsNone(cell['execution_count'])
                source = ''.join(cell['source'])
                # IPython shell escapes are not Python grammar. Check the other
                # lines without executing installations or downloads.
                source = '\n'.join(line for line in source.splitlines()
                                   if not line.lstrip().startswith(('!', '%')))
                ast.parse(source)


if __name__ == '__main__':
    unittest.main()
