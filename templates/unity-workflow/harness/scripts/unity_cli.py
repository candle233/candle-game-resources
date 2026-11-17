"""Run an installed, licensed Unity Editor on an existing project; never fake a pass."""
from __future__ import annotations
import argparse, json, os, re, shutil, signal, subprocess, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uuid import uuid4
from common import ROOT, now, load, save
TARGETS=("StandaloneWindows64","StandaloneOSX","StandaloneLinux64","WebGL")
ERROR=re.compile(r"error CS\d{4}\b|Scripts have compiler errors|Aborting batchmode due to failure",re.I)

def inspect(project):
    errors=[];version=None
    for rel in ("Assets","Packages/manifest.json","ProjectSettings/ProjectVersion.txt"):
        if not (project/rel).exists(): errors.append("Missing "+rel)
    v=project/"ProjectSettings/ProjectVersion.txt"
    if v.is_file():
        m=re.search(r"m_EditorVersion:\s*(\S+)",v.read_text(encoding="utf-8-sig"))
        if m: version=m.group(1)
        else: errors.append("Cannot parse project Editor version")
    mf=project/"Packages/manifest.json"
    if mf.is_file():
        try:
            if "com.unity.test-framework" not in load(mf).get("dependencies",{}): errors.append("Install the project-compatible Unity Test Framework")
        except ValueError as exc: errors.append(str(exc))
    if (project/"Temp/UnityLockfile").exists(): errors.append("Editor lock exists. Close the interactive Editor; do not delete its lock automatically")
    return errors,version

def parse_results(path):
    if not path.is_file(): raise ValueError("Missing fresh NUnit XML")
    try: root=ET.parse(path).getroot()
    except ET.ParseError as exc: raise ValueError("Malformed NUnit XML") from exc
    if root.tag!="test-run": raise ValueError("Expected NUnit3 test-run; review the installed test framework if format differs")
    try: counts={k:int(root.get(k,"0")) for k in ("total","passed","failed","inconclusive","skipped")}
    except ValueError as exc: raise ValueError("Invalid test counters") from exc
    if any(v<0 for v in counts.values()) or counts['total']<=0 or counts['passed']<=0: raise ValueError("Zero tests / zero passed tests is not success")
    if counts['passed']+counts['failed']+counts['inconclusive']+counts['skipped']!=counts['total']: raise ValueError('Inconsistent test counts')
    if counts['failed'] or counts['inconclusive'] or root.get('result','').lower() not in ('passed','success'): raise ValueError("Failed or inconclusive test suite")
    cases=root.findall('.//test-case')
    if len(cases)!=counts['total']: raise ValueError("Missing or inconsistent test-case evidence")
    case_results=[c.get('result','').lower() for c in cases]
    if any(r not in ('passed','skipped') for r in case_results): raise ValueError("A test case failed or has an unknown result")
    if case_results.count('passed')!=counts['passed'] or case_results.count('skipped')!=counts['skipped']:
        raise ValueError("Test-case results disagree with counters")
    return counts

def run_process(cmd,cwd,log,timeout):
    with log.open('w',encoding='utf-8') as out:
        kwargs={'start_new_session':True} if os.name!='nt' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP}
        proc=subprocess.Popen(cmd,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,**kwargs)
        try: return proc.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            else:
                try: os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            proc.wait(timeout=20);out.write('\nHARNESS: process timeout; process tree terminated\n');return 124

