"""Pod network badge is an editable header annotation, never a new OCI node."""
import copy,unittest,xml.etree.ElementTree as E
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate
from oci_lenz.architecture import make_scene,seed_plan
from oci_lenz.oke_badges import badge_rectangles


class OkeBadgeTests(unittest.TestCase):
    def fixture(self):
        s=prepare_display(sample('oke'));scene=make_scene(s,view='overview')
        return s,scene,{'version':3,'overview':seed_plan(scene)}

    def test_badge_uses_official_icon_inside_actual_subnet_header(self):
        s,scene,p=self.fixture();before=copy.deepcopy((s,p));xml=render(s,p);validate(xml,s)
        root=E.fromstring(xml).find('diagram/mxGraphModel/root')
        badge=root.find("mxCell[@ociRoleBadge='oke_pods']")
        self.assertIsNotNone(badge);self.assertEqual(badge.get('parent'),'qa-pods')
        self.assertEqual(badge.get('value'),'OKE Pods');self.assertIn('rounded=1',badge.get('style'))
        icon=root.find("mxCell[@id='"+badge.get('id')+"-icon']")
        self.assertIn('Container Engine for Kubernetes',icon.get('ociOfficialIcon',''))
        parent=root.find("mxCell[@id='qa-pods']");self.assertNotIn('OKE Pod network',parent.get('value'))
        self.assertIn('10.0.4.0/24',parent.get('value'))
        g=badge.find('mxGeometry');self.assertLessEqual(float(g.get('y'))+float(g.get('height')),scene['items'][scene['aliases']['qa-pods']]['header_height'])
        self.assertEqual((s,p),before)
        self.assertEqual(make_scene(s,view='overview')['signature'],scene['signature'])
        self.assertNotIn(badge.get('id'),scene['aliases'])

    def test_no_badge_without_api_role_and_no_duplicate_badges_for_shared_subnet(self):
        s=prepare_display(sample());self.assertNotIn('ociRoleBadge',render(s))
        s,scene,p=self.fixture();next(r for r in s['resources'] if r['id']=='qa-pods')['oke_pod_cluster_ids'].append('another-cluster')
        xml=render(s,p);validate(xml,s)
        self.assertEqual(len(E.fromstring(xml).findall(".//mxCell[@ociRoleBadge='oke_pods']")),1)

    def test_clipping_and_wrong_parent_are_rejected(self):
        s,scene,p=self.fixture();xml=render(s,p)
        for mode in ('outside','parent','text'):
            doc=E.fromstring(xml);badge=doc.find(".//mxCell[@ociRoleBadge='oke_pods']")
            self.assertIsNotNone(badge)
            if mode=='outside':badge.find('mxGeometry').set('x','90000')
            elif mode=='parent':badge.set('parent','vcn')
            else:badge.find('mxGeometry').set('width','10')
            with self.subTest(mode=mode),self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)

    def test_badge_obstacle_is_reported_by_actual_geometry(self):
        root=E.fromstring('<root><mxCell id="badge" parent="subnet" ociRoleBadge="oke_pods"/></root>')
        self.assertEqual(badge_rectangles(root,lambda key:(20,30,100,18)),[('subnet',(20,30,100,18))])

    def test_replay_and_redaction_keep_badge_without_names_or_addresses(self):
        s,scene,p=self.fixture();self.assertEqual(render(s,p),render(s,p))
        redacted=prepare_display(sample('oke'),redact=True);xml=render(redacted);validate(xml,redacted)
        self.assertIn('ociRoleBadge="oke_pods"',xml)
        self.assertNotIn('Synthetic OKE Pods',xml);self.assertNotIn('10.0.4.0',xml)
