import argparse,hashlib,json,subprocess,sys,os
from pathlib import Path
from .model import sample,graph
from .synthetic import SCENARIOS
from .draw import render,validate,export,ROOT
from .display import prepare_display
from .ai import AIConfigurationError
from .visual_review import VisualReviewTimeout
from .architecture import LayoutFormatError

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

class SkillLayoutTimeout(TimeoutError):
    """Safe marker; never retain child command or output in diagnostics."""

def positive_seconds(value):
    seconds=int(value)
    if seconds<=0:raise argparse.ArgumentTypeError('timeout must be positive')
    return seconds

def skill_layout(snapshot,output,references,timeout=600,provider='codex',model=None,detail_pages=False):
    from .architecture import make_scene
    from .ai import design
    try:
        views={}
        for view in (('overview','detail') if detail_pages else ('overview',)):
            print('OCI-Lenz: designing '+view+' layout.',file=sys.stderr,flush=True)
            views[view]=design(make_scene(snapshot,view=view),references,provider=provider,model=model,timeout=timeout)
        layout={'version':3,**views}
    except (subprocess.TimeoutExpired,TimeoutError):raise SkillLayoutTimeout('AI layout timed out') from None
    save(output/'skill-layout.json',layout)
    return layout


def main():
    p=argparse.ArgumentParser(prog='oci-lenz');sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('sample');a.add_argument('--output',type=Path,required=True);a.add_argument('--scenario',choices=('basic','overview','service-map',*SCENARIOS),default='basic')
    a=sub.add_parser('collect');a.add_argument('--profile',required=True);a.add_argument('--region',required=True);a.add_argument('--compartment-id',required=True,action='append');a.add_argument('--config-file');a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('draw');a.add_argument('--snapshot',type=Path,required=True);a.add_argument('--references',type=Path);a.add_argument('--output',type=Path,required=True);a.add_argument('--reuse-layout',type=Path);a.add_argument('--style',choices=('architecture',),default='architecture');a.add_argument('--no-ai',action='store_true',help='Deterministic helper only; does not call the skill');a.add_argument('--no-png',action='store_true');a.add_argument('--skill-timeout',type=positive_seconds,default=600,help='AI timeout per attempt in seconds (default: 600)');a.add_argument('--redact',action='store_true',help='Sharing only: hide resource names and IPs in visible labels');a.add_argument('--ai-provider',choices=('codex','openai'),default=os.environ.get('OCI_LENZ_AI_PROVIDER','codex'));a.add_argument('--model',default=os.environ.get('OCI_LENZ_AI_MODEL'))
    a.add_argument('--detail-pages',action='store_true',help='Optional separate VCN network-detail pages (architecture style)')
    a.add_argument('--groups',type=Path,help='Local explicit service-group JSON; never inferred from names')
    a.add_argument('--review-rounds',type=int,choices=(0,1,2),default=1,help='Visual revision budget for fresh AI/PNG generation (default: 1)')
    a=sub.add_parser('doctor',help='Check local prerequisites without OCI calls or model requests')
    a.add_argument('--ai-provider',choices=('codex','openai'),default=os.environ.get('OCI_LENZ_AI_PROVIDER','codex'))
    a.add_argument('--model',default=os.environ.get('OCI_LENZ_AI_MODEL'))
    a.add_argument('--no-png',action='store_true',help='Check XML-only prerequisites')
    a.add_argument('--json',action='store_true',help='Print credential-free structured results')
    args=p.parse_args()
    try:
        if args.command=='doctor':
            from .diagnostics import environment_report
            report=environment_report(args.ai_provider,args.model,require_png=not args.no_png)
            if args.json:print(json.dumps(report,indent=2))
            else:
                for check in report['checks']:print(check['name']+': '+check['status']+(' — '+check['hint'] if check.get('hint') else ''))
                print(report.get('scope',''))
            if not report['ready']:raise SystemExit(2)
            return
        args.output.mkdir(parents=True,exist_ok=True,mode=0o700)
        if args.command=='sample':
            s=sample(args.scenario);s['relationships']=graph(s)[1];save(args.output/'snapshot.json',s);return
        if args.command=='collect':
            from .collect import collect
            snapshots=[collect(args.profile,args.region,c,args.config_file) for c in args.compartment_id]
            s=snapshots[0]
            s['scope']['compartments']=args.compartment_id
            for other in snapshots[1:]:
                s['resources'].extend(other['resources']);s['coverage'].extend(other['coverage'])
                s['scope'].setdefault('compartment_names',{}).update(other['scope'].get('compartment_names',{}))
                if not s['scope'].get('tenancy_name') and other['scope'].get('tenancy_name'):
                    s['scope']['tenancy_name']=other['scope']['tenancy_name']
            s['resources']=list({r['id']:r for r in s['resources']}.values())
            s['relationships']=graph(s)[1]
            save(args.output/'snapshot.json',s);save(args.output/'coverage.json',s['coverage']);return
        s=json.loads(args.snapshot.read_text());refs=[]
        if args.groups:
            groups=json.loads(args.groups.read_text())
            s.setdefault('presentation',{})['groups']=groups['groups'] if isinstance(groups,dict) else groups
        if args.references: refs=sorted(x for x in args.references.iterdir() if x.suffix.lower() in ('.png','.jpg','.jpeg'))
        elif args.style=='architecture':
            reference=ROOT/'assets/reference/layout-guide.png'
            if reference.exists():refs=[reference]
        safe=prepare_display(s,redact=args.redact)
        if not args.no_ai and not args.reuse_layout:
            print(f'OCI-Lenz: {args.ai_provider} layout started (timeout {args.skill_timeout}s per attempt).',file=sys.stderr,flush=True)
        layout=json.loads(args.reuse_layout.read_text()) if args.reuse_layout else (None if args.no_ai else skill_layout(safe,args.output,refs,timeout=args.skill_timeout,provider=args.ai_provider,model=args.model,detail_pages=args.detail_pages))
        # Operational diagrams retain actual names/IPs locally. Redaction is explicit.
        if layout: save(args.output/'skill-layout.json',layout)
        xml=render(safe,layout,style=args.style,detail_pages=args.detail_pages);validate(xml,safe)
        path=args.output/'architecture.drawio';path.write_text(xml)
        save(args.output/'coverage.json',s.get('coverage',[]))
        review_report={'status':'skipped','reason':'replay' if args.reuse_layout else ('no_ai' if args.no_ai else ('no_png' if args.no_png else 'disabled'))}
        if args.style=='architecture' and layout and not args.no_ai and not args.reuse_layout and not args.no_png and args.review_rounds:
            from .visual_review import review_design
            print('OCI-Lenz: rendered visual review started.',file=sys.stderr,flush=True)
            layout,review_report=review_design(safe,layout,refs,provider=args.ai_provider,model=args.model,timeout=args.skill_timeout,rounds=args.review_rounds)
            xml=render(safe,layout,style=args.style,detail_pages=args.detail_pages);validate(xml,safe)
            save(args.output/'skill-layout.json',layout);path.write_text(xml)
            if review_report['status']=='needs_review':print('OCI-Lenz: visual review needs attention; see visual-review.json.',file=sys.stderr,flush=True)
        if not args.reuse_layout or not (args.output/'visual-review.json').exists():save(args.output/'visual-review.json',review_report)
        if not args.no_png:
            print('OCI-Lenz: XML validated; PNG export started.',file=sys.stderr,flush=True)
            export(path)
        save(args.output/'validation.json',{'graph_valid':True,'style':args.style,'redacted':args.redact,'visual_review_status':review_report['status'],'ai_provider':args.ai_provider,'model':args.model or 'local Codex configuration','skill_invoked':not args.no_ai and not bool(args.reuse_layout),'reused_layout':bool(args.reuse_layout),'references':[{'name':r.name,'sha256':hashlib.sha256(r.read_bytes()).hexdigest()} for r in refs]})
        print(path.resolve())
    except LayoutFormatError:
        p.exit(1,'OCI-Lenz: saved layout format is retired. Regenerate without --reuse-layout; original Draw.io files remain editable.\n')
    except VisualReviewTimeout:
        p.exit(1,'OCI-Lenz: visual review timed out. Initial XML/layout are retained; retry with saved layout or --review-rounds 0.\n')
    except AIConfigurationError as exc:
        p.exit(1,str(exc)+'\n')
    except SkillLayoutTimeout:
        p.exit(1,'OCI-Lenz: Codex layout timed out. Retry with --skill-timeout 900; check codex login status. No automatic --no-ai fallback was used.\n')
    except subprocess.TimeoutExpired:
        p.exit(1,'OCI-Lenz: PNG export timed out. XML is retained; check Draw.io Desktop and retry with --reuse-layout pointing to skill-layout.json when present.\n')
    except Exception as exc:
        # Do not print exception bodies: SDK/child errors can contain secrets.
        p.exit(1,f'OCI-Lenz failed ({type(exc).__name__}); see docs/USAGE.md for local diagnostics.\n')
