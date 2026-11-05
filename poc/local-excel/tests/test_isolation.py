"""Real OS boundary regressions; never presented as extension GUI E2E."""
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest
import isolation
import poc

BINARY = Path('/private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode').resolve()


@unittest.skipUnless(platform.system() == 'Darwin' and BINARY.is_file(), 'requires qualified Mac runtime')
class MacBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        self.run = poc.prepare(self.root)
        subprocess.run(['uv', 'sync', '--locked', '--offline', '--python', '3.12.12'],
                       cwd=self.run / 'workspace', env=poc.setup_environment(),
                       capture_output=True, check=True, timeout=60)
        self.manifest = poc.read_json(self.run / 'manifest.json')
        self.manifest.update(binary=str(BINARY), isolation=isolation.prepare(self.run, str(BINARY)))
        poc.write_json(self.run / 'manifest.json', self.manifest)

    def test_inside_and_deny_sibling_oracle_symlink_and_child_listing(self):
        outside = self.root / 'outside-canary.txt'
        outside.write_text('NO_ANSWERS')
        oracle_hash = poc.sha256(poc.ROOT / 'oracle.json')
        (self.run / 'workspace/outside-link').symlink_to(outside)
        code = '''from pathlib import Path
import subprocess,sys
from openpyxl import load_workbook
p=Path('inside.txt');p.write_text('ok');assert p.read_text()=='ok'
w=load_workbook('銷售 資料/sales.xlsx',read_only=True);assert w.sheetnames==['Sales'];w.close()
# All forbidden paths, especially oracle, are tested READ ONLY.
for p in sys.argv[1:]:
 try:
  with open(p,'rb'):pass
 except PermissionError:pass
 else:raise AssertionError('forbidden read allowed: '+p)
# Write denial uses only this test-owned disposable canary, never oracle.
try:
 with open(sys.argv[1],'wb'):pass
except PermissionError:pass
else:raise AssertionError('outside canary write allowed')
for command in [['/bin/ls',str(Path.cwd().parent.parent)],['/usr/bin/find',str(Path.cwd().parent.parent),'-name','*.xlsx']]:
 p=subprocess.run(command,capture_output=True,text=True);assert p.returncode!=0 and not p.stdout
print('inside, XLSX, cross-path, symlink and inherited child boundary verified')
'''
        result = subprocess.run(isolation.command(self.run, ['uv', 'run', '--locked', '--offline',
                                'python', '-c', code, str(outside), str(poc.ROOT / 'oracle.json'), 'outside-link']),
                                cwd=self.run / 'workspace', env=isolation.environment(self.run),
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('inherited child boundary verified', result.stdout)
        self.assertEqual(outside.read_text(), 'NO_ANSWERS')
        self.assertEqual(poc.sha256(poc.ROOT / 'oracle.json'), oracle_hash)

    def test_tampered_policy_cannot_be_used_for_launch(self):
        (self.run / 'sandbox.sb').write_text('(version 1) (allow default)')
        with self.assertRaisesRegex(RuntimeError, 'E004-qualified isolation'):
            isolation.command(self.run, ['/usr/bin/true'])
