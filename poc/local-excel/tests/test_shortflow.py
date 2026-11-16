"""Short-protocol evidence checks; no model calls or supplied analyzer."""
import json
from pathlib import Path
import tempfile
import unittest
import shortflow
import workflow


class ShortEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.run=Path(self.tmp.name);(self.run/'workspace').mkdir()
        self.answer={'total_sales':10,'monthly_sales':{'2025-01':10},'regional_sales':{'East':4,'West':6},'region_ranking':['West','East']}
        (self.run/'workspace/answer.json').write_text(json.dumps(self.answer))
        self.headers='date region product quantity unit_price\ndatetime str str int int'

    def tool(self,name,out,exit=0):
        return {'tool':'bash','state':{'status':'completed','metadata':{'exit':exit},'input':{'command':'uv run --locked --offline python '+name},'output':out}}

    def final(self,payload,negative=False):
        return (workflow.ERROR_LEAD if negative else workflow.NORMAL_LEAD)+'\n```json\n'+json.dumps(payload)+'\n```'

    def test_real_header_stdout_then_analysis_without_inspection_json(self):
        tools=[self.tool('check_excel.py',self.headers),self.tool('analysis.py',json.dumps(self.answer))]
        self.assertEqual(shortflow.review(self.run,{'case':'sales'},tools,self.final(self.answer)),[])
        self.assertFalse((self.run/'workspace/inspection.json').exists())

    def test_printing_keywords_without_python_inspection_is_rejected(self):
        fake=self.tool('check_excel.py',self.headers);fake['state']['input']['command']='echo date region product quantity unit_price datetime str int'
        self.assertTrue(shortflow.review(self.run,{'case':'sales'},[fake,self.tool('analysis.py',json.dumps(self.answer))],self.final(self.answer)))

    def test_final_value_cannot_differ_from_actual_file(self):
        changed=dict(self.answer,total_sales=999)
        tools=[self.tool('check_excel.py',self.headers),self.tool('analysis.py',json.dumps(self.answer))]
        self.assertTrue(shortflow.review(self.run,{'case':'sales'},tools,self.final(changed)))

    def test_wrong_missing_path_is_rejected_even_when_tool_and_final_agree(self):
        error={'path':str(self.run/'workspace'),'error_type':'FileNotFoundError','error_message':'missing'}
        self.assertTrue(shortflow.review(self.run,{'case':'missing'},[self.tool('check_excel.py',json.dumps(error),1)],self.final(error,True)))

    def test_exact_corrupt_path_with_matching_real_error(self):
        error={'path':str(self.run/'workspace/銷售 資料/sales.xlsx'),'error_type':'BadZipFile','error_message':'File is not a zip file'}
        self.assertEqual(shortflow.review(self.run,{'case':'corrupt'},[self.tool('check_excel.py',json.dumps(error),1)],self.final(error,True)),[])
