import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.validate_repeatability import run_repetitions


class RepeatabilityTests(unittest.TestCase):
    def test_fresh_runs_keep_failures_and_measure_spread_without_reusing_layout(self):
        def matrix(output,cases,**kwargs):
            self.assertTrue(kwargs['ai']);self.assertNotIn('resume',kwargs)
            n=int(output.name.split('-')[-1]);output.mkdir(parents=True)
            row={'case':cases[0],'snapshot_hash':'same','status':'failed' if n==2 else 'accepted',
                 'elapsed_seconds':10*n,'resumed':False}
            if n!=2:row['layout_quality']={'loss':n,'metrics':{'edge_crossings':0,'canvas_area':n*100}}
            (output/'matrix-report.json').write_text(json.dumps([row]))
            return int(n==2)
        with tempfile.TemporaryDirectory() as tmp,patch('scripts.validate_repeatability.run_matrix',side_effect=matrix) as run:
            report=run_repetitions(Path(tmp),'basic',repeats=3)
            self.assertEqual(run.call_count,3)
            self.assertEqual(report['failed_runs'],1)
            self.assertEqual(report['quality_clear_runs'],2)
            self.assertTrue(report['same_snapshot'])
            self.assertEqual(report['spread']['canvas_area'],{'min':100,'max':300,'mean':200})

    def test_invalid_repetition_count_does_not_start_model(self):
        with patch('scripts.validate_repeatability.run_matrix') as run:
            with self.assertRaises(ValueError):run_repetitions(Path('/tmp/unused'),'basic',repeats=1)
            run.assert_not_called()
