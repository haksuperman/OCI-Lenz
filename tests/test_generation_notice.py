"""Visible verification note without changing the configured diagram geometry."""
import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.architecture import make_scene,seed_plan
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.model import sample
from oci_lenz.routing import native_paths
from oci_lenz.diagram_model import diagram_graph


class GenerationNoticeTests(unittest.TestCase):
    def fixture(self,details=False):
        s=prepare_display(sample())
        p={'version':3,'overview':seed_plan(make_scene(s,view='overview'))}
        p['overview']['provider']='codex'
        if details:p['detail']=dict(seed_plan(make_scene(s,view='detail')),provider='codex')
        return s,p

    def test_ai_verification_note_is_editable_and_visible_on_every_page(self):
        s,p=self.fixture(details=True);xml=render(s,p,detail_pages=True);validate(xml,s)
        for page in E.fromstring(xml).findall('diagram'):
            c=page.find("mxGraphModel/root/mxCell[@id='generation-notice']")
            self.assertIsNotNone(c)
            self.assertIn('AI를 활용해 생성한 구성도입니다.',c.get('value'))
            self.assertIn('실제 OCI 리소스 및 설정과 대조·검증한 후 사용해 주세요.',c.get('value').replace('\n',''))
            self.assertEqual(c.get('vertex'),'1');self.assertEqual(c.get('parent'),'1')
            self.assertNotEqual(c.get('visible'),'0')
            frame=page.find("mxGraphModel/root/mxCell[@id='layout-region']/mxGeometry")
            if frame is not None:self.assertGreaterEqual(float(c.find('mxGeometry').get('y')),float(frame.get('y'))+float(frame.get('height'))+16)

    def test_diagnostic_output_does_not_claim_ai_generation(self):
        s,_=self.fixture();xml=render(s);validate(xml,s)
        notes=E.fromstring(xml).findall(".//mxCell[@id='generation-notice']")
        self.assertEqual(len(notes),2)
        for c in notes:
            self.assertIn('자동 생성된 구성도입니다.',c.get('value'))
            self.assertNotIn('AI를 활용',c.get('value'))

    def test_note_does_not_change_resource_positions_routes_or_model_items(self):
        s,p=self.fixture();before=copy.deepcopy((s,p));a=E.fromstring(render(s,p));p2=copy.deepcopy(p);p2['overview'].pop('provider')
        b=E.fromstring(render(s,p2));nodes=diagram_graph(s)[0]
        ar=a.find('diagram/mxGraphModel/root');br=b.find('diagram/mxGraphModel/root')
        self.assertEqual(native_paths(ar,nodes),native_paths(br,nodes))
        for root in (ar,br):root.remove(root.find("mxCell[@id='generation-notice']"))
        self.assertEqual(E.tostring(ar),E.tostring(br))
        self.assertEqual((s,p),before)
        self.assertNotIn('generation-notice',make_scene(s,view='overview')['aliases'])

    def test_clipped_or_intruding_note_is_rejected_and_legacy_xml_stays_valid(self):
        s,p=self.fixture();xml=render(s,p)
        for mode in ('clipped','inside'):
            doc=E.fromstring(xml);g=doc.find(".//mxCell[@id='generation-notice']/mxGeometry")
            g.set('height','1') if mode=='clipped' else g.set('y','100')
            with self.subTest(mode=mode),self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)
        doc=E.fromstring(xml)
        for root in doc.findall('diagram/mxGraphModel/root'):root.remove(root.find("mxCell[@id='generation-notice']"))
        validate(E.tostring(doc,encoding='unicode'),s)

    def test_narrow_empty_diagram_wraps_the_note_without_clipping(self):
        s=prepare_display(sample('empty'));xml=render(s);validate(xml,s)
        c=E.fromstring(xml).find(".//mxCell[@id='generation-notice']")
        self.assertIn('\n',c.get('value'))
        self.assertGreater(float(c.find('mxGeometry').get('height')),20)
