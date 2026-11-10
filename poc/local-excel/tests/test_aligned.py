"""Contract invariants for the approved instruction-only experiment."""
from copy import deepcopy
from pathlib import Path
import unittest
import aligned
import poc


class AlignedContractTests(unittest.TestCase):
    def test_only_approved_instruction_changes_without_mutating_baseline(self):
        base = poc.config(poc.MODEL)
        untouched = deepcopy(base)
        result = aligned.configuration(base)
        self.assertEqual(base, untouched)
        self.assertNotEqual(result['agent']['excel']['prompt'], base['agent']['excel']['prompt'])
        result['agent']['excel']['prompt'] = base['agent']['excel']['prompt']
        self.assertEqual(result, base)

    def test_sampler_or_permission_changes_are_rejected(self):
        for change in ('sampler', 'permission'):
            with self.subTest(change=change):
                value = aligned.configuration(poc.config(poc.MODEL))
                if change == 'sampler':
                    value['agent']['excel']['temperature'] = 0
                else:
                    value['permission']['*'] = 'allow'
                with self.assertRaisesRegex(ValueError, 'only the approved'):
                    aligned.validate(value)

    def test_model_context_and_local_route_cannot_be_changed(self):
        for change in ('model', 'context', 'route'):
            with self.subTest(change=change):
                value = aligned.configuration(poc.config(poc.MODEL))
                if change == 'model':
                    value['small_model'] = 'other/model'
                elif change == 'context':
                    value['provider']['ollama']['models'][poc.MODEL]['limit']['context'] = 4096
                else:
                    value['provider']['ollama']['options']['baseURL'] = 'https://example.invalid/v1'
                with self.assertRaises(ValueError):
                    aligned.validate(value)

    def test_prompt_restores_original_ranking_type_and_workspace_output(self):
        folder = Path('/private/tmp/example/workspace/銷售 資料')
        for negative in (False, True):
            text = aligned.prompt(folder, negative)
            self.assertIn('region_ranking（依金額遞減的區域名稱陣列）', text)
            self.assertIn('/private/tmp/example/workspace/answer.json（本次 workspace 內）', text)
            self.assertIn('stdout 僅印一個錯誤 JSON', text)
