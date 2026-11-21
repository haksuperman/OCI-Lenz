"""Synthetic design regressions: visible anchors, logical sets, fitted cards."""
import copy
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.architecture import apply_design,make_scene
from oci_lenz.draw import icon,validate
from oci_lenz.typography import card_metrics,style_card
from oci_lenz.routing import route_native_edges


def options(cell):return dict(p.split('=',1) for p in cell.get('style','').split(';') if '=' in p)


class FlowDesignTests(unittest.TestCase):
    def test_backend_sets_are_editable_name_tags_without_duplicate_lb_symbols(self):
        s=prepare_display(sample('fanout'));before=copy.deepcopy(graph(s));xml=apply_design(s);validate(xml,s)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        for key,r in before[0].items():
            if r['kind']=='backend_set':
                self.assertFalse(key+'-icon' in cells)
                self.assertIn('rounded=1;',cells[key].get('style'))
                self.assertIn(r['name'],cells[key].get('value').replace('<br>',''))
        self.assertEqual(graph(s),before)
        self.assertEqual(sum(c.get('edge')=='1' for c in cells.values()),len(before[1]))

    def test_simple_cards_fit_symbol_and_text_and_long_names_grow(self):
        simple={'kind':'compute','name':'Synthetic VM','display_details':['Private: 10.0.1.10']}
        short=card_metrics(simple,170)
        long=card_metrics(dict(simple,name='가상검증네트워크서버'*8),170)
        logical=card_metrics({'kind':'backend_set','name':'web-set','display_details':[]},170)
        self.assertLess(short['height'],100)
        self.assertGreater(long['height'],short['height'])
        self.assertLess(logical['height'],45)

    def native_cards(self,x=0,y=350):
        root=E.Element('root');nodes={}
        for key,xx,yy in (('source',0,0),('target',x,y)):
            c=E.SubElement(root,'mxCell',id=key,parent='1',vertex='1')
            E.SubElement(c,'mxGeometry',x=str(xx),y=str(yy),width='170',height='220')
            resource={'kind':'compute','name':'Synthetic '+key,'display_details':['Private: 10.0.1.10']}
            nodes[key]=resource;icon(root,key,'compute',58,10);style_card(root,c,resource,170)
        edge=E.SubElement(root,'mxCell',id='edge',source='source',target='target',edge='1',parent='1',style='endArrow=block;')
        E.SubElement(edge,'mxGeometry',relative='1')
        return root,nodes,edge

    def test_vertical_connector_attaches_to_caption_bottom_and_symbol_top(self):
        root,nodes,edge=self.native_cards();route_native_edges(root,nodes)
        cells={c.get('id'):c for c in root};style=options(edge)
        source=options(cells['source']);target_icon=cells['target-icon'].find('mxGeometry')
        actual_exit=float(style['exitY'])*220
        self.assertLess(actual_exit,110)
        self.assertAlmostEqual(actual_exit,float(source['ociContentY'])+float(source['ociContentH']))
        self.assertAlmostEqual(float(style['entryY'])*220,float(target_icon.get('y')))
        self.assertEqual(style['exitPerimeter'],'0');self.assertEqual(style['entryPerimeter'],'0')
        self.assertEqual((edge.get('source'),edge.get('target')),('source','target'))

    def test_lateral_connector_attaches_to_symbol_side_above_text(self):
        root,nodes,edge=self.native_cards(x=350,y=0);route_native_edges(root,nodes)
        cells={c.get('id'):c for c in root};style=options(edge);g=cells['source-icon'].find('mxGeometry')
        self.assertAlmostEqual(float(style['exitX'])*170,float(g.get('x'))+float(g.get('width')))
        self.assertAlmostEqual(float(style['exitY'])*220,float(g.get('y'))+float(g.get('height'))/2)

    def test_ai_scene_distinguishes_name_tags_and_preserves_parents(self):
        s=prepare_display(sample());scene=make_scene(s,view='overview')
        item=scene['items'][scene['aliases']['backend-set']]
        self.assertEqual(item['representation'],'name_tag')
        self.assertEqual(item['parent'],scene['aliases']['public'])
        self.assertFalse(any(r['kind']=='service_group' for r in scene['items'].values()))

    def test_unknown_route_targets_do_not_float_in_backend_overview(self):
        s=prepare_display(sample('unresolved'));nodes,edges=graph(s)
        scene=make_scene(s,view='overview');detail=make_scene(s)
        flow_targets={e['target'] for e in edges if e['kind'] in ('backend','lb_id')}
        doc=E.fromstring(apply_design(s));cells={c.get('id'):c for c in doc.find('diagram').iter('mxCell')}
        for key,r in nodes.items():
            if r['kind']!='unknown':continue
            backend_only=all(e['kind']=='backend' for e in edges if e['target']==key)
            self.assertEqual(key in detail['aliases'],not backend_only)
            self.assertEqual(key in scene['aliases'],key in flow_targets and not backend_only)
            self.assertEqual(cells[key].get('visible')=='0',key not in flow_targets or backend_only)
        self.assertTrue(set(nodes)<=set(cells))

    def test_compartment_heading_uses_known_name_and_keeps_it_local(self):
        import json
        s=sample();s['scope']['compartment_names']={'unspecified':'Synthetic Deployment'}
        safe=prepare_display(s);scene=make_scene(safe,view='overview')
        self.assertNotIn('Synthetic Deployment',json.dumps(scene['request']))
        root=E.fromstring(apply_design(safe)).find('diagram/mxGraphModel/root')
        frame=root.find("mxCell[@id='layout-compartment-0']")
        self.assertIn('Synthetic Deployment',frame.get('value'))
        redacted=E.fromstring(apply_design(prepare_display(s,redact=True)))
        self.assertNotIn('Synthetic Deployment',E.tostring(redacted,encoding='unicode'))

    def test_vcn_boundary_is_stronger_than_subnet_boundary(self):
        doc=E.fromstring(apply_design(prepare_display(sample())))
        cells={c.get('id'):c for c in doc.find('diagram').iter('mxCell')}
        self.assertGreater(float(options(cells['vcn'])['strokeWidth']),float(options(cells['private'])['strokeWidth']))
