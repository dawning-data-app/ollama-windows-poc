"""Evaluator regressions: these synthetic messages never reach the tested model."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ide
import workflow


class WorkflowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name)
        (self.run/'workspace').mkdir()
        self.target = str(self.run/'workspace/銷售 資料')
        self.inspection = {'path':self.target, 'file':str(Path(self.target) / 'sales.xlsx'), 'sheet':'Sales',
            'headers':['date','region','product','quantity','unit_price'],
            'types':{'date':'datetime','region':'str','product':'str','quantity':'int','unit_price':'int'},
            'region_values':['East','West'], 'product_values':['a','b']}
        self.answer = {'total_sales':10,'monthly_sales':{'2025-01':10},
                       'regional_sales':{'East':4,'West':6},'region_ranking':['West','East']}
        for name,value in [('inspection.json',self.inspection),('answer.json',self.answer)]:
            (self.run/'workspace'/name).write_text(json.dumps(value))
        self.tools = [self.tool('explore_excel.py',self.inspection),self.tool('analysis.py',self.answer)]

    def tool(self, name, value, exit=0):
        return {'tool':'bash','state':{'status':'completed','metadata':{'exit':exit},
            'input':{'command':'uv run --locked --offline python '+name},'output':json.dumps(value)}}

    def final(self, value=None, negative=False):
        lead=workflow.ERROR_LEAD if negative else workflow.NORMAL_LEAD
        return lead+'\n```json\n'+json.dumps(self.answer if value is None else value)+'\n```'

    def review(self, tools=None, final=None, case='sales'):
        return workflow.review(self.run,{'case':case},self.tools if tools is None else tools,self.final() if final is None else final)

    def test_complete_inspection_analysis_stdout_and_final_agree(self):
        self.assertEqual(self.review(),[])

    def test_unknown_types_cannot_count_as_successful_exploration(self):
        self.inspection['types']['date']='Unknown'
        (self.run/'workspace/inspection.json').write_text(json.dumps(self.inspection))
        self.tools[0]=self.tool('explore_excel.py',self.inspection)
        self.assertTrue(any('reported types' in e for e in self.review()))

    def test_analysis_before_inspection_is_rejected(self):
        self.assertTrue(any('before analysis' in e for e in self.review(tools=list(reversed(self.tools)))))

    def test_region_values_cannot_be_replaced_with_products(self):
        changed=copy.deepcopy(self.answer);changed.update(regional_sales={'a':4,'b':6},region_ranking=['b','a'])
        (self.run/'workspace/answer.json').write_text(json.dumps(changed))
        self.assertTrue(any('regional groups' in e for e in self.review(tools=[self.tools[0],self.tool('analysis.py',changed)],final=self.final(changed))))

    def test_additional_narrative_number_is_rejected(self):
        self.assertTrue(self.review(final=self.final()+'\n額外月額為 999。'))

    def test_final_json_cannot_invent_an_extra_month(self):
        changed=copy.deepcopy(self.answer);changed['monthly_sales']['2025-02']=999
        self.assertTrue(any('differs from actual answer' in e for e in self.review(final=self.final(changed))))

    def test_printed_numbers_without_executing_analysis_do_not_pass(self):
        fake=self.tool('analysis.py',self.answer);fake['state']['input']['command']='cat analysis.py'
        self.assertTrue(self.review(tools=[self.tools[0],fake]))

    def test_exact_missing_path_and_python_exception_can_be_verified(self):
        err={'path':self.target,'error_type':'FileNotFoundError','error_message':'missing target'}
        self.assertEqual(self.review(tools=[self.tool('explore_excel.py',err,1)],final=self.final(err,True),case='missing'),[])

    def test_parent_workspace_cannot_substitute_for_missing_subdirectory(self):
        err={'path':str(self.run/'workspace'),'error_type':'FileNotFoundError','error_message':'wrong target'}
        self.assertTrue(any('exact failing input path' in e for e in self.review(tools=[self.tool('explore_excel.py',err,1)],final=self.final(err,True),case='missing')))

    def test_corrupt_claim_requires_actual_failing_python_output(self):
        err={'path':self.target+'/sales.xlsx','error_type':'BadZipFile','error_message':'File is not a zip file'}
        self.assertTrue(self.review(tools=[],final=self.final(err,True),case='corrupt'))

    def test_modified_prepared_prompt_cannot_launch_vscode(self):
        (self.run/'workspace/prompt.txt').write_text('modified')
        with patch('ide.isolation.require'),patch('ide.poc.read_json',return_value={'prompt_sha256':'not-the-current-hash'}),patch('ide.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'prompt changed'):
                ide.launch(self.run)
            spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main()
