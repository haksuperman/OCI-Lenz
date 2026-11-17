"""Generate and verify a synthetic topology matrix; never performs OCI collection."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import subprocess
import sys
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from oci_lenz.synthetic import SCENARIOS
from oci_lenz.model import sample,graph
from oci_lenz.display import prepare_display
from oci_lenz.draw import render,validate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',action='append',choices=SCENARIOS)
    parser.add_argument('--ai',action='store_true',help='Use configured Codex provider; default uses deterministic diagnostic seed')
    args=parser.parse_args();args.output=args.output.expanduser().resolve();args.output.mkdir(parents=True,exist_ok=True)
    report=[]
    for case in args.case or SCENARIOS:
        out=args.output/case;out.mkdir(exist_ok=True)
        s=sample(case);(out/'snapshot.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
        cmd=[sys.executable,'-m','oci_lenz','draw','--snapshot',str(out/'snapshot.json'),'--output',str(out)]
        if not args.ai:cmd.append('--no-ai')
        print('Generating synthetic case: '+case,flush=True)
        subprocess.run(cmd,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        xml=(out/'architecture.drawio').read_text();display=prepare_display(s);validate(xml,display)
        layout=json.loads((out/'skill-layout.json').read_text()) if args.ai else None
        if render(display,layout,style='architecture')!=xml:raise ValueError('synthetic replay differs')
        cells=list(E.fromstring(xml).find('diagram').iter('mxCell'))
        if not set(graph(s)[0])<={c.get('id') for c in cells}:raise ValueError('missing synthetic resource')
        pngs={}
        for name in ('architecture.png','information-index.png'):
            data=(out/name).read_bytes()
            if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('invalid synthetic PNG')
            pngs[name]=list(struct.unpack('>II',data[16:24]))
        review=json.loads((out/'visual-review.json').read_text())
        report.append({'case':case,'resources':dict(Counter(r['kind'] for r in s['resources'])),
                       'graph_valid':True,'replay_equal':True,'png_dimensions':pngs,
                       'visual_review_status':review['status'],'ai_invoked':args.ai})
        (args.output/'matrix-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Validated synthetic cases: '+str(len(report)),flush=True)


if __name__=='__main__':main()
