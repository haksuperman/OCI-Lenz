"""A checkout must not borrow application modules from another editable install."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DependencyIsolationTests(unittest.TestCase):
    def test_all_loaded_application_modules_belong_to_this_checkout(self):
        root=Path(__file__).resolve().parents[1]
        code='''
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root))
from oci_lenz.cli import main
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.quality import assess
assess(prepare_display(sample()))
for name,module in tuple(sys.modules.items()):
    if name=='oci_lenz' or name.startswith('oci_lenz.'):
        path=getattr(module,'__file__',None)
        if path is not None:
            assert Path(path).resolve().is_relative_to(root/'oci_lenz'), 'application module escaped checkout: '+name
'''
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,'-I','-c',code,str(root)],cwd=tmp,
                                  capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
