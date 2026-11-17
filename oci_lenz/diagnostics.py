"""Read-only prerequisite checks. Never reads OCI profiles or prints secrets."""
from importlib.metadata import version,PackageNotFoundError
import os
import shutil
import subprocess
import sys
from .draw import ROOT,find_drawio


def environment_report(provider='codex',model=None,require_png=True):
    checks=[]
    def add(name,status,hint='',**extra):
        checks.append(dict(name=name,status=status,**({'hint':hint} if hint and status not in ('ok','available','configured') else {}),**extra))
    add('python','ok' if sys.version_info>=(3,10) else 'unsupported',version='.'.join(map(str,sys.version_info[:3])))
    try:add('oci_sdk','ok',version=version('oci'))
    except PackageNotFoundError:add('oci_sdk','missing','Install the project dependencies with python -m pip install .')
    for name,path in [('stencils','assets/oci/library.xml'),('drawio_skill','.agents/skills/drawio/SKILL.md'),('oci_skill','.agents/skills/oci-drawio/SKILL.md'),('reference_image','assets/reference/layout-guide.png')]:
        add(name,'ok' if (ROOT/path).is_file() else 'missing','Reinstall OCI-Lenz if packaged assets are missing.')
    if require_png:
        add('drawio','available' if find_drawio() else 'missing','Install Draw.io Desktop; set DRAWIO_BIN when it is outside standard locations.')
        if os.name=='posix' and sys.platform!='darwin' and not os.environ.get('DISPLAY'):
            add('headless_display','available' if shutil.which('xvfb-run') else 'missing','Headless Linux PNG export requires Xvfb or DISPLAY.')
    else:add('drawio','skipped','XML-only check; PNG export has not been checked.')
    if provider=='codex':
        binary=shutil.which('codex');add('codex','available' if binary else 'missing','Install Codex CLI and run codex login with your own account.')
        if binary:
            try:
                result=subprocess.run([binary,'login','status'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
                add('codex_login','available' if result.returncode==0 else 'unavailable','Run codex login; this checks local login status, not model access or usage limits.')
            except (OSError,subprocess.TimeoutExpired):add('codex_login','unavailable','Check codex login status locally.')
    elif provider=='openai':
        add('api_key','configured' if os.environ.get('OPENAI_API_KEY') else 'missing','Provide OPENAI_API_KEY through your local runtime secret manager.')
        add('api_model','configured' if model else 'missing','Select a vision/structured-output model with --model or OCI_LENZ_AI_MODEL.')
    else:add('ai_provider','unsupported','Choose codex or openai.')
    return {'ready':all(c['status'] in ('ok','available','configured','skipped') for c in checks),'checks':checks,'scope':'Prerequisites only; no OCI access or AI model request was performed.'}
