import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace as N
import xml.etree.ElementTree as E
from oci_lenz.display import prepare_display
from oci_lenz.draw import validate
from oci_lenz.model import sample
from oci_lenz.architecture import make_scene,seed_plan,check_plan,apply_plan
from oci_lenz.ai import design,request_json


class ArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.s=prepare_display(sample())
        self.scene=make_scene(self.s)

    def test_coordinates_are_applied_without_grid_override(self):
        plan=seed_plan(self.scene)
        root=next(p for p in plan['placements'] if p['id']==self.scene['region'])
        root['width']+=400
        xml=apply_plan(self.s,self.scene,plan)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        self.assertEqual(float(cells['layout-region'].find('mxGeometry').get('width')),root['width'])
        self.assertIn('information-index',xml)

    def test_cached_plan_cannot_be_reused_for_different_resource_ids(self):
        plan=seed_plan(self.scene);plan['scene_signature']='another-scene'
        with self.assertRaises(ValueError):apply_plan(self.s,self.scene,plan)

    def test_many_compartments_retain_internal_vcn_geometry_in_detail_pages(self):
        for scenario in ('overview','service-map'):
            s=prepare_display(sample(scenario));scene=make_scene(s)
            xml=apply_plan(s,scene,seed_plan(scene))
            validate(xml,s)

    def test_detail_page_crop_keeps_unresolved_targets_inside_region(self):
        s=sample();s['resources']=[r for r in s['resources'] if r['id']!='nat']
        s=prepare_display(s);scene=make_scene(s)
        validate(apply_plan(s,scene,seed_plan(scene)),s)

    def test_many_secondary_ips_remain_complete_in_information_index(self):
        s=sample()
        addresses=['10.0.1.'+str(i) for i in range(10,50)]
        next(r for r in s['resources'] if r['kind']=='vnic')['private_ips']=addresses
        s=prepare_display(s);scene=make_scene(s)
        xml=apply_plan(s,scene,seed_plan(scene));validate(xml,s)
        doc=E.fromstring(xml)
        card=doc.find("diagram/mxGraphModel/root/mxCell[@id='compute']")
        self.assertLess(float(card.find('mxGeometry').get('height')),250)
        self.assertIn('information index',card.get('value'))
        information='\n'.join(c.get('value','') for c in doc.find("diagram[@id='information-index']").iter('mxCell'))
        self.assertTrue(all(address in information for address in addresses))

    def test_invalid_layout_requires_repair_and_never_silent_fallback(self):
        good=seed_plan(self.scene);bad=copy.deepcopy(good);bad['placements'].pop()
        with patch('oci_lenz.ai.request_json',side_effect=[bad,good]) as request:
            plan=design(self.scene,[],provider='codex')
        self.assertEqual(plan['placements'],good['placements'])
        self.assertEqual(request.call_count,2)
        self.assertIn('Repair',request.call_args.args[0])
        with patch('oci_lenz.ai.request_json',return_value=bad):
            with self.assertRaises(ValueError):design(self.scene,[],provider='codex')

    def test_missing_invented_and_overlapping_rectangles_rejected(self):
        plan=seed_plan(self.scene)
        self.assertEqual(check_plan(self.scene,plan),[])
        bad=copy.deepcopy(plan);bad['placements'][0]['id']='invented'
        self.assertTrue(check_plan(self.scene,bad))
        bad=copy.deepcopy(plan)
        cards=[p for p in bad['placements'] if self.scene['items'][p['id']]['kind']=='compute']
        cards[0]['width']=1
        self.assertTrue(check_plan(self.scene,bad))

    def test_model_request_is_alias_only_and_includes_reference(self):
        self.s['resources'][0]['name']='PRIVATE-NAME-SENTINEL'
        scene=make_scene(self.s)
        with patch('oci_lenz.ai.request_json',return_value=seed_plan(scene)) as request:
            design(scene,[Path('/tmp/synthetic-reference.png')],model='test-model')
        prompt=request.call_args.args[0]
        self.assertNotIn('PRIVATE-NAME-SENTINEL',prompt)
        self.assertNotIn('10.0.1.10',prompt)
        self.assertEqual(request.call_args.kwargs['model'],'test-model')
        self.assertEqual(len(request.call_args.args[2]),1)

    def test_codex_provider_applies_model_and_images(self):
        def run(cmd,**kw):
            self.assertIn('test-model',cmd)
            self.assertIn('-i',cmd)
            self.assertIn('read-only',cmd)
            Path(cmd[cmd.index('-o')+1]).write_text('{"placements":[],"routes":[]}')
            return N(returncode=0)
        with patch('oci_lenz.ai.subprocess.run',side_effect=run):
            self.assertEqual(request_json('task',{},[Path('/tmp/example.png')],model='test-model')['routes'],[])

    def test_api_provider_uses_runtime_key_and_disables_response_storage(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return json.dumps({'output':[{'content':[{'type':'output_text','text':'{"placements":[],"routes":[]}'}]}]}).encode()
        def open_request(req,**kw):
            body=json.loads(req.data)
            self.assertFalse(body['store'])
            self.assertEqual(body['model'],'test-model')
            self.assertNotIn('TEST-KEY-SENTINEL',req.data.decode())
            self.assertEqual(req.get_header('Authorization'),'Bearer TEST-KEY-SENTINEL')
            return Response()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST-KEY-SENTINEL'}),patch('oci_lenz.ai.urllib.request.urlopen',side_effect=open_request):
            self.assertEqual(request_json('task',{},[],provider='openai',model='test-model')['placements'],[])
