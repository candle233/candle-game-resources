"""Eagle-first asset routing, local prompt TODOs and provenance checks. No paid calls."""
from __future__ import annotations
import argparse, html, json, re, sys, textwrap
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from uuid import uuid4
from common import ROOT, now, load, save, safe, sha
CATEGORIES=('music','sfx','model','image','vfx')
API='http://127.0.0.1:41595'
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('Eagle redirects disabled')
def eagle(endpoint,params=None,payload=None):
    if not endpoint.startswith('/api/') or '..' in endpoint:raise ValueError('Invalid Eagle endpoint')
    url=API+endpoint+('?' + urlencode(params) if params else '')
    raw=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    req=Request(url,data=raw,headers={'Content-Type':'application/json'},method='POST' if raw is not None else 'GET')
    # Do not send local library requests through environment-configured proxies.
    with build_opener(ProxyHandler({}),NoRedirect()).open(req,timeout=5) as response:
        raw=response.read(4_000_001)
    if len(raw)>4_000_000:raise ValueError('Eagle response too large')
    obj=json.loads(raw)
    if not isinstance(obj,dict) or obj.get('status')!='success':raise ValueError('Eagle reported failure')
    return obj

def items(result):
    v=result.get('data',[])
    if isinstance(v,dict):v=v.get('items',[])
    if not isinstance(v,list):raise ValueError('Unexpected Eagle list response')
    return [x for x in v if isinstance(x,dict)]

def make_todo(root,kind,name,brief,prompt):
    if kind not in CATEGORIES or not all(s.strip() for s in (name,brief,prompt)):raise ValueError('Type, name, brief and prompt required')
    ident=kind+'-'+uuid4().hex[:12];folder=root/'todo/assets'/ident;folder.mkdir(parents=True)
    lines=textwrap.wrap(prompt,width=68)[:14];body=''.join('<text x="36" y="'+str(150+30*i)+'">'+html.escape(line)+'</text>' for i,line in enumerate(lines))
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="680"><rect width="100%" height="100%" fill="#17212b"/><g fill="#eeeeee" font-family="sans-serif" font-size="22"><text x="36" y="50">'+html.escape(name)+'</text><text x="36" y="94">PROMPT / '+kind+' / '+ident+'</text>'+body+'<text x="36" y="640">Full prompt: Eagle annotation and request.md</text></g></svg>'
    (folder/'prompt-card.svg').write_text(svg,encoding='utf-8')
    (folder/'request.md').write_text('# '+name+'\n\n## Brief\n'+brief+'\n\n## Generation prompt\n'+prompt+'\n\n## Acceptance\nReview style, target format, rights and in-game result before importing.\n',encoding='utf-8')
    r={'schema_version':1,'id':ident,'type':kind,'name':name,'brief':brief,'prompt':prompt,'status':'awaiting_generation','eagle_status':'pending','eagle_id':None,'eagle_name':'AI-PROMPT-'+ident,'card':(folder/'prompt-card.svg').relative_to(root).as_posix(),'created_utc':now()}
    save(folder/'request.json',r);return r

def sync(root,r):
    path=safe(root,'todo/assets/'+r['id']+'/request.json')
    try:
        matches=[x for x in items(eagle('/api/item/list',{'keyword':r['eagle_name'],'limit':100})) if x.get('name')==r['eagle_name']]
        if len(matches)>1:raise ValueError('Duplicate Eagle items; reconcile manually')
        if len(matches)==1:
            r['eagle_status']='confirmed';r['eagle_id']=matches[0].get('id');save(path,r);return True
        if r['eagle_status'] in ('submitted_unconfirmed','uncertain'):
            raise ValueError('Earlier submission may have succeeded. Check Eagle manually before retrying to avoid duplicates')
        card=safe(root,r['card'])
        if not card.is_file():raise ValueError('Missing prompt card')
        r['eagle_status']='uncertain';save(path,r) # Persist BEFORE a potentially ambiguous network write.
        eagle('/api/item/addFromPath',payload={'path':str(card),'name':r['eagle_name'],'annotation':r['brief']+'\n\n'+r['prompt'],'tags':['AI-Asset-Prompt','TODO',r['type']]})
        r['eagle_status']='submitted_unconfirmed';save(path,r)
        matches=[x for x in items(eagle('/api/item/list',{'keyword':r['eagle_name'],'limit':100})) if x.get('name')==r['eagle_name']]
        if len(matches)==1:r['eagle_status']='confirmed';r['eagle_id']=matches[0].get('id')
        save(path,r);return r['eagle_status']=='confirmed'
    except Exception as exc:
        r['last_error']=str(exc);save(path,r);print('Eagle pending: '+str(exc),file=sys.stderr);return False

