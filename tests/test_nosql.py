"""NoSQL metadata is regional, not a guessed subnet or application connection."""
import copy,json,unittest
import xml.etree.ElementTree as E
from unittest.mock import Mock
from tests import test_collect as fixtures
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate,ICONS
from oci_lenz.architecture import make_scene

oci=fixtures.oci


@unittest.skipIf(oci is None,'OCI SDK required')
class NoSQLTests(unittest.TestCase):
    def collect(self,fail=None,extra=None,requests=None):
        data={'nosql_list_tables':oci.nosql.models.TableCollection(items=[oci.nosql.models.TableSummary(
            id='nosql',name='Synthetic NoSQL Table',compartment_id='c',lifecycle_state='ACTIVE',
            freeform_tags={'sensitive':'NEVER-STORE'})])}
        data.update(extra or {})
        return fixtures.CollectorTests().run_collect(extra=data,fail=fail,request_log=requests)[0]

    def test_only_scoped_table_metadata_is_collected_without_schema_or_rows(self):
        requests=[];s=self.collect(requests=requests);nodes,edges=graph(s)
        self.assertEqual(nodes['nosql'],{'id':'nosql','kind':'nosql_table','name':'Synthetic NoSQL Table',
            'compartment_id':'c','lifecycle_state':'ACTIVE','deployment_scope':'regional'})
        self.assertFalse(any(e['source']=='nosql' for e in edges))
        self.assertNotIn('NEVER-STORE',json.dumps(s))
        calls=[(name,args,kw) for name,args,kw in requests if name.startswith('nosql_')]
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'nosql_list_tables')
        self.assertEqual(calls[0][2]['compartment_id'],'c')

    def test_denied_list_is_not_successful_empty_inventory(self):
        for denied,extra,status in [(None,{'nosql_list_tables':[]},'ok'),('nosql_list_tables',{},'permission_denied')]:
            s=self.collect(fail=denied,extra=extra)
            c=next(c for c in s['coverage'] if c['service']=='nosql')
            self.assertEqual(c['status'],status)
            if status=='ok':self.assertEqual(c['count'],0)
            else:self.assertNotIn('count',c)
            self.assertNotIn('sensitive error',json.dumps(s))

    def test_native_parent_is_own_compartment_outside_vcn_and_replay_is_exact(self):
        s=self.collect();before=copy.deepcopy(s);d=prepare_display(s);scene=make_scene(d,view='overview')
        item=scene['items'][scene['aliases']['nosql']]
        self.assertEqual(scene['items'][item['parent']]['kind'],'compartment')
        xml=render(d,detail_pages=True);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertEqual(cells['nosql'].get('parent'),cells['v'].get('parent'))
        self.assertIn('nosql-icon',cells);self.assertIn('Synthetic NoSQL Table',cells['nosql'].get('value'))
        self.assertEqual(render(d,detail_pages=True),xml);self.assertEqual(s,before)
        self.assertEqual(ICONS['oci_cache'],46);self.assertEqual(ICONS['nosql_table'],46)

    def test_nosql_only_compartment_is_rendered_without_vcn(self):
        s=self.collect();s['resources']=[r for r in s['resources'] if r['kind']=='nosql_table']
        d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertTrue(cells['nosql'].get('parent').startswith('layout-compartment-'))
        self.assertNotIn('Private:',cells['nosql'].get('value'))

    def test_other_compartment_is_never_merged_into_a_vcn_owner(self):
        s=self.collect();next(r for r in s['resources'] if r['id']=='nosql')['compartment_id']='other'
        d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertNotEqual(cells['nosql'].get('parent'),cells['v'].get('parent'))

    def test_subnet_fields_cannot_turn_a_regional_table_into_a_network_resource(self):
        s=self.collect();table=next(r for r in s['resources'] if r['id']=='nosql')
        table.update(subnet_id='s',vcn_id='v',nsg_ids=['nsg'])
        self.assertFalse(any(e['source']=='nosql' for e in graph(s)[1]))
        d=prepare_display(s);xml=render(d);validate(xml,d)
        doc=E.fromstring(xml);cell=doc.find("diagram/mxGraphModel/root/mxCell[@id='nosql']")
        cell.set('parent','s')
        with self.assertRaisesRegex(ValueError,'NoSQL table must remain'):
            validate(E.tostring(doc,encoding='unicode'),d)

    def test_redaction_masks_table_name_and_original_resource_is_preserved(self):
        s=self.collect();original=copy.deepcopy(s);xml=render(prepare_display(s,redact=True))
        validate(xml,prepare_display(s,redact=True))
        self.assertNotIn('Synthetic NoSQL Table',xml);self.assertEqual(s,original)

    def test_generated_list_api_uses_collection_pagination_and_only_get_transport(self):
        from oci_lenz.nosql import collect_nosql
        client=oci.nosql.NosqlClient.__new__(oci.nosql.NosqlClient)
        client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
        client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None
        pages=[]
        def transport(**request):
            self.assertEqual(request['operation_name'],'list_tables');self.assertEqual(request['method'],'GET')
            query=request['query_params'];self.assertEqual(query['compartmentId'],'c');pages.append(query.get('page'))
            data=oci.nosql.models.TableCollection(items=[oci.nosql.models.TableSummary(id='a' if len(pages)==1 else 'b',name='Synthetic table',compartment_id='c')])
            return oci.response.Response(200,{'opc-next-page':'synthetic-next'} if len(pages)==1 else {},data,None)
        client.base_client.call_api=transport;resources=[]
        def call(service,api,**kw):
            self.assertEqual((service,api),('nosql','list_tables'))
            result=oci.pagination.list_call_get_all_results(client.list_tables,**kw).data
            return result if isinstance(result,list) else result.items
        def add(obj,kind,**data):resources.append({'id':obj.id,'kind':kind,**data})
        collect_nosql(call,add,'c')
        self.assertEqual(pages,[None,'synthetic-next']);self.assertEqual(len(resources),2)
