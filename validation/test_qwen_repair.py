"""Qwen notebook regressions: no model downloads or inference services."""
import contextlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from workbench import evaluate as E


class QwenRepairTests(unittest.TestCase):
    def test_mapping_inputs_and_attention_mask_are_passed_to_generate(self):
        class Tensor:
            shape = (1, 3)
            def to(self, device):
                self.device = device
                return self
        inputs = {'input_ids': Tensor(), 'attention_mask': Tensor()}
        class Tokenizer:
            eos_token_id = 9
            def apply_chat_template(self, messages, **kwargs):
                self.kwargs = kwargs
                return inputs  # deliberately has no .shape or .to
            def decode(self, ids, **kwargs):
                self.decoded = ids
                return 'answer'
        class Model:
            device = 'test-device'
            def generate(self, **kwargs):
                self.kwargs = kwargs
                return [[1, 2, 3, 4, 5]]
        tok, model = Tokenizer(), Model()
        with patch.dict(sys.modules, {'torch': types.SimpleNamespace(no_grad=contextlib.nullcontext)}):
            self.assertEqual('answer', E.make_hf_caller(model, tok, '%s')(E.Case('a', text='fiction')))
        self.assertTrue(tok.kwargs['return_dict'])
        self.assertIs(inputs['attention_mask'], model.kwargs['attention_mask'])
        self.assertEqual([4, 5], tok.decoded)
        self.assertEqual('test-device', inputs['input_ids'].device)

    def test_subjects_string_is_recorded_without_coercion(self):
        obj = {'title': 'Report', 'description': 'Fictional report.', 'readable': True,
               'subjects': 'river, sampling', 'genre': 'report'}
        self.assertIn('subjects must be a list of strings', E.description_schema_errors(obj))
        self.assertIsInstance(obj['subjects'], str)
        attempts = E.run_model('stub', lambda c: json.dumps(obj), [E.Case('a')])
        score = E.score(attempts, [E.Case('a')])
        self.assertEqual(100, score['schema']['parsed'])
        self.assertEqual(0, score['schema']['description_contract_valid'])

    def test_correct_null_title_abstention_is_valid(self):
        obj = {'title': None, 'description': 'Unreadable input.', 'readable': False,
               'subjects': [], 'genre': 'unknown'}
        self.assertEqual([], E.description_schema_errors(obj))
        obj['genre'] = []
        self.assertIn('genre must be an allowed value', E.description_schema_errors(obj))

    def test_checkpoint_preserves_completed_results_on_interrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'attempts.jsonl'
            def caller(case):
                if case.case_id == 'b':
                    raise KeyboardInterrupt()
                return '{"title":"A","description":"Fiction"}'
            with self.assertRaises(KeyboardInterrupt):
                E.run_model('stub', caller, [E.Case('a'), E.Case('b')], checkpoint=path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(['a'], [row['case_id'] for row in rows])
            with self.assertRaises(FileExistsError):
                E.run_model('stub', caller, [], checkpoint=path)

    def test_full_stub_has_108_saved_attempts_and_54_repeated_cases(self):
        from workbench import fixtures as F
        cases = E.build_cases(F.build_corpus(), n_real=54)
        def caller(case):
            return json.dumps({'title': None if case.expects_abstention else 'Fiction',
                'description': 'Synthetic stub only.', 'readable': not case.expects_abstention,
                'subjects': [], 'genre': 'unknown'})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'attempts.jsonl'
            attempts = E.run_model('stub', caller, cases, repeats=2, checkpoint=path)
            self.assertEqual(108, len(path.read_text().splitlines()))
        score = E.score(attempts, cases)
        self.assertEqual(108, score['calls'])
        self.assertEqual(54, score['consistency']['cases_repeated'])
        self.assertEqual(100, score['schema']['description_contract_valid'])


if __name__ == '__main__':
    unittest.main()
