"""Regression guards for persisted GUI evidence; these are not GUI E2E tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
import ide
import poc
import workflow


class PersistedEvidenceTests(unittest.TestCase):
    def run_fixture(self, *, complete=True, provider='ollama', change_input=False, boundary_receipt=False, command='uv run --locked --offline python analysis.py', context=65536, workflow_field=None, workflow_value=None):
        with tempfile.TemporaryDirectory() as folder:
            run = poc.prepare(Path(folder))
            workspace = run / 'workspace'
            (workspace / 'context-probe.txt').write_text(ide.PROBE)
            (workspace / 'analysis.py').write_text('# generated script must still be inspected independently\n')
            poc.write_json(workspace / 'answer.json', poc.read_json(poc.ROOT / 'oracle.json'))
            manifest = poc.read_json(run / 'manifest.json')
            manifest.update(interface='official', binary='/test/opencode', context_probe_sha256=poc.sha256(workspace / 'context-probe.txt'))
            if workflow_field is not None:
                answer = poc.read_json(workspace / 'answer.json')
                answer[workflow_field] = workflow_value
                poc.write_json(workspace / 'answer.json', answer)
                poc.write_json(workspace / 'inspection.json', {
                    'path': str(workspace / '銷售 資料'), 'file': str(workspace / '銷售 資料/sales.xlsx'),
                    'sheet': 'Sales', 'headers': sorted(workflow.HEADERS),
                    'types': {'date':'datetime', 'region':'str', 'product':'str', 'quantity':'int', 'unit_price':'int'},
                    'region_values':['北','中','南'], 'product_values':['A','B']})
                manifest.update(protocol=workflow.VERSION, prompt_sha256=poc.sha256(workspace / 'prompt.txt'))
            poc.write_json(run / 'manifest.json', manifest)
            if boundary_receipt:
                (run / 'evidence').mkdir(exist_ok=True)
                manifest['isolation'] = {'kind': 'test-boundary'}
                poc.write_json(run / 'manifest.json', manifest)
                (run / 'evidence/extension-launch.jsonl').write_text(json.dumps({'cwd': '/wrong-session', 'isolation': manifest['isolation']})+'\n')
            if change_input:
                (workspace / 'uv.lock').write_text('changed')
            log = run / 'state/opencode/log/opencode.log'
            log.parent.mkdir(parents=True)
            log.write_text('\n'.join(f'message=stream providerID={provider} modelID={poc.MODEL} session.id=test small={size}' for size in ['true', 'false']))
            data = {'messages': [
                {'info': {'role': 'user'}, 'parts': [{'type': 'text', 'text': 'analyze synthetic Excel'}]},
                {'info': {'role': 'assistant', 'providerID': provider, 'modelID': poc.MODEL,
                          **({'finish': 'stop'} if complete else {})},
                 'parts': [{'type': 'text', 'text': '總額 12,000'},
                           {'type': 'tool', 'tool': 'bash', 'state': {'status': 'completed',
                            'input': {'command': command}, 'metadata': {'exit': 0}}}]}]}
            if workflow_field is not None:
                data['messages'][-1]['parts'][0]['text'] = workflow.NORMAL_LEAD+'\n```json\n'+json.dumps(answer)+'\n```'
            loaded = {'models': [{'name': poc.MODEL, 'digest': ide.DIGEST, 'context_length': context}]}
            with patch('ide.subprocess.run', return_value=CompletedProcess([], 0, json.dumps(data))), patch('poc.api', return_value=loaded), patch('ide.isolation.require', return_value={'kind': 'test-boundary'}):
                report = ide.capture(run, 'test')
                if workflow_field is not None:
                    self.assertEqual(poc.read_json(run / 'interface-review.json'), json.loads(json.dumps(report)))
                return report

    def test_malformed_workflow_groups_still_save_not_passed_report(self):
        for field in ('monthly_sales', 'regional_sales'):
            for value in (None, [], 'invalid', 1):
                with self.subTest(field=field, value=value):
                    report = self.run_fixture(workflow_field=field, workflow_value=value)
                    self.assertEqual(report['status'], 'not-passed')
                    self.assertFalse(report['e2e_passed'])
                    self.assertIn('workflow: missing or invalid inspection/answer evidence', report['errors'])

    def test_numeric_output_with_incomplete_conversation_is_rejected(self):
        report = self.run_fixture(complete=False)
        self.assertIn('final assistant response is incomplete', report['errors'])
        self.assertFalse(report['e2e_passed'])

    def test_unexpected_inference_route_is_rejected(self):
        report = self.run_fixture(provider='cloud')
        self.assertIn('unexpected assistant inference route', report['errors'])
        self.assertIn('main/small inference identities not both observed', report['errors'])

    def test_cat_with_valid_numbers_does_not_count_as_python_execution(self):
        report = self.run_fixture(command='cat analysis.py')
        self.assertIn('no successful generated Python execution', report['errors'])

    def test_receipt_from_a_different_session_is_rejected(self):
        report = self.run_fixture(boundary_receipt=True)
        self.assertIn('execution boundary receipt differs from prepared session', report['errors'])

    def test_different_loaded_context_does_not_pass_the_fixed_contract(self):
        report = self.run_fixture(context=131072)
        self.assertIn('loaded model digest/context not confirmed', report['errors'])

    def test_changed_lockfile_is_rejected(self):
        report = self.run_fixture(change_input=True)
        self.assertIn('protected input changed: uv.lock', report['errors'])

class ExecutionBoundaryTests(unittest.TestCase):
    def test_both_entrypoints_stop_before_any_process_or_run_access(self):
        # Even a stale, previously prepared run cannot bypass the current stop.
        with patch('ide.subprocess.Popen') as spawn, patch('ide.poc.read_json', return_value={}) as read:
            for entrypoint in (ide.launch, ide.start_server):
                with self.subTest(entrypoint=entrypoint.__name__):
                    with self.assertRaisesRegex(RuntimeError, 'E004-qualified isolation'):
                        entrypoint(Path('/nonexistent/stale-run'))
            spawn.assert_not_called()
            self.assertEqual(read.call_count, 2)


if __name__ == '__main__':
    unittest.main()
