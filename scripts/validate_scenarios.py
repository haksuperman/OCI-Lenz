"""Generate and verify synthetic topology cases; never performs OCI collection."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
import xml.etree.ElementTree as E
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from oci_lenz.synthetic import SCENARIOS
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate

CASES=('basic','overview',*SCENARIOS)
ARTIFACTS=('snapshot.json','coverage.json','architecture.drawio','architecture.png',
           'information-index.png','visual-review.json','validation.json')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_png(path):
    """Check complete PNG payload/CRC and exclude embedded XML/text metadata."""
    data=path.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('invalid synthetic PNG')
    pos=8;dimensions=None;compressed=[];ended=False;pixel_format=None
    while pos+12<=len(data):
        size=int.from_bytes(data[pos:pos+4],'big');kind=data[pos+4:pos+8]
        end=pos+12+size
        if end>len(data):raise ValueError('truncated synthetic PNG')
        payload=data[pos+8:pos+8+size]
        if zlib.crc32(kind+payload)!=int.from_bytes(data[pos+8+size:end],'big'):
            raise ValueError('corrupt synthetic PNG')
        if kind in (b'tEXt',b'zTXt',b'iTXt',b'eXIf'):raise ValueError('PNG metadata forbidden')
        if kind==b'IHDR':
            if pos!=8 or size!=13:raise ValueError('invalid PNG header')
            width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',payload)
            if not width or not height or compression or filtering or interlace:
                raise ValueError('unsupported PNG encoding')
            dimensions=[width,height];pixel_format=(depth,color)
        elif kind==b'IDAT':compressed.append(payload)
        elif kind==b'IEND':
            ended=size==0 and end==len(data);break
        pos=end
    if not dimensions or not compressed or not ended:raise ValueError('incomplete PNG')
    depth,color=pixel_format;channels={0:1,2:3,3:1,4:2,6:4}.get(color)
    if channels is None or depth not in (1,2,4,8,16):raise ValueError('invalid PNG color')
    try:pixels=zlib.decompress(b''.join(compressed))
    except zlib.error:raise ValueError('invalid PNG pixels') from None
    stride=1+(dimensions[0]*channels*depth+7)//8
    if len(pixels)!=stride*dimensions[1] or any(pixels[i]>4 for i in range(0,len(pixels),stride)):
        raise ValueError('invalid PNG scanlines')
    return dimensions


def verify_case(out,snapshot,ai):
    """Always validate current artifacts, including on resume; do not call a model."""
    xml=(out/'architecture.drawio').read_text();display=prepare_display(snapshot)
    validate(xml,display)
    layout=json.loads((out/'skill-layout.json').read_text()) if ai else None
    if render(display,layout,style='architecture')!=xml:raise ValueError('synthetic replay differs')
    cells=list(E.fromstring(xml).find('diagram').iter('mxCell'))
    if not set(graph(snapshot)[0])<={c.get('id') for c in cells}:raise ValueError('missing synthetic resource')
    if json.loads((out/'coverage.json').read_text())!=snapshot['coverage']:raise ValueError('coverage differs')
    pngs={name:inspect_png(out/name) for name in ('architecture.png','information-index.png')}
    review=json.loads((out/'visual-review.json').read_text())
    provenance=json.loads((out/'validation.json').read_text())
    if ai and (provenance.get('skill_invoked') is not True or provenance.get('reused_layout') is not False):
        raise ValueError('fresh AI provenance required')
    by_id={c.get('id'):c for c in cells}
    nodes,edges=graph(snapshot)
    labels=[k for k,c in by_id.items() if k in nodes and c.get('visible')!='0' and 'ociNativeLabel=1;' in c.get('style','')]
    files=(*ARTIFACTS,'skill-layout.json') if ai else ARTIFACTS
    return {'graph_valid':True,'replay_equal':True,'png_dimensions':pngs,
            'graph_nodes':len(nodes),'evidence_edges':len(edges),'native_resource_labels':len(labels),
            'official_vector_groups':sum(k+'-icon' in by_id for k in labels),
            'visual_review_status':review['status'],
            'artifact_hashes':{name:digest((out/name).read_bytes()) for name in files}}


def run_matrix(output,cases,ai=False,resume=False,timeout=900):
    output=Path(output).expanduser().resolve();output.mkdir(parents=True,exist_ok=True)
    path=output/'matrix-report.json'
    previous={r['case']:r for r in json.loads(path.read_text())} if resume and path.exists() else {}
    report=[]
    for case in cases:
        if case not in CASES:raise ValueError('unknown synthetic case')
        out=output/case;out.mkdir(exist_ok=True)
        s=sample(case);encoded=(json.dumps(s,ensure_ascii=False,indent=2)+'\n').encode()
        record={'case':case,'resources':dict(Counter(r['kind'] for r in s['resources'])),
                'snapshot_hash':digest(encoded),'ai_invoked':ai,'resumed':False}
        started=time.monotonic();old=previous.get(case,{})
        if (resume and old.get('status') in ('accepted','diagnostic_pass')
                and old.get('ai_invoked')==ai and old.get('snapshot_hash')==record['snapshot_hash']):
            try:
                verified=verify_case(out,s,ai)
                if verified['artifact_hashes']==old.get('artifact_hashes'):
                    record.update(verified,status=old['status'],resumed=True)
            except (OSError,ValueError,KeyError,E.ParseError):pass
        if not record['resumed']:
            (out/'snapshot.json').write_bytes(encoded)
            (out/'coverage.json').write_text(json.dumps(s['coverage'],indent=2)+'\n')
            cmd=[sys.executable,'-m','oci_lenz','draw','--snapshot',str(out/'snapshot.json'),
                 '--output',str(out),'--skill-timeout',str(timeout)]
            if not ai:cmd.append('--no-ai')
            print('Generating synthetic case: '+case,flush=True)
            try:
                subprocess.run(cmd,cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                record.update(verify_case(out,s,ai))
                record['status']=('accepted' if record['visual_review_status']=='accepted' else 'needs_review') if ai else 'diagnostic_pass'
            except Exception as error:
                # Raw model, SDK or process output must never enter the report.
                record.update(status='failed',error_type=type(error).__name__)
                if isinstance(error,subprocess.CalledProcessError):record['exit_code']=error.returncode
        record['elapsed_seconds']=round(time.monotonic()-started,2)
        report.append(record)
        # Persist each case so a later failure never loses completed evidence.
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(case+': '+record['status']+(' (resumed)' if record['resumed'] else ''),flush=True)
    return int(any(r['status'] not in ('accepted','diagnostic_pass') for r in report))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',action='append',choices=CASES)
    parser.add_argument('--ai',action='store_true',help='Use configured AI provider and visual review; default is diagnostic only')
    parser.add_argument('--resume',action='store_true',help='Revalidate and reuse unchanged passing artifacts without AI calls')
    parser.add_argument('--skill-timeout',type=int,default=900,help='AI timeout per attempt in seconds')
    args=parser.parse_args()
    if args.skill_timeout<=0:parser.error('--skill-timeout must be positive')
    return run_matrix(args.output,args.case or SCENARIOS,args.ai,args.resume,args.skill_timeout)


if __name__=='__main__':sys.exit(main())
