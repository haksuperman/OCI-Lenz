import copy
import json
import tempfile
import io
import sys
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import unittest
import xml.etree.ElementTree as E
from oci_lenz.model import sample,graph
from oci_lenz.draw import render,validate
from oci_lenz.display import prepare_display
from oci_lenz.cli import main


class DisplayTests(unittest.TestCase):
    def test_cli_defaults_to_operational_names_redaction_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/'snapshot.json'
            snapshot.write_text(json.dumps(self.snapshot()))
            for redact in (False,True):
                out=root/('sharing' if redact else 'operational')
                argv=['oci-lenz','draw','--snapshot',str(snapshot),'--output',str(out),'--no-ai','--no-png']
                if redact:argv.append('--redact')
                with patch.object(sys,'argv',argv),redirect_stdout(io.StringIO()):main()
                xml=(out/'architecture.drawio').read_text()
                self.assertEqual('192.0.2.20' in xml,not redact)
                self.assertEqual(json.loads((out/'validation.json').read_text())['redacted'],redact)

    def snapshot(self):
        s=sample()
        for r in s['resources']:
            if r['id']=='compute':r['name']='synthetic-operational-web-server-name-with-long-suffix'
            if r['id']=='vnic':r.update(public_ip='192.0.2.10')
            if r['id']=='lb':r['ip_addresses']=[{'ip_address':'192.0.2.20','is_public':True}]
            if r['id']=='private':r['cidr_block']='10.0.1.0/24'
        s['resources'].append(dict(id='secondary',name='Secondary NIC',kind='vnic',instance_id='compute',subnet_id='private',vcn_id='vcn',private_ips=['10.0.1.11']))
        return s

    def test_private_labels_include_names_observed_ips_and_cidrs(self):
        s=self.snapshot();original=copy.deepcopy(s)
        private=prepare_display(s)
        self.assertEqual(s,original)
        self.assertEqual(graph(s)[1],graph(private)[1])
        xml=render(private);validate(xml,private)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram').iter('mxCell')}
        import html
        label=html.unescape(cells['compute'].get('value')).replace('<br>','')
        self.assertIn('synthetic-operational-web-server-name-with-long-suffix',label)
        for ip in ('10.0.1.10','192.0.2.10'):self.assertIn(ip,label)
        index=E.fromstring(xml).find("diagram[@id='information-index']")
        self.assertIn('10.0.1.11',E.tostring(index,encoding='unicode'))
        self.assertIn('192.0.2.20',cells['lb'].get('value'))
        self.assertIn('10.0.1.0/24',cells['private'].get('value'))

    def test_redacted_output_hides_labels_ips_and_route_destinations(self):
        s=self.snapshot()
        next(r for r in s['resources'] if r['kind']=='route')['rules'][0]['destination']='198.51.100.0/24'
        safe=prepare_display(s,redact=True)
        xml=render(safe)
        validate(xml,safe)
        for text in ('synthetic-operational','10.0.1.10','10.0.1.11','192.0.2.10','192.0.2.20','10.0.1.0/24','198.51.100.0/24'):
            self.assertNotIn(text,xml)
        self.assertIn('Tenancy: Hidden',xml)

    def test_legacy_snapshot_without_new_address_fields_still_renders(self):
        s=prepare_display(sample())
        validate(render(s),s)
