from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
import aligned
import poc
import thinking


class ThinkingContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name); (self.run/'workspace').mkdir(); (self.run/'evidence').mkdir()
        poc.write_json(self.run/'workspace/opencode.json', thinking.configuration(poc.config(poc.MODEL)))
        self.result = {'marker':thinking.MARKER,'python':str(self.run/'workspace/.venv/bin/python'),'prefix':str(self.run/'workspace/.venv')}
        self.final = thinking.PROBE_LEAD+'\n```json\n'+json.dumps(self.result)+'\n```'
        self.tool = {'tool':'bash','state':{'status':'completed','input':{'command':'uv run --locked --offline python runtime_probe.py'},'metadata':{'exit':0},'output':json.dumps(self.result)}}

    def traces(self, enabled=True):
        poc.write_json(self.run/'evidence/session-export.json',{'messages':[{'info':{'role':'assistant'},'parts':[{'type':'reasoning','text':'synthetic probe thought'}] if enabled else []}]})

    def test_only_effort_changes_relative_to_approved_aligned(self):
        base=aligned.configuration(poc.config(poc.MODEL));old=deepcopy(base);result=thinking.configuration(base)
        self.assertEqual(base,old)
        result['provider']['ollama']['models'][poc.MODEL]['options']['reasoningEffort']='none'
        self.assertEqual(result,base)

    def test_other_instruction_or_permission_or_effort_changes_rejected(self):
        for field in ['instruction','permission','effort']:
            with self.subTest(field=field):
                c=thinking.configuration(poc.config(poc.MODEL))
                if field=='instruction':c['agent']['excel']['prompt']='changed'
                elif field=='permission':c['permission']['*']='allow'
                else:c['provider']['ollama']['models'][poc.MODEL]['options']['reasoningEffort']='high'
                with self.assertRaises(ValueError):thinking.validate(c)

    def test_real_probe_with_reasoning_and_matching_final(self):
        self.traces();self.assertEqual(thinking.review(self.run,{'probe':True},[self.tool],self.final),[])

    def test_configured_mode_without_actual_reasoning_is_not_enough(self):
        self.traces(False);self.assertTrue(thinking.review(self.run,{'probe':True},[self.tool],self.final))

    def test_final_json_without_real_python_or_with_wrong_prefix_rejected(self):
        self.traces();self.assertTrue(thinking.review(self.run,{'probe':True},[],self.final))
        changed=dict(self.result,prefix='/somewhere-else');final=thinking.PROBE_LEAD+'\n```json\n'+json.dumps(changed)+'\n```'
        self.assertTrue(thinking.review(self.run,{'probe':True},[self.tool],final))
