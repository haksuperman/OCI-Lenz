"""Scoped metadata inventory and evidence-only regional service placement."""
import copy,json,unittest
import xml.etree.ElementTree as E
from types import SimpleNamespace as N
from unittest.mock import Mock
from tests import test_collect as fixtures
from oci_lenz.model import graph,sample
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate,ICONS

oci=fixtures.oci

@unittest.skipIf(oci is None,'OCI SDK required')
class RegionalServicesTests(unittest.TestCase):
    def responses(self):
        return {
            'object_storage_get_namespace':'synthetic-namespace',
            'object_storage_list_buckets':[oci.object_storage.models.BucketSummary(name='Synthetic Bucket',compartment_id='c')],
            'object_storage_get_bucket':oci.object_storage.models.Bucket(id='bucket',name='Synthetic Bucket',compartment_id='c',metadata={'secret':'NEVER-STORE'}),
            'artifacts_list_container_repositories':oci.artifacts.models.ContainerRepositoryCollection(items=[oci.artifacts.models.ContainerRepositorySummary(id='registry',display_name='Synthetic Registry',compartment_id='c',lifecycle_state='AVAILABLE')]),
            'devops_list_projects':oci.devops.models.ProjectCollection(items=[oci.devops.models.ProjectSummary(id='project',name='Synthetic Project',compartment_id='c',description='NEVER-STORE')]),
            'devops_list_repositories':oci.devops.models.RepositoryCollection(items=[oci.devops.models.RepositorySummary(id='repo',name='Synthetic Code',compartment_id='c',project_id='project',http_url='NEVER-STORE')]),
            'devops_list_build_pipelines':oci.devops.models.BuildPipelineCollection(items=[oci.devops.models.BuildPipelineSummary(id='build',display_name='Synthetic Build',compartment_id='c',project_id='project')]),
            'devops_list_deploy_pipelines':oci.devops.models.DeployPipelineCollection(items=[oci.devops.models.DeployPipelineSummary(id='deploy',display_name='Synthetic Deploy',compartment_id='c',project_id='project')]),
            'devops_list_deploy_environments':oci.devops.models.DeployEnvironmentCollection(items=[oci.devops.models.DeployEnvironmentSummary(id='environment',display_name='Synthetic Environment',compartment_id='c',project_id='project',deploy_environment_type='OKE_CLUSTER')])}
    def collect(self,fail=None,extra=None):
        responses=self.responses();responses.update(extra or {});requests=[]
        s=fixtures.CollectorTests().run_collect(extra=responses,fail=fail,request_log=requests)[0]
        return s,requests
    def test_metadata_allowlist_scope_and_project_evidence(self):
        s,requests=self.collect();nodes,edges=graph(s)
        for key in ('bucket','registry','project','repo','build','deploy','environment'):
            self.assertIn(key,nodes);self.assertEqual(nodes[key]['compartment_id'],'c')
        self.assertNotIn('NEVER-STORE',json.dumps(s))
        self.assertEqual(nodes['bucket']['identity_status'],'ocid')
        for key,model in [('repo','RepositorySummary'),('build','BuildPipelineSummary'),('deploy','DeployPipelineSummary'),('environment','DeployEnvironmentSummary')]:
            e=next(e for e in edges if e['source']==key and e['kind']=='project_id')
            self.assertEqual(e['target'],'project');self.assertEqual(e['evidence'],model+'.project_id')
        for name,args,kw in requests:
            if name.startswith(('object_storage_','artifacts_','devops_')):
                method=name[len('object_storage_'):] if name.startswith('object_storage_') else name.split('_',1)[1]
                self.assertTrue(method.startswith(('get_','list_')))
                if 'list_' in name:self.assertEqual(kw['compartment_id'],'c')
        self.assertFalse(any(e['source'] in ('bucket','registry') for e in edges))
    def test_denied_empty_and_namespace_dependency_are_distinct(self):
        for api in self.responses():
            s,_=self.collect(fail=api)
            service,method=api.split('_',1) if not api.startswith('object_storage_') else ('object_storage',api[len('object_storage_'):])
            entry=next(c for c in s['coverage'] if c['service']==service and c['api']==method)
            self.assertEqual(entry['status'],'permission_denied');self.assertNotIn('count',entry)
        s,requests=self.collect(fail='object_storage_get_namespace')
        self.assertFalse(any(n=='object_storage_list_buckets' for n,a,k in requests))
        self.assertTrue(any(c['api']=='list_buckets' and c['status']=='skipped' for c in s['coverage']))
        s,_=self.collect(extra={'devops_list_projects':[],'artifacts_list_container_repositories':[]})
        self.assertTrue(any(c['service']=='devops' and c['api']=='list_projects' and c.get('count')==0 for c in s['coverage']))
        # A denied project list must not suppress independently accessible children.
        s,_=self.collect(fail='devops_list_projects');nodes,edges=graph(s)
        self.assertIn('repo',nodes);self.assertTrue(any(e['target']=='unknown:project' for e in edges))
    def test_bucket_detail_denied_keeps_stable_explicit_summary_identity(self):
        a,_=self.collect(fail='object_storage_get_bucket');b,_=self.collect(fail='object_storage_get_bucket')
        ar=next(r for r in a['resources'] if r['kind']=='object_storage_bucket')
        br=next(r for r in b['resources'] if r['kind']=='object_storage_bucket')
        self.assertEqual(ar,br);self.assertEqual(ar['identity_status'],'list_summary')
        self.assertTrue(ar['id'].startswith('bucket-summary:'));self.assertEqual(ar['name'],'Synthetic Bucket')
        self.assertNotIn('namespace',ar)
    def test_native_editable_icons_compartment_parent_and_exact_replay(self):
        s,_=self.collect();before=copy.deepcopy(s);d=prepare_display(s);xml=render(d,detail_pages=True);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        for key in ('bucket','registry','project','repo','build','deploy','environment'):
            self.assertEqual(cells[key].get('parent'),cells['v'].get('parent'))
            self.assertIn(key+'-icon',cells)
        self.assertNotIn('layout-osn',cells)
        self.assertEqual(ICONS['object_storage_bucket'],11);self.assertEqual(ICONS['container_repository'],75)
        self.assertEqual(ICONS['devops_project'],85);self.assertEqual(render(d,detail_pages=True),xml)
        self.assertEqual(s,before)
    def test_regional_only_and_bad_network_fields_do_not_create_network_links(self):
        s,_=self.collect();s['resources']=[r for r in s['resources'] if r['id'] in ('bucket','registry','project','repo','build','deploy','environment')]
        for r in s['resources']:r.update(subnet_id='bogus',vcn_id='bogus',nsg_ids=['bogus'])
        self.assertTrue(all(e['kind']=='project_id' for e in graph(s)[1]))
        self.assertEqual(len(s['resources']),7)
        d=prepare_display(s);xml=render(d);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertTrue(all(cells[r['id']].get('parent').startswith('layout-compartment-') for r in s['resources']))
        self.assertNotIn('bogus',json.dumps(graph(s)[1]))
        doc=E.fromstring(xml);doc.find("diagram/mxGraphModel/root/mxCell[@id='bucket']").set('parent','layout-region')
        with self.assertRaisesRegex(ValueError,'Regional resource must remain'):
            validate(E.tostring(doc,encoding='unicode'),d)
    def test_actual_compartment_membership_overrides_cross_compartment_project_relation(self):
        s,_=self.collect()
        for r in s['resources']:
            if r['id']=='repo':r['compartment_id']='other'
        d=prepare_display(s);xml=render(d,detail_pages=True);validate(xml,d)
        cells={c.get('id'):c for c in E.fromstring(xml).find('diagram/mxGraphModel/root')}
        self.assertNotEqual(cells['repo'].get('parent'),cells['project'].get('parent'))
        relation=next(e for e in graph(s)[1] if e['source']=='repo' and e['kind']=='project_id')
        self.assertEqual(relation['target'],'project')

    def test_redacted_export_preserves_original_snapshot(self):
        s,_=self.collect();before=copy.deepcopy(s);d=prepare_display(s,redact=True);xml=render(d);validate(xml,d)
        for name in ('Synthetic Bucket','Synthetic Registry','Synthetic Code'):self.assertNotIn(name,xml)
        self.assertEqual(s,before)
    def test_actual_sdk_paginated_list_requests_are_get_and_compartment_scoped(self):
        cases=[('object_storage','ObjectStorageClient','list_buckets',{'namespace_name':'synthetic','compartment_id':'c'},lambda ids:[oci.object_storage.models.BucketSummary(name=k) for k in ids]),
               ('artifacts','ArtifactsClient','list_container_repositories',{'compartment_id':'c'},lambda ids:oci.artifacts.models.ContainerRepositoryCollection(items=[oci.artifacts.models.ContainerRepositorySummary(id=k) for k in ids])),
               ('devops','DevopsClient','list_projects',{'compartment_id':'c'},lambda ids:oci.devops.models.ProjectCollection(items=[oci.devops.models.ProjectSummary(id=k) for k in ids]))]
        for method,model in [('list_repositories','Repository'),('list_build_pipelines','BuildPipeline'),('list_deploy_pipelines','DeployPipeline'),('list_deploy_environments','DeployEnvironment')]:
            def make(ids,model=model):
                return getattr(oci.devops.models,model+'Collection')(items=[getattr(oci.devops.models,model+'Summary')(id=k) for k in ids])
            cases.append(('devops','DevopsClient',method,{'compartment_id':'c'},make))
        for service,cls,method,kwargs,collection in cases:
            with self.subTest(service=service):
                client=getattr(getattr(oci,service),cls).__new__(getattr(getattr(oci,service),cls))
                client.retry_strategy=oci.retry.NoneRetryStrategy();client.circuit_breaker_callback=None
                client.base_client=Mock();client.base_client.get_preferred_retry_strategy.return_value=None;pages=[]
                def transport(**request):
                    self.assertEqual(request['method'],'GET');self.assertEqual(request['query_params']['compartmentId'],'c')
                    pages.append(request['query_params'].get('page'))
                    return oci.response.Response(200,{'opc-next-page':'next'} if len(pages)==1 else {},collection(['a' if len(pages)==1 else 'b']),None)
                client.base_client.call_api=transport
                result=oci.pagination.list_call_get_all_results(getattr(client,method),**kwargs).data
                self.assertEqual(pages,[None,'next']);self.assertEqual(len(result if isinstance(result,list) else result.items),2)