def check(root,release=False):
    # Normalize once: safe() resolves paths, so an unresolved root (for example
    # a Windows 8.3 temp path such as RUNNER~1) would not match rglob results.
    root=Path(root).resolve()
    reg=load(root/'harness/assets/registry.json');conf=load(root/'harness/project.json');errors=[];seen=set();ids=set()
    if reg.get('schema_version')!=1 or not isinstance(reg.get('assets'),list):raise ValueError('Invalid asset registry')
    for a in reg['assets']:
        rel=a.get('file','');ident=a.get('id','')
        if rel in seen or ident in ids:errors.append('Duplicate asset path/id: '+rel)
        seen.add(rel);ids.add(ident)
        if not ident:errors.append('Missing asset id')
        try:
            file=safe(root,rel)
            if not any(file.is_relative_to(safe(root,d)) for d in conf['asset_roots']):raise ValueError('Asset outside approved roots')
            if not file.is_file() or sha(file)!=a.get('sha256'):errors.append('Missing/changed asset: '+rel)
            # A file recorded as a prototype placeholder may not ship.
            if a.get('use')=='prototype_only' and not release:continue
            if a.get('review_status')!='approved' or not a.get('reviewer'):errors.append('Human rights review missing: '+rel)
            for key in ('origin','source','author','license'):
                if not isinstance(a.get(key),str) or not a[key].strip():errors.append('Missing '+key+': '+rel)
            ev=a.get('evidence_file','');evidence=safe(root,ev)
            if not ev or not evidence.is_file() or evidence.stat().st_size==0:errors.append('Missing license evidence: '+rel)
            if a.get('attribution_required') is not False and not a.get('attribution'):errors.append('Attribution requirement unresolved: '+rel)
            if release and a.get('use')!='shipping':errors.append('Not cleared for shipping: '+rel)
        except (OSError,ValueError) as exc:errors.append(str(exc))
    for base in conf['asset_roots']:
        directory=safe(root,base)
        if directory.is_dir():
            for f in directory.rglob('*'):
                if f.is_file() and f.suffix.lower() in conf['asset_extensions'] and f.relative_to(root).as_posix() not in seen:
                    errors.append('Unregistered media: '+f.relative_to(root).as_posix())
    print(json.dumps({'status':'FAIL' if errors else 'PASS','registered':len(reg['assets']),'errors':errors},indent=2));return 1 if errors else 0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('doctor');q=s.add_parser('search');q.add_argument('--query',required=True)
    q=s.add_parser('route');q.add_argument('--type',choices=CATEGORIES,required=True)
    q=s.add_parser('todo');q.add_argument('--type',choices=CATEGORIES,required=True);q.add_argument('--name',required=True);q.add_argument('--brief',required=True);q.add_argument('--prompt-file',type=Path,required=True);q.add_argument('--try-eagle',action='store_true')
    q=s.add_parser('sync');q.add_argument('--id',required=True)
    q=s.add_parser('check');q.add_argument('--release',action='store_true')
    a=p.parse_args(argv);root=a.root.resolve()
    try:
        if a.cmd=='doctor':print(json.dumps(eagle('/api/library/info'),ensure_ascii=False));return 0
        if a.cmd=='route':print(json.dumps(load(root/'harness/integrations.json')['asset_routes'][a.type],ensure_ascii=False,indent=2));return 0
        if a.cmd=='search':
            # Minimal fields avoid dumping private annotations and local library paths.
            data=items(eagle('/api/item/list',{'keyword':a.query,'limit':50}));print(json.dumps([{k:x.get(k) for k in ('id','name','ext','tags')} for x in data],ensure_ascii=False,indent=2));return 0
        if a.cmd=='todo':
            r=make_todo(root,a.type,a.name,a.brief,a.prompt_file.read_text(encoding='utf-8-sig'))
            ok=sync(root,r) if a.try_eagle else True
            print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if ok else 2
        if a.cmd=='sync':
            if not re.fullmatch(r'(music|sfx|model|image|vfx)-[0-9a-f]{12}',a.id):raise ValueError('Invalid TODO id')
            r=load(safe(root,'todo/assets/'+a.id+'/request.json'));return 0 if sync(root,r) else 2
        return check(root,a.release)
    except Exception as exc:print('ERROR: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
