"""Resource-owned labels, without detached text vertices."""
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene
from oci_lenz.visual_review import masked_preview


class NativeLabelTests(unittest.TestCase):
    def test_label_belongs_to_resource_and_sits_just_below_symbol(self):
        s=prepare_display(sample());xml=render(s,style='architecture');root=E.fromstring(xml).find('diagram/mxGraphModel/root')
        cells={c.get('id'):c for c in root}
        self.assertFalse(any(k.endswith(('-label-name','-label-details')) for k in cells))
        c=cells['compute'];self.assertIn('Compute',c.get('value'));self.assertIn('10.0.1.10',c.get('value'))
        self.assertIn('html=1;',c.get('style'))
        options=dict(p.split('=',1) for p in c.get('style').split(';') if '=' in p)
        g=cells['compute-icon'].find('mxGeometry')
        gap=float(options['spacingTop'])-float(g.get('y'))-float(g.get('height'))
        self.assertGreaterEqual(gap,0);self.assertLessEqual(gap,4)
        self.assertLess(float(g.get('height')),45)  # excludes the toolkit's old caption area
        self.assertTrue(validate(xml,s))

    def test_rich_text_is_escaped_and_preview_keeps_markup_but_hides_data(self):
        raw=sample();next(r for r in raw['resources'] if r['kind']=='compute')['name']='가상 <script> & Test'
        s=prepare_display(raw);xml=render(s,style='architecture');scene=make_scene(s,view='overview')
        c=E.fromstring(xml).find("diagram/mxGraphModel/root/mxCell[@id='compute']")
        self.assertIn('&lt;script&gt;',c.get('value'));self.assertNotIn('<script>',c.get('value'))
        preview=masked_preview(xml,s,scene)
        masked=E.fromstring(preview).find("diagram/mxGraphModel/root/mxCell[@id='compute']").get('value')
        self.assertIn('<div',masked);self.assertNotIn('가상',masked);self.assertNotIn('script',masked)
        self.assertNotIn('10.0.1.10',preview)
        self.assertIn('font-size',masked)
        self.assertIn(scene['aliases']['compute'],masked)

    def test_official_vector_art_fits_the_caption_free_icon_bounds(self):
        s=prepare_display(sample());doc=E.fromstring(render(s,style='architecture'))
        cells={c.get('id'):c for c in doc.find('diagram/mxGraphModel/root')}
        def rect(key):
            c=cells[key];g=c.find('mxGeometry')
            if g is None:return 0,0,0,0
            x,y,w,h=[float(g.get(f,0)) for f in ('x','y','width','height')]
            if c.get('parent') in cells:
                px,py,_,_=rect(c.get('parent'));x+=px;y+=py
            return x,y,w,h
        ix,iy,iw,ih=rect('compute-icon');painted=0
        for key,c in cells.items():
            if not key.startswith('compute-i-'):continue
            options=dict(p.split('=',1) for p in c.get('style','').split(';') if '=' in p)
            if options.get('fillColor','none')=='none' and options.get('strokeColor','none')=='none':continue
            x,y,w,h=rect(key);painted+=1
            self.assertGreaterEqual(x+0.001,ix);self.assertGreaterEqual(y+0.001,iy)
            self.assertLessEqual(x+w,ix+iw+0.001);self.assertLessEqual(y+h,iy+ih+0.001)
        self.assertGreater(painted,0)
