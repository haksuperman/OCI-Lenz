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
          'Edge WAF (kind=edge_waf) is a global edge service, never subnet-attached. Keep it outside VCN/subnet containers, near the endpoints of edge_protection arrows; arrows point from Edge WAF to observed targets or logical unresolved edge_origin tags. Never invent OCI membership or DNS mappings. '
          'WAF is NOT subnet-attached: keep each kind=waf outside all VCN/subnet boundaries, near its evidenced LB. Prefer flanking the VCN on the same icon row as the LB for a short horizontal protection arrow below container titles. Place WAF above only when a clear vertical corridor avoids every container header. waf_protection arrows point FROM WAF TO protected LB, never the reverse or to an invented gateway. '
          'Use kind=lb or kind=nlb to find entry subnets; public/private status alone does not establish application role. '
          'Place many unrelated compute in compact rows; related backend targets adjacent; technical VNIC/NSG/route resources in subordinate lanes. '
          'Expand actual containers as needed for readable arrows. Empty subnets without wires remain content-sized; reserved connection lanes are useful space. '
          'Apply design_policy consistently: measured leaf cards at minimum size (at most 8px extra), unrelated gaps 24px, connected gaps at least design_policy.connector_corridor=72px and network lanes 96px. Grow containers and the canvas, not icons or labels. '
          'Shrink each sparse subnet/VPN/group to its own child envelope and measured header; never stretch a sparse sibling to the height or width of a dense one. '
          'After reserving the actual branch paths, crop unused OUTER frame margins: boundary_padding=16px around children, measured header_height at the top, wire_boundary_clearance=8px around bends/side buses. Do not add a full 72/96px band at EVERY frame edge. Those corridors belong between connected objects/rows, not as universal padding. Preserve the shared branch tree, independent arrow landings and terminal shafts; crop empty borders before moving any leaf or compressing flow rows. '
          'Align ordinary sibling rows/columns within 8px. Keep an evidenced one-to-one LB/backend chain centered vertically inside its actual VCN; fanout may use aligned rows. '
          'Reserve 72px connection corridors and 96px network corridors, including side buses for multiple target rows. These are not avoidable whitespace. Leave 40px side margins where a branch bus needs to pass. '
          'Use compact columns sized to actual captions/counts; never expand a card or spread its children just to fill a boundary. No fixed page size is prescribed. '
          'Size sparse subnets for their titles plus actual connecting lanes; do not squeeze a populated subnet so that wires must weave through its cards. '
          'Resource rectangles are measured from visible symbols and captions. Prefer their minimum height; use 24px between unrelated siblings (gateway groups use 8px), at least 72px between connected cards or successive fanout rows, and enough parent padding for 32px side buses. Readable arrows take precedence over compact area. '
          'kind=oke_cluster uses the official OKE icon as an API ENDPOINT representation when its supplied parent is a subnet, never as physical control-plane VMs. Keep the exact parent: unknown endpoint placement falls back to an observed VCN or real compartment with icon/name only. Do not add Node Pool frames, worker duplicates, Pods, or OKE-to-worker/LB/gateway traffic arrows. Existing LB backends and route rules remain the only such connection evidence. Subnets marked as OKE Pod networks retain their actual names/CIDRs and immutable parents. '
          'File Storage file_system cards are compartment-owned outside VCNs; mount_target cards use their actual subnet/IP. file_export tags are visually anchored to a unique evidenced MountTarget export set; never invent client VM mounts. Functions applications use their supplied actual subnet membership; function cards near that application are logical ownership, not a claim about a specific invocation subnet. api_gateway cards use the observed subnet, api_deployment tags are near their exact gateway; api_backend arrows mean configured HTTP/Function targets, not verified traffic. Do not infer DNS, application grouping or unsupplied endpoints. '
          'goldengate_deployment represents the observed GoldenGate private endpoint in its exact API subnet, not all service internals. Keep its official icon and name/IP caption compact. Do not invent replication arrows, source/target databases, connections or a managed public load balancer. '
          'oci_cache is an actual managed Cache cluster using the official NoSQL symbol as reused for Cache in Oracle reference material; it stays inside its API subnet. Object Storage buckets, Container Registry repositories and all devops_* resources belong to their actual compartment OUTSIDE VCN/subnet boxes. Keep DevOps children near their API project; project_id lines mean membership, not execution/data flow. Do not invent SGW, image-pull, build-to-deploy or application lines. nosql_table is a distinct regional table resource inside its actual compartment OUTSIDE all VCN/subnet boxes, with no IP or inferred service-gateway/client links. postgresql_db_system and opensearch_cluster are actual managed service cards. Keep all in their supplied actual subnet when known; do not invent child nodes or client application links. '
          'backend_endpoint is a normal configured NLB backend address: keep each next to its exact Backend Set source using connection_readability.nearby, never in a remote unknown column. Its visual subnet anchor follows the Backend Set only; it is not confirmed VM placement. Retain its supplied backend arrow and label footprint; no VM icon or invented identity. '
          'Backend Set labels may include a locally owned backend status badge inside their measured footprint. Do not create separate unknown target cards or extra connectors for that badge; all hidden API endpoints remain in the native document. '
          'representation=name_tag denotes a compact logical Backend Set, LPG or IPSec tunnel label. Use its minimum height. Put Backend Sets between their evidenced LB and targets. '
          'DRGs and RPCs are regional resources outside VCN boundaries. Supplied direct DRG/network edges are API-evidenced display projections. Never infer VCN-to-VCN transit or traffic reachability. '
          'Attachment cards, names and frames are deliberately omitted from EVERY diagram page. Do not recreate them, add badges or invent group containers. '
          'network_groups are API relationship alignment hints, never service groups. Keep the supplied endpoints and edges. '
          'For local_peer, put LPG endpoints on facing sides INSIDE their actual VCNs with a short corridor. For remote_peer, put the peer or unknown endpoint immediately beyond that RPC. '
          'Each drg group has a mandatory direction contract: vcns entirely LEFT, ipsec_members RIGHT, remote_members ABOVE, with at least branch_gap. Apply separately per DRG; never rotate these sides. '
          'kind=ipsec is the actual VPN CONNECTION CONTAINER, with its existing API-owned tunnel children. Keep supplied parents immutable. Put tunnels in compact parallel rows INSIDE their own connection box, below header_height, preferably near its left side. '
          'Do not create a separate VPN connection card, extra grouping box or visible tunnel-to-parent ownership wire. Containment expresses that relationship. '
          'DRG enters the VPN box toward its evidenced tunnel children; the connection box links outward to its CPE. Keep DRG/CPE/RPC outside every VPN box. Keep VPN containers RIGHT of their DRG and CPE near the right edge outside its box. '
          'When fastconnect_members exists, keep that branch BELOW its DRG by at least branch_gap, separate from VPN on the right and RPC above. Lay out virtual circuits then their exact mapped physical endpoints in short horizontal rows below. '
          'If a DRG has exactly one virtual circuit, align that circuit center X with the DRG center X within 8px. If exactly one RPC is above a DRG, keep their center X aligned, including its single unknown peer when supplied. Multiple circuits/RPCs may use parallel branches; never stack them at identical positions. '
          'kind=cross_connect_group is an actual API-owned physical container: only its cross_connect child ports go inside. Virtual circuits, DRGs and CPEs stay outside that group. Preserve measured headers and immutable parents. '
          'Virtual circuits without a gateway (including public/provider-managed cases) must not be connected to a guessed DRG, CPE or on-premises network. Names and peering addresses never establish physical relationships. '
          'Reserve 96px connector corridors between network columns and between VCN boundaries; prefer short aligned paths, not long loops. '
          'Remote Peering leaves ABOVE the DRG; VCNs approach from LEFT; IPSec branches leave RIGHT. Leave unrelated CPEs separate. Do not infer a direct CPE-to-VCN link. '
          'Place targets of the same backend set adjacent in their actual subnet; arrange unrelated compute beside or below without inventing a service group. '
          'gateway_groups are API-owned VCN attachments. Keep each group together at ONE VCN edge or corner, preferably a single short horizontal row for up to three gateways. '
          'Use their minimum card widths/heights and 8px gaps (never above max_gap); use compact aligned rows/columns for larger groups. Do not spread gateways across the VCN or stretch their cards to fill a row. '
          'Keep the gateway cluster within edge_inset of one VCN content edge, leave room for backend flows, and do not draw an extra group box or label. '
          'Reserve each parent item header_height above its children (at least 48px); long network titles need larger headers. '
          'All rectangles are absolute page coordinates; parent IDs are immutable. Root region must start below y=90. '
          'connection_readability.nearby lists single-owner unresolved endpoints: keep each near its exact source, ideally within two card widths; never collect all unknowns in a remote page-wide column. Preserve actual parents. '
          'connection_readability.fanouts lists actual branches: prefer targets side by side on a common row. Use a separate side bus and 72px row corridors for multi-row targets; never stack a later target directly behind another with only a tiny gap. Reserve separate lanes for unrelated owners. Keep LB-to-Set-to-backend direction consistent. '
          'Put WAF outside the VCN near its exact target; keep ingress separate from outgoing backend lanes. Keep tunnel rows and branch order consistent, with separate DRG ingress/egress corridors. '
          'Prefer short straight orthogonal flow and a compact shared branch from the same evidenced owner. Do not add stair steps or page-wide detours solely to eliminate a clean perpendicular crossing: the local renderer uses native line jumps to distinguish independent wires. Keep crossovers away from icons, labels, endpoints and bends. Never overlap unrelated wires or treat crossing as connectivity. '
          'connection_readability.corridors applies to ALL supplied relationships, not only LB. Leave visible straight shafts at least 24px at arrowheads. Multiple independent owners entering one resource use separate landing lanes; do not merge them into one arrowhead. Plan orthogonal edge bend points when useful. Retain clear corridors; do not route through unrelated cards. '
          'connector_guides are mandatory native glyph-row contracts: source_anchor.y + source_offset must equal target_anchor.y + target_offset (null offset means half actual card height). '
          'Align the actual painted icons/content row, not card centers or container centers. Place the single child and its external peer on that row below the container header. Preserve original edge source/target; never add a child edge. '
          'Do not add doglegs to a clear collinear connection; only obstacles or genuine branching justify turns. '
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
        from .connector_rules import VERSION
        result['connector_rule_version']=VERSION
        issues=check_plan(scene,result)
        if not issues:
            result['version']=2;result['scene_signature']=scene['signature'];result['provider']=provider;result['model']=model or 'local Codex configuration';result['attempts']=attempt+1
            return result
        previous=result
    raise ValueError('AI layout rejected after three geometry attempts')
