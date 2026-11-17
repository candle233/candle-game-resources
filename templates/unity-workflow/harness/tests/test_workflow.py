"""Offline tests only. These tests do not run a real Editor, Eagle or AI client."""
from __future__ import annotations
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(S))
import common, workflow, unity_cli, assets, hooks, configure, install
PACKAGE=S.parents[1]

class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'project';self.root.mkdir()
        for name in ('AGENTS.md','WORKFLOW.md','design','docs','.codex','.agents','harness/project.json','harness/integrations.json','harness/assets','harness/scripts'):
            src=PACKAGE/name;dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            if name=='.agents' and not src.exists():
                shutil.copytree(PACKAGE.parents[1]/'skills',dest/'skills');continue
            if src.is_dir():shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__'))
            else:shutil.copy2(src,dest)
        (self.root/'tasks').mkdir();(self.root/'Assets').mkdir()
        (self.root/'Packages').mkdir();common.save(self.root/'Packages/manifest.json',{'dependencies':{'com.unity.test-framework':'test-fixture-only'}})
        (self.root/'ProjectSettings').mkdir();(self.root/'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.0.1f1\n')
    def tearDown(self):self.tmp.cleanup()
    def call(self,*args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return workflow.main(['--root',str(self.root),*args])
    def task(self):return common.load(self.root/'tasks/TASK-001.json')
    def save_task(self,t):common.save(self.root/'tasks/TASK-001.json',t)
    def ready_task(self,kind='setup'):
        self.assertEqual(self.call('new','--id','TASK-001','--title','Test scope','--kind',kind),0)
        t=self.task();t.update(scope=['design'],acceptance=['Acceptance example'],plan=['Implement then verify'],gates=['check'],reviews_required=['owner']);self.save_task(t)
        self.assertEqual(self.call('ready','--id','TASK-001','--by','operator','--note','Test fixture approval'),0)
        return self.task()
    def reviewed_task(self):
        self.ready_task();self.assertEqual(self.call('start','--id','TASK-001'),0)
        self.assertEqual(self.call('verify','--id','TASK-001'),0)
        evidence=self.root/'Artifacts/reviews/owner.md';evidence.parent.mkdir(parents=True);evidence.write_text('Actual fixture review note')
        self.assertEqual(self.call('review','--id','TASK-001','--kind','owner','--by','operator','--note','Test fixture','--evidence','Artifacts/reviews/owner.md'),0)
        return self.task()

class CommonTests(Workspace):
    def test_path_traversal(self):
        with self.assertRaises(ValueError):common.safe(self.root,'../escape')
    def test_absolute_path(self):
        with self.assertRaises(ValueError):common.safe(self.root,str(self.root/'x'))
    def test_windows_drive_rejected(self):
        with self.assertRaises(ValueError):common.safe(self.root,'C:/escape')
    def test_atomic_json_roundtrip(self):
        p=self.root/'test.json';common.save(p,{'x':1});self.assertEqual(common.load(p),{'x':1})
    def test_fingerprint_changes(self):
        a=common.fingerprint(self.root);(self.root/'Assets/x.cs').write_text('x');self.assertNotEqual(a,common.fingerprint(self.root))
    def test_evidence_output_not_in_fingerprint(self):
        a=common.fingerprint(self.root);p=self.root/'Artifacts/log.txt';p.parent.mkdir();p.write_text('evidence');self.assertEqual(a,common.fingerprint(self.root))
    def test_extra_scope_fingerprinted(self):
        a=common.fingerprint(self.root,['custom']);(self.root/'custom').mkdir();(self.root/'custom/a.txt').write_text('x');self.assertNotEqual(a,common.fingerprint(self.root,['custom']))

class TaskTests(Workspace):
    def test_clean_structure(self):self.assertEqual(self.call('check'),0)
    def test_new_is_draft(self):
        self.assertEqual(self.call('new','--id','TASK-001','--title','A'),0);self.assertEqual(self.task()['state'],'draft')
    def test_empty_task_cannot_be_ready(self):
        self.call('new','--id','TASK-001','--title','A');self.assertEqual(self.call('ready','--id','TASK-001','--by','owner','--note','x'),2)
    def test_duplicate_task_refused(self):
        self.call('new','--id','TASK-001','--title','A');self.assertEqual(self.call('new','--id','TASK-001','--title','B'),2)
    def test_invalid_id_refused(self):self.assertEqual(self.call('new','--id','../x','--title','A'),2)
    def test_draft_cannot_start(self):
        self.call('new','--id','TASK-001','--title','A');self.assertEqual(self.call('start','--id','TASK-001'),2)
    def test_spec_edit_invalidates_ready(self):
        t=self.ready_task();t['objective']='Different scope';self.save_task(t);self.assertEqual(self.call('start','--id','TASK-001'),2)
    def test_blank_approval_refused(self):
        self.ready_task();self.assertEqual(self.call('ready','--id','TASK-001','--by','','--note','x'),2)
    def test_code_gates_required(self):
        self.call('new','--id','TASK-001','--title','A');t=self.task();t.update(scope=['Assets'],acceptance=['A'],plan=['B'],gates=['check']);self.save_task(t)
        self.assertEqual(self.call('ready','--id','TASK-001','--by','owner','--note','x'),2)
    def test_scope_traversal_refused(self):
        self.ready_task();t=self.task();t['scope']=['../escape'];self.save_task(t);self.assertEqual(self.call('ready','--id','TASK-001','--by','owner','--note','x'),2)
    def test_one_active_writer(self):
        self.ready_task();self.call('start','--id','TASK-001');t=self.task();t.update(id='TASK-002',state='ready');t['approved_spec_sha256']=workflow.spec_hash(t);common.save(self.root/'tasks/TASK-002.json',t)
        self.assertEqual(self.call('start','--id','TASK-002'),2)
    def test_success_enters_review_not_done(self):
        self.ready_task();self.call('start','--id','TASK-001');self.assertEqual(self.call('verify','--id','TASK-001'),0);self.assertEqual(self.task()['state'],'review')
    def test_review_required(self):
        self.ready_task();self.call('start','--id','TASK-001');self.call('verify','--id','TASK-001');self.assertEqual(self.call('done','--id','TASK-001'),2)
    def test_full_offline_lifecycle(self):
        self.reviewed_task();self.assertEqual(self.call('done','--id','TASK-001'),0);self.assertEqual(self.task()['state'],'done')
    def test_code_change_invalidates_evidence(self):
        self.reviewed_task();(self.root/'Assets/Changed.cs').write_text('changed');self.assertEqual(self.call('done','--id','TASK-001'),2)
    def test_task_change_invalidates_evidence(self):
        t=self.reviewed_task();t['acceptance'].append('new condition');self.save_task(t);self.assertEqual(self.call('done','--id','TASK-001'),2)
    def test_review_evidence_change_refused(self):
        self.reviewed_task();(self.root/'Artifacts/reviews/owner.md').write_text('different');self.assertEqual(self.call('done','--id','TASK-001'),2)
    def test_log_tampering_refused(self):
        t=self.reviewed_task();(self.root/t['verification']['gates'][0]['log']).write_text('fake');self.assertEqual(self.call('done','--id','TASK-001'),2)
    def test_budget_is_bounded(self):
        self.ready_task();self.call('start','--id','TASK-001');t=self.task();t['attempts']=3;self.save_task(t);self.assertEqual(self.call('verify','--id','TASK-001'),2)
    def test_done_not_reopened(self):
        self.reviewed_task();self.call('done','--id','TASK-001');self.assertEqual(self.call('reset-budget','--id','TASK-001','--by','owner','--note','x'),2)
    def test_done_cannot_be_blocked_and_reopened(self):
        self.reviewed_task();self.assertEqual(self.call('done','--id','TASK-001'),0)
        self.assertEqual(self.call('block','--id','TASK-001','--reason','reopen'),2)
        self.assertEqual(self.task()['state'],'done')
    def test_parallel_workflow_lock_refuses_write(self):
        p=self.root/'Artifacts/harness/workflow.lock';p.parent.mkdir(parents=True);p.write_text('other writer')
        self.assertEqual(self.call('new','--id','TASK-001','--title','A'),2)
        self.assertEqual(p.read_text(),'other writer')
    def test_verify_checks_other_writer(self):
        self.ready_task();self.call('start','--id','TASK-001');t=self.task()
        t.update(id='TASK-002',state='implementing');common.save(self.root/'tasks/TASK-002.json',t)
        self.assertEqual(self.call('verify','--id','TASK-001'),2)
    def test_handoff(self):
        self.ready_task();self.assertEqual(self.call('handoff'),0);self.assertTrue((self.root/'tasks/HANDOFF.md').is_file())

class UnityTests(Workspace):
    def xml(self,text):
        p=self.root/'test.xml';p.write_text(text);return p
    def test_zero_tests_fail(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="0" passed="0" result="Passed"/>'))
    def test_missing_xml_fails(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.root/'missing.xml')
    def test_bad_xml_fails(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('bad'))
    def test_failed_case_fails(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="1" passed="1" result="Passed"><test-case result="Failed"/></test-run>'))
    def test_counts_invalid(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="1" passed="3" result="Passed"/>'))
    def test_passing_xml(self):self.assertEqual(unity_cli.parse_results(self.xml('<test-run total="2" passed="2" result="Passed"><test-case result="Passed"/><test-case result="Passed"/></test-run>'))['passed'],2)
    def test_incomplete_counts_fail(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="2" passed="1" result="Passed"/>'))
    def test_missing_case_evidence_fails(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="1" passed="1" result="Passed"/>'))
    def test_case_counters_must_match(self):
        with self.assertRaises(ValueError):unity_cli.parse_results(self.xml('<test-run total="2" passed="1" skipped="1" result="Passed"><test-case result="Passed"/><test-case result="Passed"/></test-run>'))
    def test_tests_do_not_use_quit(self):
        cmd=unity_cli.command(Path('Unity'),self.root,'playmode',self.root/'output');self.assertIn('-runTests',cmd);self.assertNotIn('-quit',cmd)
    def test_build_output_unique(self):
        a=unity_cli.command(Path('Unity'),self.root,'build',self.root/'run1/build','WebGL');b=unity_cli.command(Path('Unity'),self.root,'build',self.root/'run2/build','WebGL');self.assertNotEqual(a[a.index('-harnessBuildRoot')+1],b[b.index('-harnessBuildRoot')+1])
    def test_interactive_lock_refused(self):
        (self.root/'Temp').mkdir();(self.root/'Temp/UnityLockfile').write_text('x');errs,_=unity_cli.inspect(self.root);self.assertTrue(any('lock' in e for e in errs))
    def test_missing_editor_not_run(self):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):rc=unity_cli.main(['compile','--project',str(self.root),'--editor',str(self.root/'missing')])
        self.assertEqual(rc,2);self.assertEqual(common.load(next((self.root/'Artifacts').rglob('result.json')))['status'],'NOT_RUN')
    def test_process_timeout(self):
        rc=unity_cli.run_process([sys.executable,'-c','import time;time.sleep(3)'],self.root,self.root/'process.log',1);self.assertEqual(rc,124)
    def fake_run(self,mode,action='verify'):
        fake=self.root/'fake_unity.py'
        fake.write_text('''import sys, pathlib, json, os
args=sys.argv
def arg(k):return args[args.index(k)+1]
mode=os.environ.get("HARNESS_TEST_MODE","")
pathlib.Path(arg("-logFile")).write_text("Initialize engine version: 6000.0.1f1\\n" + ("error CS1001\\n" if mode=="compile_error" else ""))
if mode=="exit_failure":sys.exit(1)
if "-runTests" in args:
 if mode!="no_xml":pathlib.Path(arg("-testResults")).write_text('<test-run total="1" passed="1" failed="0" result="Passed"><test-case result="Passed"/></test-run>')
else:
 pathlib.Path(arg("-harnessReceipt")).write_text(json.dumps({"status":"PASS","unityVersion":"6000.0.1f1"}))
''')
        original=unity_cli.command
        def amended(*args,**kwargs):
            cmd=original(*args,**kwargs);return [sys.executable,str(fake),*cmd[1:]]
        with patch.object(unity_cli,'command',side_effect=amended),patch.dict(os.environ,{'HARNESS_TEST_MODE':mode}),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return unity_cli.main([action,'--project',str(self.root),'--editor',sys.executable])
    def test_mock_editor_success(self):self.assertEqual(self.fake_run('ok'),0)
    def test_mock_missing_xml_fails(self):self.assertEqual(self.fake_run('no_xml'),1)
    def test_mock_compile_error_fails(self):self.assertEqual(self.fake_run('compile_error'),1)
    def test_mock_exit_failure_fails(self):self.assertEqual(self.fake_run('exit_failure'),1)
    def test_own_lock_released(self):self.fake_run('exit_failure');self.assertFalse((self.root/'Artifacts/harness/unity.lock').exists())

class AssetTests(Workspace):
    def test_todo_files(self):
        r=assets.make_todo(self.root,'music','Name','brief','original prompt');p=self.root/'todo/assets'/r['id'];self.assertTrue((p/'request.md').is_file());self.assertTrue((p/'prompt-card.svg').is_file())
    def test_empty_prompt_refused(self):
        with self.assertRaises(ValueError):assets.make_todo(self.root,'music','Name','brief','')
    def test_svg_escapes_text(self):
        r=assets.make_todo(self.root,'image','<script>','brief','<script>&');self.assertIn('&lt;script&gt;',common.safe(self.root,r['card']).read_text())
    def test_offline_eagle_keeps_todo(self):
        r=assets.make_todo(self.root,'music','Name','brief','prompt')
        with patch.object(assets,'eagle',side_effect=OSError('offline')),contextlib.redirect_stderr(io.StringIO()):self.assertFalse(assets.sync(self.root,r))
        self.assertEqual(r['eagle_status'],'pending');self.assertTrue((self.root/'todo/assets'/r['id']/'request.json').is_file())
    def test_ambiguous_post_not_retried(self):
        r=assets.make_todo(self.root,'music','Name','brief','prompt')
        with patch.object(assets,'eagle',side_effect=[{'status':'success','data':[]},OSError('timeout')]),contextlib.redirect_stderr(io.StringIO()):self.assertFalse(assets.sync(self.root,r))
        self.assertEqual(r['eagle_status'],'uncertain')
        with patch.object(assets,'eagle',return_value={'status':'success','data':[]}) as m,contextlib.redirect_stderr(io.StringIO()):self.assertFalse(assets.sync(self.root,r));self.assertEqual(m.call_count,1)
    def test_existing_eagle_item_confirmed(self):
        r=assets.make_todo(self.root,'music','Name','brief','prompt')
        with patch.object(assets,'eagle',return_value={'status':'success','data':[{'name':r['eagle_name'],'id':'123'}]}) as m:self.assertTrue(assets.sync(self.root,r));self.assertEqual(m.call_count,1)
        self.assertEqual(r['eagle_id'],'123')
    def test_unregistered_media_fails(self):
        (self.root/'Assets/x.png').write_bytes(b'x')
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(assets.check(self.root),1)
    def test_check_normalizes_root(self):
        # safe() resolves roots; check() must resolve too or rglob paths fail relative_to.
        (self.root/'Assets/x.png').write_bytes(b'x')
        alias=self.root/'..'/self.root.name
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(assets.check(alias),1)
    def test_prototype_not_shipping(self):
        p=self.root/'Assets/x.png';p.write_bytes(b'x');common.save(self.root/'harness/assets/registry.json',{'schema_version':1,'assets':[{'id':'x','file':'Assets/x.png','sha256':common.sha(p),'use':'prototype_only'}]})
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(assets.check(self.root),0);self.assertEqual(assets.check(self.root,True),1)
    def test_approved_shipping_asset(self):
        p=self.root/'Assets/x.png';p.write_bytes(b'x');ev=self.root/'docs/rights.txt';ev.write_text('License evidence fixture')
        a={'id':'x','file':'Assets/x.png','sha256':common.sha(p),'use':'shipping','review_status':'approved','reviewer':'operator','origin':'created','source':'local source','author':'author','license':'test fixture terms','evidence_file':'docs/rights.txt','attribution_required':False}
        common.save(self.root/'harness/assets/registry.json',{'schema_version':1,'assets':[a]})
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(assets.check(self.root,True),0)
        p.write_bytes(b'changed')
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(assets.check(self.root,True),1)

class AdapterTests(Workspace):
    def test_native_configs_parse(self):
        import tomllib
        self.assertEqual(tomllib.loads((self.root/'.codex/config.toml').read_text(encoding='utf-8'))['sandbox_mode'],'workspace-write');self.assertIn('SessionStart',common.load(self.root/'.codex/hooks.json')['hooks'])
    def test_dangerous_hook_denied(self):
        x=hooks.process({'hook_event_name':'PreToolUse','tool_input':{'command':'git reset --hard'}},self.root);self.assertEqual(x['hookSpecificOutput']['permissionDecision'],'deny')
    def test_harmless_hook_allowed(self):self.assertEqual(hooks.process({'hook_event_name':'PreToolUse','tool_input':{'command':'git status'}},self.root),{})
    def test_start_context(self):self.assertIn('AGENTS.md',hooks.process({'hook_event_name':'SessionStart'},self.root)['hookSpecificOutput']['additionalContext'])
    def test_stop_advisory(self):self.assertNotIn('decision',hooks.process({'hook_event_name':'Stop'},self.root))
    def test_zcode_stop_uses_supported_context(self):
        r=hooks.process({'hook_event_name':'Stop'},self.root,'zcode');self.assertIn('additionalContext',r['hookSpecificOutput']);self.assertNotIn('systemMessage',r)
    def test_zcode_process_paths(self):
        f=configure.fragment(self.root,Path(sys.executable));h=f['hooks']['events']['PreToolUse'][0]['hooks'][0];self.assertEqual(h['type'],'process');self.assertEqual(h['args'][0],'-I');self.assertTrue(Path(h['args'][1]).is_absolute())
    def test_hook_outside_project_noop(self):
        raw=json.dumps({'hook_event_name':'SessionStart','cwd':self.tmp.name})
        with patch('sys.stdin',io.StringIO(raw)),contextlib.redirect_stdout(io.StringIO()) as out:self.assertEqual(hooks.main(['--root',str(self.root)]),0)
        self.assertEqual(out.getvalue().strip(),'{}')

class InstallerTests(Workspace):
    def source(self):
        source=Path(self.tmp.name)/'package';source.mkdir();(source/'AGENTS.md').write_text('new rules');(source/'README.md').write_text('new readme')
        common.save(source/'MANIFEST.json',{'schema_version':1,'files':[{'path':p.name,'sha256':common.sha(p)} for p in source.iterdir() if p.name!='MANIFEST.json']});return source
    def test_all_conflicts_detected_before_copy(self):
        source=self.source()
        with self.assertRaises(ValueError):install.install(source,self.root,False)
        self.assertFalse((self.root/'harness/README.md').exists())
    def test_dry_run_does_not_write(self):
        source=self.source();(self.root/'AGENTS.md').unlink();paths=install.install(source,self.root,True);self.assertIn('AGENTS.md',paths);self.assertFalse((self.root/'AGENTS.md').exists())
    def test_create_only_install(self):
        source=self.source();(self.root/'AGENTS.md').unlink();install.install(source,self.root,False);self.assertEqual((self.root/'AGENTS.md').read_text(),'new rules');self.assertTrue((self.root/'harness/README.md').exists())
    def test_tampered_package_refused(self):
        source=self.source();(source/'AGENTS.md').write_text('tampered')
        with self.assertRaises(ValueError):install.install(source,self.root,True)
    def test_project_required(self):
        source=self.source();(self.root/'ProjectSettings/ProjectVersion.txt').unlink()
        with self.assertRaises(ValueError):install.install(source,self.root,True)
    def test_source_changed_after_preflight_uses_manifest_sha(self):
        source=self.source();(self.root/'AGENTS.md').unlink()
        original=install.package_plan
        def changed(*args,**kwargs):
            plan=original(*args,**kwargs)
            (source/'AGENTS.md').write_text('changed after preflight',encoding='utf-8')
            return plan
        with patch.object(install,'package_plan',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'Source changed during installation'):
                install.install(source,self.root,False)
        self.assertFalse((self.root/'AGENTS.md').exists())
        self.assertFalse((self.root/'harness/README.md').exists())
    def test_later_source_change_rolls_back_earlier_copies(self):
        source=self.source();(self.root/'AGENTS.md').unlink()
        data=common.load(source/'MANIFEST.json');data['files'].sort(key=lambda item:item['path']);common.save(source/'MANIFEST.json',data)
        original=install.package_plan
        def changed(*args,**kwargs):
            plan=original(*args,**kwargs)
            (source/'README.md').write_text('changed after preflight',encoding='utf-8')
            return plan
        with patch.object(install,'package_plan',side_effect=changed):
            with self.assertRaises(ValueError):install.install(source,self.root,False)
        self.assertFalse((self.root/'AGENTS.md').exists())
        self.assertFalse((self.root/'harness/README.md').exists())
    def test_existing_game_readme_is_never_overwritten(self):
        source=self.source();(self.root/'AGENTS.md').unlink()
        (self.root/'README.md').write_text('Game README',encoding='utf-8')
        install.install(source,self.root,False)
        self.assertEqual((self.root/'README.md').read_text(encoding='utf-8'),'Game README')
        self.assertEqual((self.root/'harness/README.md').read_text(encoding='utf-8'),'new readme')
    def test_bootstrap_without_unity_does_not_invent_project(self):
        source=self.source();target=Path(self.tmp.name)/'bootstrap'
        install.install(source,target,False,True)
        self.assertTrue((target/'AGENTS.md').is_file())
        self.assertFalse((target/'Packages').exists())
        self.assertFalse((target/'ProjectSettings').exists())
    def test_bootstrap_rejects_manifest_creating_unity_settings(self):
        source=self.source();target=Path(self.tmp.name)/'bootstrap'
        data=common.load(source/'MANIFEST.json');data['files'][0]['target']='ProjectSettings/ProjectVersion.txt';common.save(source/'MANIFEST.json',data)
        with self.assertRaisesRegex(ValueError,'Bootstrap cannot create Unity'):
            install.install(source,target,False,True)
        self.assertFalse(target.exists())
    def test_duplicate_and_parent_child_targets_rejected(self):
        source=self.source();target=Path(self.tmp.name)/'bootstrap'
        for first,second in (('same','SAME'),('same','same/child')):
            data=common.load(source/'MANIFEST.json');data['files'][0]['target']=first;data['files'][1]['target']=second;common.save(source/'MANIFEST.json',data)
            with self.assertRaisesRegex(ValueError,'mapped target'):
                install.install(source,target,False,True)
        self.assertFalse(target.exists())
    def test_all_conflicts_include_parent_files_before_copy(self):
        source=self.source();(self.root/'AGENTS.md').unlink();shutil.rmtree(self.root/'harness');(self.root/'harness').write_text('not a folder',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'not a directory'):install.install(source,self.root,False)
        self.assertFalse((self.root/'AGENTS.md').exists())
    def test_installer_refuses_target_root_symlink(self):
        source=self.source();target=Path(self.tmp.name)/'linked-project'
        try:target.symlink_to(self.root,target_is_directory=True)
        except (NotImplementedError,OSError) as exc:self.skipTest('Symlink unavailable: '+str(exc))
        with self.assertRaisesRegex(ValueError,'Symlink'):install.install(source,target,True)
    def test_installer_refuses_source_file_symlink(self):
        source=self.source();(source/'AGENTS.md').unlink()
        try:(source/'AGENTS.md').symlink_to(self.root/'AGENTS.md')
        except (NotImplementedError,OSError) as exc:self.skipTest('Symlink unavailable: '+str(exc))
        with self.assertRaisesRegex(ValueError,'Symlink'):install.install(source,self.root,True)
    def test_noncanonical_manifest_path_rejected(self):
        source=self.source();data=common.load(source/'MANIFEST.json');data['files'][0]['path']='./AGENTS.md';common.save(source/'MANIFEST.json',data)
        with self.assertRaisesRegex(ValueError,'canonical'):install.install(source,self.root,True)

if __name__=='__main__':unittest.main()
