import copy
import json
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene,seed_plan,check_plan,apply_design
from oci_lenz.draw import validate
from oci_lenz.typography import wrap_text

CASES=('long-names','dense','fanout','cross-compartment','unresolved','empty')

class TopologyMatrixTests(unittest.TestCase):
    def test_matrix_preserves_evidence_and_is_repeatable_without_service_inference(self):
        for case in CASES:
            with self.subTest(case=case):
                raw=sample(case);s=prepare_display(raw);before=copy.deepcopy(graph(s))
                scene=make_scene(s,view='overview');plan={'version':3,'overview':seed_plan(scene)}
                self.assertFalse(any(i['kind']=='service_group' for i in scene['items'].values()))
                self.assertEqual(check_plan(scene,plan['overview']),[])
                xml=apply_design(s,plan);validate(xml,s)
                self.assertEqual(xml,apply_design(s,plan))
                self.assertEqual(graph(s),before)
                cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
                self.assertTrue(set(before[0])<=set(cells))
                self.assertEqual(sum(c.get('edge')=='1' for c in cells.values()),len(before[1]))
                self.assertTrue(all(c.get('source')=='synthetic' for c in raw['coverage']))

    def test_long_network_titles_reserve_header_space(self):
        raw=sample();next(r for r in raw['resources'] if r['id']=='private')['name']='가상검증네트워크제목-'*12
        scene=make_scene(prepare_display(raw),view='overview')
        parent=scene['aliases']['private'];child=scene['aliases']['compute']
        self.assertGreater(scene['items'][parent].get('header_height',0),48)
        plan=seed_plan(scene);boxes={p['id']:p for p in plan['placements']}
        self.assertGreaterEqual(boxes[child]['y']-boxes[parent]['y'],scene['items'][parent]['header_height'])
        bad=copy.deepcopy(plan);next(p for p in bad['placements'] if p['id']==child)['y']=boxes[parent]['y']+48
        self.assertTrue(check_plan(scene,bad))

    def test_information_index_grows_for_wrapped_unicode_text(self):
        raw=sample();next(r for r in raw['resources'] if r['kind']=='compute')['name']='가상독립검증문자열'*60
        doc=E.fromstring(apply_design(prepare_display(raw)))
        row=next(c for c in doc.find("diagram[@id='information-index']").iter('mxCell') if '가상독립검증문자열' in c.get('value',''))
        lines=wrap_text(row.get('value'),1080,12).split('\n')
        self.assertGreaterEqual(float(row.find('mxGeometry').get('height')),20+16*len(lines))

    def test_index_clipping_is_rejected_by_validator(self):
        s=prepare_display(sample());doc=E.fromstring(apply_design(s))
        doc.find("diagram[@id='information-index']/mxGraphModel/root/mxCell[@vertex='1']/mxGeometry").set('height','1')
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)

    def test_empty_snapshot_has_notice_without_claiming_collection_success(self):
        s=prepare_display(sample('empty'));doc=E.fromstring(apply_design(s))
        index=doc.find("diagram[@id='information-index']")
        self.assertTrue(any('coverage.json' in c.get('value','') for c in index.iter('mxCell')))
        validate(E.tostring(doc,encoding='unicode'),s)

    def test_matrix_requests_keep_source_labels_and_addresses_local(self):
        s=prepare_display(sample('long-names'));scene=make_scene(s,view='overview')
        request=json.dumps(scene['request'],ensure_ascii=False)
        self.assertNotIn('가상검증용',request)
        self.assertNotIn('10.0.1.10',request)
        self.assertTrue(all(isinstance(i['header_height'],int) for i in scene['items'].values() if i['container']))

    def test_detail_pages_keep_cross_compartment_and_unknown_relations(self):
        for case in ('cross-compartment','unresolved'):
            with self.subTest(case=case):
                s=prepare_display(sample(case));xml=apply_design(s,detail_pages=True)
                validate(xml,s)

    def test_information_index_row_overlap_is_rejected(self):
        s=prepare_display(sample());doc=E.fromstring(apply_design(s))
        rows=doc.findall("diagram[@id='information-index']/mxGraphModel/root/mxCell[@vertex='1']")
        rows[1].find('mxGeometry').set('y',rows[0].find('mxGeometry').get('y'))
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)

    def test_cross_compartment_and_unknown_scenarios_have_expected_evidence(self):
        s=sample('cross-compartment');nodes,edges=graph(s)
        self.assertGreater(len(s['scope']['compartments']),1)
        self.assertTrue(any(e['kind']=='instance_id' and nodes[e['source']].get('compartment_id')!=nodes[e['target']].get('compartment_id') for e in edges))
        s=sample('unresolved');nodes,edges=graph(s)
        self.assertTrue(any(r['kind']=='unknown' for r in nodes.values()))
        self.assertTrue(any(e['kind']=='backend' and nodes[e['target']]['kind']=='unknown' for e in edges))
