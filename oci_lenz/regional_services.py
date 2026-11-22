"""Compartment-owned control-plane metadata; never fetch service contents."""
import hashlib
from types import SimpleNamespace

DEVOPS_MODELS={
    'devops_repository':'RepositorySummary',
    'devops_build_pipeline':'BuildPipelineSummary',
    'devops_deploy_pipeline':'DeployPipelineSummary',
    'devops_deploy_environment':'DeployEnvironmentSummary',
}
REGIONAL_KINDS=frozenset(('file_system','nosql_table','object_storage_bucket','container_repository','devops_project',*DEVOPS_MODELS))


def collect_regional_services(call,add,snapshot,compartment):
    namespace=call('object_storage','get_namespace')
    if isinstance(namespace,str) and namespace:
        for bucket in call('object_storage','list_buckets',namespace_name=namespace,compartment_id=compartment) or []:
            detail=call('object_storage','get_bucket',namespace_name=namespace,bucket_name=bucket.name)
            bucket_id=getattr(detail,'id',None)
            # ListBuckets has no OCID. Preserve visible summary on GetBucket denial
            # with an explicitly non-OCID stable identity, never invent an OCID.
            if not bucket_id:
                identity=json_identity(snapshot['scope']['region'],namespace,bucket.name)
                bucket_id='bucket-summary:'+hashlib.sha256(identity).hexdigest()
            obj=SimpleNamespace(id=bucket_id,name=bucket.name,compartment_id=getattr(bucket,'compartment_id',None) or compartment)
            add(obj,'object_storage_bucket',deployment_scope='regional',identity_status='ocid' if getattr(detail,'id',None) else 'list_summary')
    else:
        snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,
            'service':'object_storage','api':'list_buckets','status':'skipped','reason':'namespace_unavailable'})
    for repo in call('artifacts','list_container_repositories',compartment_id=compartment) or []:
        add(repo,'container_repository',compartment_id=getattr(repo,'compartment_id',None) or compartment,
            lifecycle_state=getattr(repo,'lifecycle_state',None),deployment_scope='regional')
    for api,kind in [('list_projects','devops_project'),('list_repositories','devops_repository'),
                     ('list_build_pipelines','devops_build_pipeline'),('list_deploy_pipelines','devops_deploy_pipeline'),
                     ('list_deploy_environments','devops_deploy_environment')]:
        # Query each kind independently in the selected compartment: a project
        # list failure must not hide child resources the principal can inspect.
        for obj in call('devops',api,compartment_id=compartment) or []:
            fields={'compartment_id':getattr(obj,'compartment_id',None) or compartment,
                    'lifecycle_state':getattr(obj,'lifecycle_state',None),'deployment_scope':'regional'}
            if kind in DEVOPS_MODELS:fields['project_id']=getattr(obj,'project_id',None)
            if kind=='devops_deploy_environment':fields['environment_type']=getattr(obj,'deploy_environment_type',None)
            add(obj,kind,**fields)


def json_identity(*parts):
    import json
    return json.dumps(parts,ensure_ascii=False,separators=(',',':')).encode()
