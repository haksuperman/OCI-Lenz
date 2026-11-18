import copy
import json
import io
import sys
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,apply_design
from oci_lenz.draw import validate
from oci_lenz.typography import wrap_text,card_metrics
from oci_lenz.visual_review import review_design,masked_preview,export_preview
from oci_lenz.cli import main


class PresentationReviewTests(unittest.TestCase):
    def test_native_label_overflow_is_rejected(self):
        s=prepare_display(sample());doc=E.fromstring(apply_design(s))
        cell=doc.find("diagram/mxGraphModel/root/mxCell[@id='compute']")
        cell.set('style',cell.get('style')+'spacingTop=5000;')
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)

    def test_redundant_ownership_edge_labels_are_hidden_but_evidence_remains(self):
        s=prepare_display(sample());doc=E.fromstring(apply_design(s))
        edges=graph(s)[1]
        ownership_index=next(i for i,e in enumerate(edges) if e['kind']=='lb_id')
        cell=doc.find("diagram/mxGraphModel/root/mxCell[@id='edge-"+str(ownership_index)+"']")
        self.assertEqual(cell.get('value'),'Backend set')
        self.assertIn('textOpacity=0',cell.get('style'))

    def test_cli_runs_visual_review_for_fresh_ai_but_not_replay(self):
        s=sample();scene=make_scene(prepare_display(s),view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json';snapshot.write_text(json.dumps(s))
            saved=root/'plan.json';saved.write_text(json.dumps(plan))
            for replay in (False,True):
                out=root/('replay' if replay else 'fresh')
                args=['oci-lenz','draw','--snapshot',str(snapshot),'--output',str(out)]
                if replay:args+=['--reuse-layout',str(saved)]
                with patch.object(sys,'argv',args),patch('oci_lenz.cli.skill_layout',return_value=plan),patch('oci_lenz.cli.export'),patch('oci_lenz.visual_review.review_design',return_value=(plan,{'status':'accepted','reviews':[]})) as review,redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):main()
                self.assertEqual(review.call_count,0 if replay else 1)
    def test_default_never_infers_service_groups_from_names_or_connections(self):
        s=sample('service-map');s.pop('presentation',None)
        for r in s['resources']:
            r['name']='shared-production-payments-'+r['kind']
        s=prepare_display(s);before=copy.deepcopy(graph(s))
        scene=make_scene(s,view='overview')
        self.assertFalse(any(v['kind']=='service_group' for v in scene['items'].values()))
        xml=apply_design(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertFalse(any(k.startswith('layout-service-') for k in cells))
        for r in s['resources']:
            if r['kind']=='vcn':
                self.assertTrue(cells[r['id']].get('parent').startswith('layout-compartment-'))
        self.assertEqual(graph(s),before)

    def test_explicit_service_groups_apply_without_changing_evidence(self):
        s=prepare_display(sample('service-map'));edges=graph(s)[1]
        scene=make_scene(s,view='overview')
        self.assertTrue(any(v['kind']=='service_group' for v in scene['items'].values()))
        self.assertNotIn('Service A',str(scene['request']))
        xml=apply_design(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(cells['s1-vcn'].get('parent'),cells['s2-vcn'].get('parent'))
        self.assertEqual(graph(s)[1],edges)
        self.assertFalse(any(k.startswith('layout-compartment-') for k in cells))

    def test_service_group_index_retains_physical_compartment_privately(self):
        s=prepare_display(sample('service-map'))
        xml=apply_design(s)
        self.assertTrue('Compartment: synthetic-compartment-1' in xml,'physical compartment missing from private information index')
        safe=prepare_display(sample('service-map'),redact=True)
        self.assertNotIn('Compartment: synthetic-compartment-1',apply_design(safe))

    def test_review_rejects_png_metadata_before_upload(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        with tempfile.TemporaryDirectory() as tmp:
            png=Path(tmp)/'metadata.png';png.write_bytes(b'\x89PNG\r\n\x1a\n'+(4).to_bytes(4,'big')+b'tEXt'+b'test'+b'\0'*4)
            with patch('oci_lenz.visual_review.export',return_value=[png]):
                with self.assertRaises(ValueError):export_preview(s,plan,scene,tmp)

    def test_unicode_and_long_labels_get_measured_native_resource_text(self):
        s=sample();r=next(r for r in s['resources'] if r['kind']=='compute')
        r['name']='운영 웹 애플리케이션 & <데이터> 서버 이름이 아주 긴 가상 예시'
        s=prepare_display(s);xml=apply_design(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        import html
        label=cells['compute'].get('value')
        self.assertIn('<b>',label)
        self.assertIn('<데이터>',html.unescape(label).replace('<br>',''))
        self.assertIn('font-size:10px',label)
        metrics=card_metrics(next(r for r in s['resources'] if r['kind']=='compute'),170)
        self.assertGreater(metrics['height'],110)
        self.assertEqual(wrap_text('가나다라마바사아자차카타파하',60,12).replace('\n',''),'가나다라마바사아자차카타파하')

    def test_preview_removes_real_names_ips_group_names_and_other_pages(self):
        s=prepare_display(sample('service-map'))
        scene=make_scene(s,view='overview');plan={'version':3,'overview':seed_plan(scene)}
        xml=apply_design(s,plan)
        preview=masked_preview(xml,s,scene)
        for text in ('s1-Compute','10.0.1.10','Service A'):self.assertNotIn(text,preview)
        self.assertEqual(len(E.fromstring(preview).findall('diagram')),1)

    def test_visual_review_accepts_or_records_unresolved_quality(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        with tempfile.TemporaryDirectory() as tmp,patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value={'acceptable':True,'issues':[],'revision':None}):
            result,report=review_design(s,plan,[],rounds=1)
        self.assertEqual(result,plan);self.assertEqual(report['status'],'needs_review')
        self.assertIn('flow_alignment_error',report['quality']['final']['issues'])
        rejected={'acceptable':False,'issues':['excessive_whitespace'],'revision':None}
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=rejected):
            _,report=review_design(s,plan,[],rounds=0)
        self.assertEqual(report['status'],'skipped')

    def test_review_cannot_pass_with_remaining_issues(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        response={'acceptable':True,'issues':['unreadable_labels'],'revision':None}
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=response):
            _,report=review_design(s,plan,[],rounds=1)
        self.assertEqual(report['status'],'needs_review')

    def test_review_revision_cannot_invent_or_drop_resources(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        plan={'version':3,'overview':seed_plan(scene)};bad=copy.deepcopy(plan['overview']);bad['placements'].pop()
        response={'acceptable':False,'issues':['poor_grouping'],'revision':bad}
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')),patch('oci_lenz.visual_review.request_json',return_value=response):
            result,report=review_design(s,plan,[],rounds=1)
        self.assertEqual(result,plan);self.assertEqual(report['status'],'needs_review')

    def test_valid_revision_is_rendered_and_reviewed_again(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        revision=seed_plan(scene)
        plan={'version':3,'overview':copy.deepcopy(revision)}
        root=next(p for p in plan['overview']['placements'] if p['id']==scene['region']);root['width']+=100
        responses=[{'acceptable':False,'issues':['inconsistent_spacing'],'revision':revision},
                   {'acceptable':True,'issues':[],'revision':None}]
        with patch('oci_lenz.visual_review.export_preview',return_value=Path('/tmp/synthetic.png')) as preview,patch('oci_lenz.visual_review.request_json',side_effect=responses) as request:
            result,report=review_design(s,plan,[],rounds=1)
        self.assertEqual(request.call_count,2);self.assertEqual(preview.call_count,2)
        self.assertEqual(report['status'],'needs_review')
        self.assertTrue(report['decisions'][0]['accepted'])
        self.assertIn('flow_alignment_error',report['quality']['final']['issues'])
        self.assertEqual(result['overview']['placements'],revision['placements'])

    def test_cli_groups_file_controls_service_labels(self):
        s=sample('overview')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json';snapshot.write_text(json.dumps(s))
            groups=root/'groups.json';groups.write_text(json.dumps({'groups':[{'label':'Synthetic service','vcn_ids':['demo-1-vcn','demo-2-vcn']}]}))
            args=['oci-lenz','draw','--snapshot',str(snapshot),'--groups',str(groups),'--output',str(root/'out'),'--no-ai','--no-png']
            with patch.object(sys,'argv',args),redirect_stdout(io.StringIO()):main()
            doc=E.parse(root/'out/architecture.drawio').getroot()
            self.assertEqual(doc.find("diagram/mxGraphModel/root/mxCell[@id='layout-service-0']").get('value'),'Synthetic service')
