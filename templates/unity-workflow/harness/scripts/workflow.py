"""Task-scoped workflow: explicit readiness, reproducible evidence and review attestations.
Attestations are NOT authentication. Protect merge/release approval outside the agent.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uuid import uuid4
from common import ROOT, now, load, save, safe, sha, digest, fingerprint, git_head
KINDS=("setup","prototype","feature","bugfix","refactor","asset","docs","release")
GATES=("check","python","compile","editmode","playmode","build","assets")
SPEC_KEYS=("id","kind","objective","scope","out_of_scope","assumptions","design_sources","acceptance","plan","gates","reviews_required")

def task_path(root, ident):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,63}", ident): raise ValueError("Invalid task id")
    return safe(root,"tasks/"+ident+".json")
def spec_hash(t): return digest({k:t.get(k) for k in SPEC_KEYS})
def validate_task(t):
    errors=[]
    if t.get("kind") not in KINDS: errors.append("Unknown task kind")
    for key in ("objective",):
        if not isinstance(t.get(key),str) or not t[key].strip(): errors.append("Missing "+key)
    for key in ("scope","acceptance","plan","gates","reviews_required"):
        if not isinstance(t.get(key),list) or not t[key] or not all(isinstance(x,str) and x.strip() for x in t[key]): errors.append("Fill nonempty list: "+key)
    if any(g not in GATES for g in t.get("gates",[])): errors.append("Unknown gate")
    if t.get("kind") in ("prototype","feature","bugfix","refactor") and not {"compile","editmode","playmode"}.issubset(t.get("gates",[])):
        errors.append("Code tasks require compile, editmode and playmode gates; use a docs task for text-only work")
    if t.get("kind")=="release" and not {"compile","editmode","playmode","build","assets"}.issubset(t.get("gates",[])):
        errors.append("Release requires compile, both test modes, build and asset clearance")
    if t.get("kind")=="release" and not {"human_playtest","release_owner"}.issubset(t.get("reviews_required",[])):
        errors.append("Release requires human_playtest and release_owner reviews")
    for p in t.get("scope",[]):
        if p in (".","/","*",""): errors.append("Scope must identify concrete paths")
        if p.split("/")[0] in ("tasks","Artifacts"): errors.append("Do not include task/evidence output in implementation scope")
    return errors

def check(root):
    problems=[]
    for f in ("AGENTS.md","WORKFLOW.md","design/CURRENT.md","harness/project.json","harness/integrations.json","harness/assets/registry.json"):
        if not (root/f).is_file(): problems.append("Missing "+f)
    for f in (root/"harness").rglob("*.json"):
        if "tests" in f.parts: continue
        try: load(f)
        except (ValueError,OSError) as exc: problems.append(str(f)+": "+str(exc))
    for p in (root/"tasks").glob("*.json"):
        try:
            t=load(p)
            if t.get("state")!="draft": problems += [p.name+": "+e for e in validate_task(t)]
        except (ValueError,OSError) as exc: problems.append(str(exc))
    try:
        import tomllib
        tomllib.loads((root/".codex/config.toml").read_text())
    except (OSError,ValueError) as exc: problems.append(str(exc))
    print(json.dumps({"check":"workflow_structure","status":"FAIL" if problems else "PASS","errors":problems},indent=2))
    return 1 if problems else 0

def gate_commands(root,t):
    py=sys.executable; scripts=root/"harness/scripts"; c=load(root/"harness/project.json")
    result=[]
    for gate in t["gates"]:
        if gate=="check": cmd=[py,"-I",str(scripts/"workflow.py"),"--root",str(root),"check"]
        elif gate=="python": cmd=[py,"-I","-m","unittest","discover","-s",str(root/"harness/tests"),"-v"]
        elif gate=="assets": cmd=[py,"-I",str(scripts/"assets.py"),"--root",str(root),"check","--release"]
        else:
            cmd=[py,"-I",str(scripts/"unity_cli.py"),gate,"--project",str(root)]
            if gate=="build":
                target=c["unity"].get("build_target")
                if not target: raise ValueError("Set an approved build_target in harness/project.json before build")
                cmd += ["--target",target]
        result.append((gate,cmd))
    return result

def fresh_evidence(root,t):
    e=t.get("verification")
    if not e or e.get("status")!="PASS": raise ValueError("No passing task verification")
    if e["spec_sha256"]!=spec_hash(t): raise ValueError("Task spec changed: approve scope and re-verify")
    if e["input_sha256"]!=fingerprint(root,t.get("scope",[])+t.get("design_sources",[])): raise ValueError("Project changed after verification: re-verify")
    if [x["gate"] for x in e["gates"]]!=t["gates"] or any(x["returncode"]!=0 for x in e["gates"]):
        raise ValueError("Required gates did not all pass")
    for x in e["gates"]:
        p=safe(root,x["log"])
        if not p.is_file() or sha(p)!=x["log_sha256"]: raise ValueError("Verification log missing or changed")
    return e

def assert_single_writer(root,t):
    for f in (root/"tasks").glob("*.json"):
        other=load(f)
        if other["id"]!=t["id"] and other["state"] in ("implementing","verifying"):
            raise ValueError("One writer per checkout: "+other["id"])

def verify(root,t):
    assert_single_writer(root,t)
    if t["state"] not in ("implementing","verifying","blocked","review"): raise ValueError("Start an approved task first")
    if t.get("approved_spec_sha256")!=spec_hash(t): raise ValueError("Scope changed: run ready again with approval")
    limit=load(root/"harness/project.json")["max_verification_attempts"]
    if t["attempts"]>=limit: raise ValueError("Attempt budget reached. Record a blocker; human must re-scope or approve a reset")
    commands=gate_commands(root,t)
    t["attempts"]+=1; t["state"]="verifying"; t["reviews"]=[]
    save(task_path(root,t["id"]),t)
    run=uuid4().hex; folder=root/"Artifacts/harness/tasks"/t["id"]/run; folder.mkdir(parents=True)
    before=fingerprint(root,t.get("scope",[])+t.get("design_sources",[])); outcomes=[]
    timeout=load(root/"harness/project.json")["command_timeout_seconds"]
    for gate,cmd in commands:
        log=folder/(gate+".log")
        # Unity owns its process-tree timeout; allow it time to write its result.
        outer_timeout=timeout+60 if gate in ("compile","editmode","playmode","build") else timeout
        if gate in ("compile","editmode","playmode","build"): cmd += ["--timeout",str(timeout)]
        with log.open("w",encoding="utf-8") as stream:
            try: rc=subprocess.run(cmd,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=outer_timeout,check=False).returncode
            except subprocess.TimeoutExpired: rc=124; stream.write("\nHARNESS TIMEOUT\n")
            except OSError as exc: rc=127; stream.write(str(exc))
        outcomes.append({"gate":gate,"returncode":rc,"log":log.relative_to(root).as_posix(),"log_sha256":sha(log)})
        if rc: break
    after=fingerprint(root,t.get("scope",[])+t.get("design_sources",[]))
    status="PASS" if len(outcomes)==len(commands) and all(x["returncode"]==0 for x in outcomes) and before==after else "FAIL"
    result={"run_id":run,"status":status,"time_utc":now(),"git_head":git_head(root),"spec_sha256":spec_hash(t),"input_sha256":after,"inputs_changed_during_run":before!=after,"gates":outcomes}
    save(folder/"result.json",result); t["verification"]=result; t["state"]="review" if status=="PASS" else "blocked"
    t["blocked_reason"]="" if status=="PASS" else "Inspect gate logs; changed inputs also invalidate the run"
    save(task_path(root,t["id"]),t); print(json.dumps(result,indent=2))
    return 0 if status=="PASS" else 1

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--root",type=Path,default=ROOT)
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("check"); sub.add_parser("status"); sub.add_parser("handoff")
    n=sub.add_parser("new"); n.add_argument("--id",required=True); n.add_argument("--title",required=True); n.add_argument("--kind",choices=KINDS,default="feature")
    for name in ("ready","start","verify","review","done","block","reset-budget"):
        a=sub.add_parser(name); a.add_argument("--id",required=True)
        if name in ("ready","review","reset-budget"): a.add_argument("--by",required=True); a.add_argument("--note",required=True)
        if name=="review": a.add_argument("--kind",required=True); a.add_argument("--evidence",required=True)
        if name=="block": a.add_argument("--reason",required=True)
    a=p.parse_args(argv); root=a.root.resolve()
    lock=root/"Artifacts/harness/workflow.lock"; lock_fd=None
    try:
        if a.cmd not in ("check","status"):
            lock.parent.mkdir(parents=True,exist_ok=True)
            try: lock_fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            except FileExistsError: raise ValueError("Another workflow writer is active; inspect stale locks manually")
            os.write(lock_fd,str(os.getpid()).encode())
        if a.cmd=="check": return check(root)
        if a.cmd in ("status","handoff"):
            tasks=[load(f) for f in sorted((root/"tasks").glob("*.json"))]
            rows=[{k:t.get(k) for k in ("id","state","objective","attempts","blocked_reason")} for t in tasks]
            if a.cmd=="handoff":
                path=root/"tasks/HANDOFF.md"; path.write_text("# Generated handoff\n\nRead each task JSON and its evidence before continuing.\n\n```json\n"+json.dumps(rows,ensure_ascii=False,indent=2)+"\n```\n",encoding="utf-8")
            print(json.dumps(rows,ensure_ascii=False,indent=2)); return 0
        path=task_path(root,a.id)
        if a.cmd in ("ready","review","reset-budget") and (not a.by.strip() or not a.note.strip()): raise ValueError("Reviewer identity and note cannot be blank")
        if a.cmd=="new":
            if path.exists(): raise ValueError("Task already exists")
            gates=["check","python"] if a.kind in ("setup","docs","asset") else ["check","python","compile","editmode","playmode"]
            reviews=["owner"]
            if a.kind in ("prototype","feature"): reviews+=["human_playtest"]
            if a.kind=="asset": gates+=["assets"]; reviews+=["asset_review"]
            if a.kind=="release": gates+=["build","assets"]; reviews+=["human_playtest","release_owner"]
            t={"schema_version":1,"id":a.id,"kind":a.kind,"state":"draft","objective":a.title,"scope":[],"out_of_scope":[],"assumptions":[],"design_sources":[],"acceptance":[],"plan":[],"gates":gates,"reviews_required":reviews,"attempts":0,"reviews":[],"verification":None,"events":[],"blocked_reason":""}
        else:
            t=load(path)
            if t.get("id")!=a.id: raise ValueError("Task id does not match its filename")
            if t.get("state")=="done": raise ValueError("Create a new task to change delivered work")
            if a.cmd=="ready":
                if t["state"]=="done": raise ValueError("Create a new task to change delivered work")
                errs=validate_task(t)
                for rel in t["scope"]: safe(root,rel)
                for rel in t.get("design_sources",[]):
                    if not safe(root,rel).is_file(): errs.append("Missing design source: "+rel)
                if errs: raise ValueError("; ".join(errs))
                t["state"]="ready"; t["approved_spec_sha256"]=spec_hash(t); t["verification"]=None; t["reviews"]=[]
            elif a.cmd=="start":
                if t["state"]!="ready": raise ValueError("Task is not ready")
                if t.get("approved_spec_sha256")!=spec_hash(t): raise ValueError("Task changed since readiness approval")
                assert_single_writer(root,t)
                t["state"]="implementing"; t["start_git_head"]=git_head(root)
            elif a.cmd=="verify": return verify(root,t)
            elif a.cmd=="review":
                if t["state"]!="review": raise ValueError("Verification must pass before review")
                e=fresh_evidence(root,t)
                if a.kind not in t["reviews_required"]: raise ValueError("Unexpected review kind")
                f=safe(root,a.evidence)
                if not f.is_file() or f.stat().st_size==0: raise ValueError("Review evidence is missing/empty")
                t["reviews"]=[r for r in t["reviews"] if r["kind"]!=a.kind]+[{"kind":a.kind,"reviewer":a.by,"note":a.note,"file":a.evidence,"sha256":sha(f),"run_id":e["run_id"],"time_utc":now()}]
            elif a.cmd=="done":
                if t["state"]!="review": raise ValueError("Only a reviewed task can finish")
                e=fresh_evidence(root,t)
                reviews={r["kind"]:r for r in t["reviews"]}
                for kind in t["reviews_required"]:
                    if kind not in reviews: raise ValueError("Missing human review: "+kind)
                    r=reviews[kind]; f=safe(root,r["file"])
                    if r["run_id"]!=e["run_id"] or not f.is_file() or sha(f)!=r["sha256"]: raise ValueError("Review is stale or missing")
                t["state"]="done"
            elif a.cmd=="block": t["state"]="blocked"; t["blocked_reason"]=a.reason
            elif a.cmd=="reset-budget":
                if t["state"]=="done": raise ValueError("Create a new task instead of reopening a done task")
                if validate_task(t): raise ValueError("Correct the task contract before resetting budget")
                t["attempts"]=0; t["state"]="ready"; t["approved_spec_sha256"]=spec_hash(t); t["reviews"]=[]; t["verification"]=None
        t["events"].append({"action":a.cmd,"time_utc":now(),"by":getattr(a,"by",None),"note":getattr(a,"note",None)})
        save(path,t); print(str(path)); return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr); return 2
    finally:
        if lock_fd is not None:
            os.close(lock_fd); lock.unlink(missing_ok=True)
if __name__=="__main__": raise SystemExit(main())
