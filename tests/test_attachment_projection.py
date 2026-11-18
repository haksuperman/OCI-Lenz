import copy
import json
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate


class AttachmentProjectionTests(unittest.TestCase):
    def test_only_api_confirmed_endpoint_pairs_are_projected_without_source_mutation(self):
        from oci_lenz.diagram_model import diagram_graph
        s=sample('drg-centered');before=copy.deepcopy(s);raw=graph(s)
        nodes,edges=diagram_graph(s)
        self.assertFalse(any(n['kind']=='drg_attachment' for n in nodes.values()))
        edge=next(e for e in edges if e['source']=='qa-drg' and e['target']=='vcn')
        self.assertEqual(edge['attachment_ids'],['qa-vcn-attach'])
        self.assertIn('DrgAttachment.drg_id',edge['evidence']);self.assertIn('network_details.id',edge['evidence'])
        self.assertEqual(s,before);self.assertEqual(graph(s),raw)
        self.assertFalse(any(nodes[e['source']]['kind']=='vcn' and nodes[e['target']]['kind']=='vcn' for e in edges))

    def test_attachment_names_and_shapes_are_absent_from_every_diagram_page(self):
        s=sample('drg-centered')
        for r in s['resources']:
            if r['kind']=='drg_attachment':r['name']='OMIT-ATTACHMENT-NAME-'+r['id']
        s=prepare_display(s);xml=render(s,detail_pages=True);validate(xml,s)
        self.assertTrue('OMIT-ATTACHMENT-NAME' not in xml)
        doc=E.fromstring(xml)
        for page in doc.findall('diagram'):
            cells={c.get('id'):c for c in page.iter('mxCell')}
            for r in s['resources']:
                if r['kind']=='drg_attachment':self.assertNotIn(r['id'],cells)
            self.assertFalse(any(c.get('ociVisualFrame') for c in cells.values()))
        edge=next(c for c in doc.find('diagram').iter('mxCell') if c.get('source')=='qa-drg' and c.get('target')=='vcn')
        self.assertEqual(json.loads(edge.get('ociAttachmentIds')),['qa-vcn-attach'])
        edge.set('target','public')
        with self.assertRaises(ValueError):validate(E.tostring(doc,encoding='unicode'),s)

    def test_duplicate_attachments_and_rpc_owner_edges_do_not_duplicate_lines(self):
        from oci_lenz.diagram_model import diagram_graph
        s=sample('drg-centered')
        att=copy.deepcopy(next(r for r in s['resources'] if r['id']=='qa-vcn-attach'));att['id']='second-att';s['resources'].append(att)
        _,edges=diagram_graph(s)
        vcn=[e for e in edges if {e['source'],e['target']}=={'vcn','qa-drg'}]
        self.assertEqual(len(vcn),1);self.assertEqual(vcn[0]['attachment_ids'],['qa-vcn-attach','second-att'])
        rpc=[e for e in edges if {e['source'],e['target']}=={'remote','qa-drg'}]
        self.assertEqual(len(rpc),1);self.assertIn('RemotePeeringConnection.drg_id',rpc[0]['evidence'])
        self.assertFalse(any(e['source']=='qa-vpn' and e['kind']=='drg_id' for e in edges))

    def test_unresolved_attachment_endpoints_are_not_guessed(self):
        from oci_lenz.diagram_model import diagram_graph
        s=sample('drg-centered')
        a=next(r for r in s['resources'] if r['id']=='qa-vcn-attach');a['drg_id']='outside-drg';a.pop('network_id')
        nodes,edges=diagram_graph(s)
        edge=next(e for e in edges if 'qa-vcn-attach' in e.get('attachment_ids',[]))
        self.assertEqual(nodes[edge['source']]['kind'],'unknown');self.assertEqual(nodes[edge['target']]['kind'],'unknown')
        self.assertFalse(any(e['target']=='vcn' and 'qa-vcn-attach' in e.get('attachment_ids',[]) for e in edges))

    def test_native_attachment_provenance_cannot_be_forged(self):
        s=prepare_display(sample('drg-centered'));doc=E.fromstring(render(s))
        edge=next(c for c in doc.find('diagram').iter('mxCell') if c.get('ociAttachmentIds'))
        edge.set('ociAttachmentIds','["not-an-attachment"]')
        with self.assertRaisesRegex(ValueError,'attachment'):validate(E.tostring(doc,encoding='unicode'),s)

    def test_duplicating_a_projected_native_edge_is_rejected(self):
        s=prepare_display(sample('drg-centered'));doc=E.fromstring(render(s));root=doc.find('diagram/mxGraphModel/root')
        edge=copy.deepcopy(next(c for c in root if c.get('ociAttachmentIds')))
        edge.set('id','unexpected-edge');root.append(edge)
        with self.assertRaisesRegex(ValueError,'relationship'):validate(E.tostring(doc,encoding='unicode'),s)
