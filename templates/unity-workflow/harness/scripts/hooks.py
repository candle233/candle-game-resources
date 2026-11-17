"""Shared Codex / ZCode hook handler; advisory context + limited guardrails only."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT, load, now
DANGEROUS=(r'\bgit\s+reset\s+--hard\b',r'\bgit\s+clean\s+-[a-z]*[fx]',r'\bgit\s+push\b.*(?:--force\b|\s-f\b)',r'\brm\s+(?:-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s',r'\bRemove-Item\b[^\n]*-Recurse\b[^\n]*-Force\b',r'\b(?:curl|wget)\b[^\n]*\|\s*(?:ba)?sh\b')

def process(payload,root,client="codex"):
    event=payload.get('hook_event_name') or payload.get('hookEventName','')
    tool=payload.get('tool_name') or payload.get('toolName','')
    value=payload.get('tool_input') or payload.get('toolInput') or {}
    if event=='PreToolUse':
        raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
        if any(re.search(p,raw,re.I) for p in DANGEROUS):
            return {'hookSpecificOutput':{'hookEventName':event,'permissionDecision':'deny','permissionDecisionReason':'Destructive operation blocked. Ask the operator to perform any approved destructive maintenance outside the agent.'}}
        # This does not parse arbitrary shell code, encoded commands or nested scripts.
        return {}
    tasks=[]
    for f in sorted((root/'tasks').glob('*.json')):
        t=load(f)
        if t.get('state')!='done':tasks.append(t['id']+': '+t['state'])
    if event=='SessionStart':
        text='Read AGENTS.md and WORKFLOW.md. Use only the current task contract; draft game concepts are not immutable requirements. Tasks: '+('; '.join(tasks[:6]) or 'none; create a task before changing project code.')
        return {'hookSpecificOutput':{'hookEventName':event,'additionalContext':text}}
    if event=='PostToolUse':
        return {'hookSpecificOutput':{'hookEventName':event,'additionalContext':'After editing, run relevant verification. A prior passing run is stale after input changes. Do not edit tests or acceptance criteria merely to force a pass.'}}
    if event=='Stop':
        message='Report changed paths, actual evidence, missing checks and blockers. Do not claim completion without task review. Stop is advisory; the workflow CLI and protected CI own gates.'
        if client=='zcode': return {'hookSpecificOutput':{'hookEventName':event,'additionalContext':message}}
        return {'systemMessage':message}
    return {}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--client',choices=['codex','zcode'],default='codex');a=p.parse_args(argv);root=a.root.resolve()
    try:
        payload=json.loads(sys.stdin.read(1_000_000));cwd=Path(payload.get('cwd',str(root))).resolve()
        # User-level ZCode hook entries are scoped to this project only.
        if not cwd.is_relative_to(root) or not (root/'harness/project.json').is_file():print('{}');return 0
        result=process(payload,root,a.client)
        # Never log commands, prompts, tokens, transcripts, file contents or secrets.
        event=payload.get('hook_event_name') or payload.get('hookEventName','')
        folder=root/'Artifacts/harness/hooks';folder.mkdir(parents=True,exist_ok=True)
        with (folder/'events.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'time':now(),'event':event,'tool':payload.get('tool_name') or payload.get('toolName'),'blocked':result.get('hookSpecificOutput',{}).get('permissionDecision')=='deny'})+'\n')
        print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as exc:
        # No hidden fail-closed security promise: native runtimes can fail open.
        print('Workflow hook error: '+str(exc),file=sys.stderr);print('{}');return 1
if __name__=='__main__':raise SystemExit(main())