def command(editor,project,stage,folder,target=None,test_filter=None):
    cmd=[str(editor),'-batchmode','-projectPath',str(project),'-logFile',str(folder/'editor.log')]
    if stage in ('editmode','playmode'):
        # Test Framework owns process exit; do NOT combine -runTests with -quit.
        cmd += ['-runTests','-testPlatform',stage,'-testResults',str(folder/'tests.xml')]
        if test_filter: cmd += ['-testFilter',test_filter]
    else:
        cmd += ['-quit','-executeMethod','WorkflowHarness.EditorAutomation.'+('Build' if stage=='build' else 'Compile'),'-harnessReceipt',str(folder/'receipt.json')]
        if stage=='build': cmd += ['-buildTarget',target,'-harnessBuildRoot',str(project/'Builds'/folder.parent.name)]
    return cmd

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['doctor','compile','editmode','playmode','verify','build'])
    p.add_argument('--project',type=Path,default=ROOT);p.add_argument('--editor');p.add_argument('--timeout',type=int,default=1800)
    p.add_argument('--target',choices=TARGETS);p.add_argument('--filter',dest='test_filter')
    a=p.parse_args(argv);project=a.project.resolve()
    if a.timeout<=0: p.error('Timeout must be positive')
    if a.action=='build' and not a.target:p.error('build needs --target')
    try:
        errors,version=inspect(project)
        raw=a.editor or os.environ.get('UNITY_EDITOR',''); found=shutil.which(raw) if raw else None
        editor=Path(found or raw).expanduser() if raw else None
        if editor is None or not editor.is_file(): errors.append('Set UNITY_EDITOR to the matching Editor executable')
        else: editor=editor.resolve()
        print(json.dumps({'project':str(project),'project_version':version,'editor':str(editor),'errors':errors},indent=2))
        if a.action=='doctor':return 2 if errors else 0
        runid=time.strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:10]
        folder=project/'Artifacts/harness/unity'/runid;folder.mkdir(parents=True,exist_ok=False)
        result={'run_id':runid,'action':a.action,'started_utc':now(),'project_version':version,'status':'NOT_RUN','stages':[]}
        if errors:result['errors']=errors;save(folder/'result.json',result);return 2
        lock=project/'Artifacts/harness/unity.lock'
        try:
            fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
        except FileExistsError: raise ValueError('Another Harness Unity run is active, or a stale harness lock needs human inspection')
        try:
            stages=['compile','editmode','playmode'] if a.action=='verify' else [a.action]
            for stage in stages:
                dest=folder/stage;dest.mkdir()
                cmd=command(editor,project,stage,dest,a.target,a.test_filter)
                start=time.monotonic();rc=run_process(cmd,project,dest/'process.log',a.timeout)
                entry={'stage':stage,'returncode':rc,'seconds':round(time.monotonic()-start,3),'directory':dest.relative_to(project).as_posix(),'status':'PASS'}
                err=[];log=dest/'editor.log'
                if rc:err.append('Unity exit code '+str(rc))
                if not log.is_file():err.append('Missing fresh Editor log')
                else:
                    text=log.read_text(encoding='utf-8',errors='replace')
                    if ERROR.search(text):err.append('Compiler or batch failure in Editor log')
                    m=re.search(r'Initialize engine version:\s*(\S+)',text)
                    if not m:err.append('Missing Editor version in fresh log')
                    elif m.group(1)!=version:err.append('Editor version mismatch')
                if not err:
                    try:
                        if stage in ('editmode','playmode'):entry['tests']=parse_results(dest/'tests.xml')
                        else:
                            receipt=load(dest/'receipt.json')
                            if receipt.get('status')!='PASS' or receipt.get('unityVersion')!=version:raise ValueError('Invalid Editor receipt or version mismatch')
                            if stage=='build':
                                if receipt.get('target')!=a.target:raise ValueError('Build target mismatch')
                                output=Path(receipt.get('output','')).resolve()
                                if not output.is_relative_to((project/'Builds').resolve()) or not output.exists():raise ValueError('Missing/outside build artifact')
                                if output.is_dir() and not any(p.is_file() for p in output.rglob('*')):raise ValueError('Empty build directory')
                            entry['receipt']=receipt
                    except (OSError,ValueError) as exc:err.append(str(exc))
                if err:entry['status']='FAIL';entry['errors']=err
                result['stages'].append(entry)
                if err:break
            result['status']='PASS' if len(result['stages'])==len(stages) and all(s['status']=='PASS' for s in result['stages']) else 'FAIL'
            save(folder/'result.json',result);print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 1
        finally:lock.unlink(missing_ok=True)
    except (OSError,ValueError,subprocess.SubprocessError) as exc:print('ERROR: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
