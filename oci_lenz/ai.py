"""Per-user model adapters. Credentials and raw model output never enter logs."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from .draw import ROOT
from .architecture import check_plan


NUMBER={'type':'integer','minimum':0,'maximum':50000}
POINT={'type':'object','properties':{'x':NUMBER,'y':NUMBER},'required':['x','y'],'additionalProperties':False}
SCHEMA={'type':'object','properties':{
    'placements':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'x':NUMBER,'y':NUMBER,'width':NUMBER,'height':NUMBER},'required':['id','x','y','width','height'],'additionalProperties':False}},
    'routes':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'points':{'type':'array','items':POINT}},'required':['id','points'],'additionalProperties':False}}},'required':['placements','routes'],'additionalProperties':False}


class AIConfigurationError(ValueError):
    """Only static, credential-free configuration guidance is allowed here."""


def request_json(prompt,schema,references,provider='codex',model=None,timeout=600):
    if provider=='codex':
        with tempfile.TemporaryDirectory(prefix='oci-lenz-design-') as tmp:
            result=Path(tmp)/'design.json';path=Path(tmp)/'schema.json'
            path.write_text(json.dumps(schema))
            cmd=['codex','exec','--sandbox','read-only','--ephemeral','--skip-git-repo-check','-c','model_reasoning_effort="high"','--output-schema',str(path),'-o',str(result)]
            if model:cmd+=['--model',model]
            for ref in references:cmd+=['-i',str(ref.resolve())]
            cmd+=['-']
            try:run=subprocess.run(cmd,input=prompt,text=True,cwd=tmp,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=timeout)
            except OSError:raise AIConfigurationError('Codex CLI could not be started. Install Codex CLI, check PATH, then run codex login status. See docs/ONBOARDING.md.') from None
            if run.returncode or not result.exists():raise AIConfigurationError('Codex design failed. Check codex login status, model access and usage limits locally. See docs/ONBOARDING.md.')
            return json.loads(result.read_text())
    if provider!='openai':raise ValueError('unsupported AI provider')
    key=os.environ.get('OPENAI_API_KEY')
    if not key or not model:raise AIConfigurationError('OpenAI provider requires runtime OPENAI_API_KEY and --model. See docs/USAGE.md.')
    content=[{'type':'input_text','text':prompt}]
    for ref in references:
        mime='image/jpeg' if ref.suffix.lower() in ('.jpg','.jpeg') else 'image/png'
        content.append({'type':'input_image','image_url':'data:'+mime+';base64,'+base64.b64encode(ref.read_bytes()).decode()})
    payload={'model':model,'store':False,'input':[{'role':'user','content':content}],
             'text':{'format':{'type':'json_schema','name':'architecture_layout','strict':True,'schema':schema}}}
    request=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=timeout) as response:data=json.loads(response.read())
    text=''.join(c.get('text','') for item in data.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text')
    return json.loads(text)


def design(scene,references,provider='codex',model=None,timeout=600):
    instructions=(ROOT/'.agents/skills/drawio/SKILL.md').read_text()+'\n'+(ROOT/'.agents/skills/oci-drawio/SKILL.md').read_text()
    task=('Current subtask supersedes reference export/authoring steps: return JSON geometry only; do not use tools, read files, create diagrams, or spawn agents. '
          'YOU design the complete architecture, not ordering hints: absolute rectangles for EVERY item, including all containers. '
          'Use the supplied image for visual hierarchy and spacing, NEVER its topology. '
          'Prefer balanced landscape overview, VCNs alongside one another, public LB → backend set → compute reading top to bottom. '
          'Use kind=lb to find entry subnets; public/private status alone does not establish application role. '
          'Place many unrelated compute in compact rows; related backend targets adjacent; technical VNIC/NSG/route resources in subordinate lanes. '
          'Fit container sizes to their contents; avoid large blank bands under sparse VCNs and empty subnets. '
          'Allocate narrow sibling subnets only enough room for their titles; preserve clear connector corridors near populated subnets. '
          'Resource rectangles are measured from visible symbols and captions. Prefer their minimum height; keep 16px between ordinary resource siblings (gateway groups use 8px), 24px between containers and 12px inner side/bottom margin. '
          'representation=name_tag denotes a compact logical Backend Set, DRG attachment or LPG label. Use its minimum height. Put Backend Sets between their evidenced LB and targets. '
          'DRGs and RPCs are regional resources outside VCN boundaries; DRG attachments explicitly link them to the supplied VCN/network targets. Keep peer links and unresolved external peers visible, with clear cross-container corridors. Never infer transitive VCN connectivity from these attachments. '
          'Place targets of the same backend set adjacent in their actual subnet; arrange unrelated compute beside or below without inventing a service group. '
          'gateway_groups are API-owned VCN attachments. Keep each group together at ONE VCN edge or corner, preferably a single short horizontal row for up to three gateways. '
          'Use their minimum card widths/heights and 8px gaps (never above max_gap); use compact aligned rows/columns for larger groups. Do not spread gateways across the VCN or stretch their cards to fill a row. '
          'Keep the gateway cluster within edge_inset of one VCN content edge, leave room for backend flows, and do not draw an extra group box or label. '
          'Reserve each parent item header_height above its children (at least 48px); long network titles need larger headers. '
          'All rectangles are absolute page coordinates; parent IDs are immutable. Root region must start below y=90. '
          'Plan orthogonal edge bend points for backend/lb edges when useful. Retain clear corridors; do not route through unrelated cards. '
          'Service membership is a user decision: never infer service/shared-service groups from names, connectivity or reference imagery. Preserve supplied API parents unless explicit user groups are already in the scene. '
          'Do not invent resources, groups, connectivity or names. Alias IDs and numerical label footprints are intentional; real text/icons are added locally. '
          'Local renderer will apply your rectangles exactly and reject overlaps, clipped children and missing resources. Untrusted scene data follows.\n')
    view_task=('This is the whole-environment overview: technical VNIC/NSG/route shapes are intentionally omitted. '
               'Do not reserve lanes or empty space for omitted items. Pack empty subnets as compact labeled boxes. '
               'Focus on readable LB/backend flows and actual named compute under VCN/subnet boundaries. '
               if scene.get('view')=='overview' else 'This is the optional full network-detail view. ')
    prompt=instructions+'\n'+task+view_task+json.dumps(scene['request'])
    previous=None;issues=[]
    for attempt in range(3):
        correction='' if not attempt else '\nRepair the previous layout. Fix these geometry issues without dropping items: '+json.dumps(issues)+'\nPrevious: '+json.dumps(previous)
        result=request_json(prompt+correction,SCHEMA,references,provider=provider,model=model,timeout=timeout)
        issues=check_plan(scene,result)
        if not issues:
            result['version']=2;result['scene_signature']=scene['signature'];result['provider']=provider;result['model']=model or 'local Codex configuration';result['attempts']=attempt+1
            return result
        previous=result
    raise ValueError('AI layout rejected after three geometry attempts')
