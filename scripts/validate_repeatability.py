"""Repeat fresh synthetic AI designs; preserve failures as part of the evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_scenarios import CASES,run_matrix


def run_repetitions(output,case,repeats=3,*,ai=True,timeout=600):
    if not 2<=repeats<=10:raise ValueError('repeats must be between 2 and 10')
    if case not in CASES or timeout<=0:raise ValueError('invalid repeat configuration')
    output=Path(output).expanduser().resolve();output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for n in range(1,repeats+1):
        directory=output/f'run-{n}'
        run_matrix(directory,[case],ai=ai,timeout=timeout)
        row=json.loads((directory/'matrix-report.json').read_text())[0]
        rows.append({'run':n,**row})
        hashes={r['snapshot_hash'] for r in rows}
        report={'case':case,'mode':'fresh_ai' if ai else 'diagnostic_only',
                'requested_runs':repeats,'completed_runs':len(rows),'same_snapshot':len(hashes)==1,
                'quality_clear_runs':sum(r['status']=='accepted' for r in rows),
                'failed_runs':sum(r['status']=='failed' for r in rows),
                'needs_review_runs':sum(r['status']=='needs_review' for r in rows),
                'runs':rows,'spread':{}}
        measurements={}
        for r in rows:
            q=r.get('layout_quality')
            if q:
                for key,value in {'loss':q['loss'],**q['metrics']}.items():measurements.setdefault(key,[]).append(value)
        report['spread']={key:{'min':min(values),'max':max(values),'mean':round(sum(values)/len(values),6)} for key,values in measurements.items()}
        (output/'repeatability-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',choices=CASES,default='fastconnect')
    parser.add_argument('--repeats',type=int,choices=range(2,11),default=3)
    parser.add_argument('--no-ai',action='store_true',help='Diagnostic only; cannot demonstrate AI consistency')
    parser.add_argument('--skill-timeout',type=int,default=600)
    args=parser.parse_args()
    if args.skill_timeout<=0:parser.error('--skill-timeout must be positive')
    report=run_repetitions(args.output,args.case,args.repeats,ai=not args.no_ai,timeout=args.skill_timeout)
    print('Completed: '+str(report['completed_runs'])+'; quality clear: '+str(report['quality_clear_runs'])+
          '; needs review: '+str(report['needs_review_runs'])+'; failed: '+str(report['failed_runs']))
    return int(not report['same_snapshot'] or bool(report['failed_runs']+report['needs_review_runs']))


if __name__=='__main__':sys.exit(main())
