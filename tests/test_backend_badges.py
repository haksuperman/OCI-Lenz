"""Backend status is a local owned annotation, never invented OCI placement."""
import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.diagram_model import diagram_graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene


class BackendBadgeTests(unittest.TestCase):
    def snapshot(self,backends,status='ok'):
        s=sample();r=next(r for r in s['resources'] if r['kind']=='backend_set')
        r['backends']=backends
        if status is not None:r['backends_status']=status
        return s,r['id']

    def test_empty_success_has_no_fake_unknown_or_status_badge(self):
        s,key=self.snapshot([]);nodes,edges=diagram_graph(s)
        self.assertFalse(nodes[key].get('backend_badge'))
        self.assertFalse(any(e['source']==key and e['kind']=='backend' for e in edges))

    def test_failure_and_legacy_empty_are_distinct_from_successful_zero(self):
        for status,text in [('unavailable','백엔드 조회 불가'),(None,'백엔드 조회 상태 미확인')]:
            s,key=self.snapshot([],status)
            self.assertEqual(diagram_graph(s)[0][key]['backend_badge'],text)
            xml=render(prepare_display(s));validate(xml,prepare_display(s))
            cell=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='"+key+"']")
            self.assertIn(text,cell.get('value'))
            self.assertNotIn('↓',cell.get('value'))

    def test_lb_and_nlb_collectors_preserve_successful_empty_vs_denied(self):
        from tests.test_collect import CollectorTests,oci
        if oci is None:self.skipTest('OCI SDK required')
        from types import SimpleNamespace as N
        extra={'list_backends':[],
               'nlb_list_network_load_balancers':[N(id='nlb',display_name='Synthetic NLB',subnet_id='s',
                   network_security_group_ids=[],ip_addresses=[],listeners={},lifecycle_state='ACTIVE')],
               'nlb_list_backend_sets':[N(name='set')],'nlb_list_backends':[]}
        for denied in (None,'list_backends','nlb_list_backends'):
            s,_=CollectorTests().run_collect(fail=denied,extra=extra)
            sets={r['lb_id']:r for r in s['resources'] if r['kind']=='backend_set'}
            for lb,api in [('lb','list_backends'),('nlb','nlb_list_backends')]:
                self.assertEqual(sets[lb]['backends'],[])
                self.assertEqual(sets[lb]['backends_status'],'unavailable' if denied==api else 'ok')

    def test_multiple_unresolved_backends_collapse_into_owned_label_without_losing_evidence(self):
        s,key=self.snapshot([{'ip_address':'10.0.1.10','port':80},
                             {'ip_address':'203.0.113.20','port':80},
                             {'ip_address':'203.0.113.21','port':443}])
        before=copy.deepcopy(s);canonical=graph(s)
        display=prepare_display(s);nodes,edges=diagram_graph(s)
        self.assertEqual(nodes[key]['backend_badge'],'백엔드 대상 미확인 (2)')
        scene=make_scene(display,view='overview')
        unknowns={e['target'] for e in edges if e['source']==key and e['kind']=='backend' and nodes[e['target']]['kind']=='unknown'}
        self.assertTrue(unknowns)
        self.assertTrue(unknowns.isdisjoint(scene['aliases']))
        xml=render(display);validate(xml,display)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertIn('백엔드 대상 미확인 (2)',cells[key].get('value'))
        self.assertIn('ociBackendBadge=1;',cells[key].get('style'))
        self.assertTrue(all(cells[k].get('visible')=='0' for k in unknowns))
        for i,e in enumerate(edges):
            if e['kind']=='backend' and e['source']==key:
                c=cells['edge-'+str(i)]
                self.assertEqual((c.get('source'),c.get('target')),(e['source'],e['target']))
                self.assertEqual(c.get('visible')=='0',e['target'] in unknowns)
        self.assertEqual(graph(s),canonical);self.assertEqual(s,before)
        self.assertEqual(render(display),xml)

    def test_badges_apply_to_detail_pages_and_known_targets_remain_visible(self):
        s,key=self.snapshot([{'ip_address':'10.0.1.10','port':80},
                             {'ip_address':'203.0.113.20','port':80}])
        xml=render(prepare_display(s),detail_pages=True);validate(xml,prepare_display(s))
        for page in E.fromstring(xml).findall('diagram'):
            if page.get('id')=='information-index':continue
            cells={c.get('id'):c for c in page.iter('mxCell')}
            if key in cells:self.assertIn('백엔드 대상 미확인',cells[key].get('value'))
            if 'compute' in cells:self.assertNotEqual(cells['compute'].get('visible'),'0')

    def test_nlb_explicit_unresolved_targets_use_the_same_owned_annotation(self):
        s,key=self.snapshot([{'target_id':'compute','port':80},
                             {'target_id':'outside-scope','port':443}])
        lb=next(r for r in s['resources'] if r['kind']=='lb')
        lb['kind']='nlb';lb['subnet_id']=lb.pop('subnet_ids')[0]
        nodes,edges=diagram_graph(s)
        self.assertEqual(nodes[key]['backend_badge'],'백엔드 대상 미확인 (1)')
        self.assertTrue(any(e['source']==key and e['target']=='compute' and e['kind']=='backend' for e in edges))
        display=prepare_display(s);xml=render(display);validate(xml,display)
        self.assertIn('백엔드 대상 미확인 (1)',xml)

    def test_status_footprint_change_rejects_old_saved_layout(self):
        from oci_lenz.architecture import seed_plan
        s,key=self.snapshot([])
        scene=make_scene(prepare_display(s),view='overview')
        plan={'version':3,'overview':seed_plan(scene)}
        next(r for r in s['resources'] if r['id']==key)['backends_status']='unavailable'
        with self.assertRaises(ValueError):render(prepare_display(s),plan)
