"""Evidence-preserving label and display-flow regression cases."""
import unittest
import xml.etree.ElementTree as E
from oci_lenz.typography import wrap_text
from oci_lenz.routing import route_native_edges,intersects


class FlowReadabilityTests(unittest.TestCase):
    def test_names_wrap_at_separators_instead_of_leaving_one_letter(self):
        name='SyntheticLongLabel-DEV'
        result=wrap_text(name,154,12)
        self.assertEqual(result,'SyntheticLongLabel-\nDEV')
        self.assertEqual(result.replace('\n',''),name)

    def test_short_suffix_keeps_its_separator_on_the_previous_line(self):
        self.assertEqual(wrap_text('SyntheticLongLabel-QA',140,12),'SyntheticLongLabel-\nQA')

    def test_long_unbroken_name_has_no_single_character_last_line(self):
        name='A'*22
        result=wrap_text(name,154,12)
        self.assertEqual(result.replace('\n',''),name)
        self.assertTrue(all(len(line)>=3 for line in result.splitlines()))

    def test_lb_ownership_fanout_uses_downward_shared_corridor(self):
        root=E.Element('root')
        rects={'lb':(220,20,170,140),'left':(20,184,170,140),'right':(420,184,170,140)}
        for key,(x,y,w,h) in rects.items():
            c=E.SubElement(root,'mxCell',id=key,parent='1',vertex='1')
            E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h))
        for key in ('left','right'):
            c=E.SubElement(root,'mxCell',id='edge-'+key,source=key,target='lb',parent='1',edge='1',style='startArrow=block;endArrow=none;')
            E.SubElement(c,'mxGeometry',relative='1')
        nodes={'lb':{'kind':'lb'},'left':{'kind':'backend_set'},'right':{'kind':'backend_set'}}
        route_native_edges(root,nodes)
        paths=[]
        for c in root.findall("mxCell[@edge='1']"):
            self.assertEqual(c.get('target'),'lb')
            self.assertIn('exitX=0.5;exitY=0;',c.get('style'))
            self.assertIn('entryX=0.5;entryY=1;',c.get('style'))
            points=[(float(p.get('x')),float(p.get('y'))) for p in c.find('mxGeometry/Array')]
            target=rects[c.get('source')]
            path=[(target[0]+target[2]/2,target[1]),*points,(305,160)]
            for a,b in zip(path,path[1:]):
                self.assertTrue(a[0]==b[0] or a[1]==b[1])
                self.assertFalse(any(intersects(a,b,r) for r in rects.values()))
            paths.append(points)
        self.assertEqual(paths[0][-1],paths[1][-1])
