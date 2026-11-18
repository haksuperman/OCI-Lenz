"""Objective geometry gates and best-so-far AI revision selection."""
import copy
import json
import io
import math
import sys
import tempfile
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
import unittest
from unittest.mock import patch

from oci_lenz.architecture import make_scene,seed_plan,check_plan,apply_design
from oci_lenz.display import prepare_display
from oci_lenz.model import sample,graph
from oci_lenz.quality import assess,revision_decision
from oci_lenz.visual_review import review_design


class LayoutQualityTests(unittest.TestCase):
    def setUp(self):
        self.snapshot=prepare_display(sample())
        self.scene=make_scene(self.snapshot,view='overview')
        self.plan={'version':3,'overview':seed_plan(self.scene)}

    def inflate(self,plan,amount):
        result=copy.deepcopy(plan)
        next(p for p in result['overview']['placements'] if p['id']==self.scene['region'])['width']+=amount
        return result

    def test_assessment_is_repeatable_alias_only_and_does_not_change_geometry_or_graph(self):
        before=copy.deepcopy((self.snapshot,self.plan,graph(self.snapshot)))
        one=assess(self.snapshot,self.plan);two=assess(self.snapshot,self.plan)
        self.assertEqual(one,two)
        self.assertEqual((self.snapshot,self.plan,graph(self.snapshot)),before)
        self.assertEqual(one['metrics']['resource_intersections'],0)
        self.assertEqual(one['metrics']['title_intersections'],0)
        self.assertEqual(one['metrics']['nonorthogonal_segments'],0)
        encoded=json.dumps(one)
        for value in ('10.0.1.10','Compute','layout-region','compute'):
            self.assertNotIn(value,encoded)

    def test_empty_area_is_penalized_and_equal_or_worse_revisions_are_rejected(self):
        initial=assess(self.snapshot,self.plan)
        inflated=assess(self.snapshot,self.inflate(self.plan,500))
        self.assertGreater(inflated['loss'],initial['loss'])
        self.assertFalse(revision_decision(initial,initial)['accepted'])
        self.assertFalse(revision_decision(initial,inflated)['accepted'])
        self.assertTrue(revision_decision(inflated,initial)['accepted'])

    def test_crossings_and_intrusions_cannot_be_traded_for_compactness(self):
        initial=assess(self.snapshot,self.plan)
        for field in ('edge_crossings','edge_overlap_length','resource_intersections','title_intersections','nonorthogonal_segments'):
            worse=copy.deepcopy(initial);worse['metrics'][field]+=1;worse['loss']=0
            with self.subTest(field=field):self.assertFalse(revision_decision(initial,worse)['accepted'])

    def test_crossing_repair_cannot_expand_canvas_without_limit(self):
        initial=assess(self.snapshot,self.plan);candidate=copy.deepcopy(initial)
        candidate['loss']=initial['loss']/2
        candidate['metrics']['canvas_area']*=2
        self.assertEqual(revision_decision(initial,candidate)['reason'],'canvas_growth')

    def test_invalid_geometry_is_not_scored_as_a_good_candidate(self):
        bad=copy.deepcopy(self.plan);bad['overview']['placements'].pop()
        with self.assertRaises(ValueError):assess(self.snapshot,bad)

    def test_reports_from_different_inventories_cannot_be_compared(self):
        initial=assess(self.snapshot,self.plan);candidate=copy.deepcopy(initial)
        candidate['scene_signature']='different';candidate['loss']=0
        self.assertEqual(revision_decision(initial,candidate)['reason'],'different_inventory')

    def test_subpixel_anchor_noise_does_not_create_false_diagonal_intrusions(self):
        paths=[{'source':'lb','target':'compute','network':False,
                'points':[(0,0),(100+1e-12,1e-12)]}]
        with patch('oci_lenz.quality.native_paths',return_value=paths):report=assess(self.snapshot,self.plan)
        self.assertEqual(report['metrics']['nonorthogonal_segments'],0)
        self.assertEqual(report['metrics']['resource_intersections'],0)
        self.assertEqual(report['metrics']['title_intersections'],0)

    def test_code_detects_non_network_crossing_and_reports_only_aliases(self):
        # Native path extraction is independent of resource/service type.
        paths=[{'source':'compute','target':'lb','network':False,'points':[(0,50),(100,50)]},
               {'source':'app-nsg','target':'private','network':False,'points':[(50,0),(50,100)]}]
        with patch('oci_lenz.quality.native_paths',return_value=paths):report=assess(self.snapshot,self.plan)
        self.assertEqual(report['metrics']['edge_crossings'],1)
        self.assertIn('edge_crossings',report['issues'])
        self.assertNotIn('compute',json.dumps(report))

    def test_native_invalid_labels_are_rejected_even_if_model_geometry_is_valid(self):
        import xml.etree.ElementTree as E
        doc=E.fromstring(apply_design(self.snapshot,self.plan))
        cell=doc.find("diagram/mxGraphModel/root/mxCell[@id='compute']")
        cell.set('style',cell.get('style')+'spacingTop=5000;')
        with self.assertRaises(ValueError):assess(self.snapshot,self.plan,xml=E.tostring(doc,encoding='unicode'))

    def test_quality_handles_empty_dense_and_projected_resources_without_graph_changes(self):
        for case in ('empty','dense','base-database','fastconnect'):
            with self.subTest(case=case):
                snapshot=prepare_display(sample(case));before=copy.deepcopy(graph(snapshot))
                report=assess(snapshot)
                self.assertTrue(math.isfinite(report['loss']))
                self.assertEqual(report['metrics']['resource_intersections'],0)
                self.assertEqual(report['metrics']['title_intersections'],0)
                self.assertEqual(graph(snapshot),before)

    def test_review_keeps_original_when_ai_proposes_larger_worse_layout(self):
        revision=self.inflate(self.plan,500)['overview']
        response={'acceptable':False,'issues':['excessive_whitespace'],'revision':revision}
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=response):
            result,report=review_design(self.snapshot,self.plan,[],rounds=1)
        self.assertEqual(result,self.plan)
        self.assertFalse(report['decisions'][0]['accepted'])
        self.assertEqual(report['quality']['initial'],report['quality']['final'])

    def test_better_revision_is_kept_and_focus_feedback_is_alias_only(self):
        original=self.inflate(self.plan,500)
        responses=[{'acceptable':False,'issues':['excessive_whitespace'],'revision':self.plan['overview']},
                   {'acceptable':True,'issues':[],'revision':None}]
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',side_effect=responses) as request:
            result,report=review_design(self.snapshot,original,[],rounds=1)
        self.assertEqual(result,self.plan)
        self.assertTrue(report['decisions'][0]['accepted'])
        self.assertLess(report['quality']['final']['loss'],report['quality']['initial']['loss'])
        self.assertIn('Objective quality',request.call_args.args[0])
        self.assertNotIn('10.0.1.10',request.call_args.args[0])
        self.assertNotIn('Compute',request.call_args.args[0])

    def test_ai_acceptance_does_not_override_remaining_objective_issues(self):
        quality=assess(self.snapshot,self.plan)
        quality['issues']=['edge_crossings'];quality['status']='needs_review'
        response={'acceptable':True,'issues':[],'revision':None}
        with patch('oci_lenz.visual_review.assess',return_value=quality),patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=response):
            _,report=review_design(self.snapshot,self.plan,[],rounds=1)
        self.assertEqual(report['status'],'needs_review')
        self.assertEqual(report['reason'],'objective_issues')

    def test_cli_writes_the_retained_plan_and_matching_final_metrics(self):
        from oci_lenz.cli import main
        response={'acceptable':False,'issues':['excessive_whitespace'],
                  'revision':self.inflate(self.plan,500)['overview']}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'snapshot.json';source.write_text(json.dumps(sample()))
            out=root/'out'
            argv=['oci-lenz','draw','--snapshot',str(source),'--output',str(out)]
            with patch.object(sys,'argv',argv),patch('oci_lenz.cli.skill_layout',return_value=self.plan),patch('oci_lenz.cli.export'),patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=response),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                main()
            self.assertEqual(json.loads((out/'skill-layout.json').read_text()),self.plan)
            self.assertEqual((out/'architecture.drawio').read_text(),apply_design(self.snapshot,self.plan))
            review=json.loads((out/'visual-review.json').read_text())
            validation=json.loads((out/'validation.json').read_text())
            self.assertFalse(review['decisions'][0]['accepted'])
            self.assertEqual(review['quality']['final'],validation['layout_quality'])
