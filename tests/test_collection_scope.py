"""Compartment-only collection scope; no live OCI requests."""
import copy
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from oci_lenz.cli import main
from oci_lenz.collect import collect
from oci_lenz.model import sample


class CollectionScopeTests(unittest.TestCase):
    def test_collector_has_no_vcn_filter_interface(self):
        self.assertNotIn('vcn_id',inspect.signature(collect).parameters)

    def test_removed_vcn_option_is_rejected_before_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv=['oci-lenz','collect','--profile','TEST','--region','test-region',
                  '--compartment-id','compartment-a','--vcn-id','vcn-a','--output',tmp]
            with patch.object(sys,'argv',argv),patch('oci_lenz.collect.collect') as fetch,redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:main()
            self.assertEqual(exc.exception.code,2)
            fetch.assert_not_called()

    def test_multiple_compartments_keep_all_vcns_and_cross_scope_resources(self):
        inventory=sample('overview');resources=inventory['resources']
        first=copy.deepcopy(inventory);second=copy.deepcopy(inventory)
        first['resources']=[r for r in resources if not r['id'].startswith('demo-3-')]
        second['resources']=[r for r in resources if r['id'].startswith('demo-3-')]
        first['coverage']=[{'status':'ok','compartment':'compartment-a'}]
        second['coverage']=[{'status':'ok','compartment':'compartment-b'}]
        # An instance in one compartment can have network objects in the other.
        moved=next(r for r in second['resources'] if r['kind']=='compute')
        second['resources'].remove(moved);first['resources'].append(moved)
        with tempfile.TemporaryDirectory() as tmp:
            argv=['oci-lenz','collect','--profile','TEST','--region','test-region',
                  '--compartment-id','compartment-a','--compartment-id','compartment-b','--output',tmp]
            with patch.object(sys,'argv',argv),patch('oci_lenz.collect.collect',side_effect=[first,second]) as fetch:main()
            result=json.loads((Path(tmp)/'snapshot.json').read_text())
        self.assertEqual(fetch.call_count,2)
        self.assertEqual([c.args for c in fetch.call_args_list],
                         [('TEST','test-region','compartment-a',None),('TEST','test-region','compartment-b',None)])
        self.assertEqual({r['id'] for r in result['resources']},{r['id'] for r in resources})
        self.assertEqual(sum(r['kind']=='vcn' for r in result['resources']),3)
        self.assertEqual(result['scope']['compartments'],['compartment-a','compartment-b'])
        self.assertTrue(any(e['kind']=='instance_id' and e['target']==moved['id'] for e in result['relationships']))
        self.assertEqual(len(result['coverage']),2)
