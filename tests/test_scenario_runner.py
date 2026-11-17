import json
from pathlib import Path
import tempfile
import struct
import unittest
import zlib
from unittest.mock import patch

from scripts.validate_scenarios import run_matrix,inspect_png,verify_case
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render
from oci_lenz.architecture import make_scene,seed_plan


class ScenarioRunnerTests(unittest.TestCase):
    def test_ai_verification_requires_fresh_model_provenance(self):
        s=sample();display=prepare_display(s)
        plan={'version':3,'overview':seed_plan(make_scene(display,view='overview'))}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            (out/'architecture.drawio').write_text(render(display,plan,style='architecture'))
            (out/'skill-layout.json').write_text(json.dumps(plan))
            (out/'coverage.json').write_text(json.dumps(s['coverage']))
            (out/'visual-review.json').write_text(json.dumps({'status':'accepted'}))
            (out/'validation.json').write_text(json.dumps({'skill_invoked':False,'reused_layout':False}))
            with patch('scripts.validate_scenarios.inspect_png',return_value=[1,1]):
                with self.assertRaises(ValueError):verify_case(out,s,True)

    def test_png_checks_full_chunks_pixels_and_rejects_metadata(self):
        def chunk(kind,data):
            return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
        header=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))
        body=chunk(b'IDAT',zlib.compress(b'\0\xff\xff\xff\xff'))
        tail=chunk(b'IEND',b'')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'image.png'
            path.write_bytes(header+body+tail)
            self.assertEqual(inspect_png(path),[1,1])
            for bad in (header,header+body[:-1]+tail,header+chunk(b'tEXt',b'private')+body+tail,
                        header+chunk(b'IDAT',zlib.compress(b''))+tail):
                path.write_bytes(bad)
                with self.assertRaises(ValueError):inspect_png(path)

    def test_failure_is_recorded_and_remaining_cases_run_without_raw_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('scripts.validate_scenarios.subprocess.run',side_effect=RuntimeError('SECRET RAW RESPONSE')) as run:
                result=run_matrix(Path(tmp),['basic','fanout'],ai=True)
            report=json.loads((Path(tmp)/'matrix-report.json').read_text())
            self.assertEqual(result,1)
            self.assertEqual(run.call_count,2)
            self.assertEqual([r['status'] for r in report],['failed','failed'])
            self.assertNotIn('SECRET',json.dumps(report))

    def test_needs_review_is_not_an_ai_quality_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('scripts.validate_scenarios.subprocess.run'),patch('scripts.validate_scenarios.verify_case',return_value={'visual_review_status':'needs_review','artifact_hashes':{}}):
                self.assertEqual(run_matrix(Path(tmp),['basic'],ai=True),1)
            item=json.loads((Path(tmp)/'matrix-report.json').read_text())[0]
            self.assertEqual(item['status'],'needs_review')

    def test_diagnostic_pass_is_explicitly_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('scripts.validate_scenarios.subprocess.run') as run,patch('scripts.validate_scenarios.verify_case',return_value={'visual_review_status':'skipped','artifact_hashes':{}}):
                self.assertEqual(run_matrix(Path(tmp),['basic']),0)
            item=json.loads((Path(tmp)/'matrix-report.json').read_text())[0]
            self.assertEqual(item['status'],'diagnostic_pass')
            self.assertFalse(item['ai_invoked'])
            self.assertIn('--no-ai',run.call_args.args[0])

    def test_resume_rechecks_artifacts_and_does_not_consume_ai(self):
        with tempfile.TemporaryDirectory() as tmp:
            verification={'visual_review_status':'accepted','artifact_hashes':{'architecture.drawio':'hash'}}
            with patch('scripts.validate_scenarios.subprocess.run') as run,patch('scripts.validate_scenarios.verify_case',return_value=verification) as verify:
                self.assertEqual(run_matrix(Path(tmp),['basic'],ai=True),0)
                self.assertEqual(run_matrix(Path(tmp),['basic'],ai=True,resume=True),0)
            self.assertEqual(run.call_count,1)
            self.assertEqual(verify.call_count,2)
            self.assertTrue(json.loads((Path(tmp)/'matrix-report.json').read_text())[0]['resumed'])

    def test_modified_artifact_or_changed_mode_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            one={'visual_review_status':'accepted','artifact_hashes':{'architecture.png':'one'}}
            two={'visual_review_status':'accepted','artifact_hashes':{'architecture.png':'two'}}
            with patch('scripts.validate_scenarios.subprocess.run') as run,patch('scripts.validate_scenarios.verify_case',side_effect=[one,two,two]):
                run_matrix(Path(tmp),['basic'],ai=True)
                run_matrix(Path(tmp),['basic'],ai=True,resume=True)
            self.assertEqual(run.call_count,2)
            with patch('scripts.validate_scenarios.subprocess.run') as run,patch('scripts.validate_scenarios.verify_case',return_value={'visual_review_status':'skipped','artifact_hashes':{}}):
                run_matrix(Path(tmp),['basic'],resume=True)
            self.assertEqual(run.call_count,1)
