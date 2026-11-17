"""Offline stdlib-only regression tests for the public resource tool."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('resource_tool', REPOSITORY / 'tools/resources.py')
resources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resources)


class ResourceWorkspace(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'resources'
        self.root.mkdir()
        for directory in ('templates/unity-workflow', 'skills'):
            shutil.copytree(REPOSITORY / directory, self.root / directory,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (self.root / 'tools').mkdir()
        shutil.copy2(REPOSITORY / 'tools/resources.py', self.root / 'tools/resources.py')
        (self.root / 'README.md').write_text('Resource README, not a game README.\n', encoding='utf-8')
        self.project = self.base / 'game'
        self.project.mkdir()
        self.template = self.root / 'templates/unity-workflow'
        # The fixture contains installable resources, not concurrent root docs.
        # Do not copy the skill-index README's links to absent provenance docs.
        (self.root / 'skills/README.md').unlink(missing_ok=True)
        (self.template / 'README.md').unlink(missing_ok=True)
        resources.generate_manifest(self.root)

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
        return path

    def manifest(self):
        return json.loads((self.root / 'MANIFEST.json').read_text(encoding='utf-8'))

    def save_manifest(self, manifest):
        (self.root / 'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')

    def unity_project(self):
        (self.project / 'Assets').mkdir()
        (self.project / 'Packages').mkdir()
        (self.project / 'Packages/manifest.json').write_text('{"dependencies":{}}', encoding='utf-8')
        (self.project / 'ProjectSettings').mkdir()
        (self.project / 'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.0.1f1\n', encoding='utf-8')

    def symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (NotImplementedError, OSError) as exc:
            self.skipTest('Platform does not permit symlink creation: ' + str(exc))

    def cli(self, *args):
        return subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(self.root / 'tools/resources.py'), *map(str, args)],
                              cwd=self.base, capture_output=True, text=True, encoding='utf-8', timeout=60)

    def install(self, **kwargs):
        return resources.install_resources(self.project, root=self.root, **kwargs)


class ManifestTests(ResourceWorkspace):
    def test_inventory_mappings_sorted_and_no_self_hash(self):
        data = self.manifest()
        self.assertEqual(data['schema_version'], 1)
        paths = [item['path'] for item in data['files']]
        self.assertEqual(paths, sorted(paths))
        self.assertNotIn('MANIFEST.json', paths)
        self.assertNotIn('README.md', paths)
        self.assertFalse(any(item['target'] == 'README.md' for item in data['files']))
        self.assertTrue(any(item['target'] == '.agents/skills/workflow-orchestrator/SKILL.md' for item in data['files']))
        for item in data['files']:
            self.assertEqual(item['sha256'], hashlib.sha256((self.root / item['path']).read_bytes()).hexdigest())

    def test_template_readme_mapping_not_resource_readme(self):
        self.write('templates/unity-workflow/README.md', 'Template README\n')
        # Remove a concurrently supplied target README to test the legacy mapping alone.
        (self.template / 'harness/README.md').unlink(missing_ok=True)
        data = resources.generate_manifest(self.root)
        item = next(item for item in data['files'] if item['path'] == 'templates/unity-workflow/README.md')
        self.assertEqual(item['target'], 'harness/README.md')
        self.assertEqual(resources.verify(self.root)['status'], 'ok')

    def test_excludes_caches_archival_fragment_and_skill_index(self):
        for path in ('templates/unity-workflow/__pycache__/cache.pyc', 'skills/asset-production/__pycache__/cache.pyc',
                     'templates/unity-workflow/cache.tmp', 'templates/unity-workflow/.git/HEAD',
                     'skills/README.md'):
            self.write(path, 'ignored')
        data = resources.generate_manifest(self.root)
        paths = [item['path'] for item in data['files']]
        self.assertNotIn('templates/unity-workflow/.gitignore.workflow', paths)
        self.assertNotIn('skills/README.md', paths)
        self.assertFalse(any('__pycache__' in path or path.endswith('.tmp') or '/.git/' in path for path in paths))
        self.assertEqual(resources.verify(self.root)['skills'], 6)

    def test_manifest_regeneration_is_reproducible_and_verifies(self):
        before = (self.root / 'MANIFEST.json').read_bytes()
        resources.generate_manifest(self.root)
        self.assertEqual(before, (self.root / 'MANIFEST.json').read_bytes())
        self.assertEqual(resources.verify(self.root)['status'], 'ok')

    def test_source_tamper_and_missing_manifest_entry_rejected(self):
        self.write('templates/unity-workflow/AGENTS.md', 'changed')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            resources.verify(self.root)
        with self.assertRaises(ValueError):
            self.install(bootstrap=True, apply=True)
        self.assertFalse(any(self.project.iterdir()))
        resources.generate_manifest(self.root)
        data = self.manifest()
        data['files'].pop()
        self.save_manifest(data)
        with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
            resources.verify(self.root)

    def test_added_source_requires_manifest_regeneration(self):
        self.write('templates/unity-workflow/harness/new.txt', 'new')
        with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
            resources.verify_manifest(self.root)

    def test_manifest_hash_tamper_rejected_on_verify_and_install(self):
        data = self.manifest()
        data['files'][0]['sha256'] = '0' * 64
        self.save_manifest(data)
        for operation in (lambda: resources.verify(self.root), lambda: self.install(bootstrap=True, apply=True)):
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                operation()
        self.assertFalse(any(self.project.iterdir()))

    def test_manifest_mapping_tamper_and_traversal_rejected(self):
        for target in ('unexpected.txt', '../escape', '/absolute', 'C:/escape', 'a\\b', 'a/./b', '.', 'a//b'):
            with self.subTest(target=target):
                data = resources.inventory(self.root)
                data['files'][0]['target'] = target
                self.save_manifest(data)
                with self.assertRaises(ValueError):
                    self.install(bootstrap=True, apply=True)
        self.assertFalse(any(self.project.iterdir()))

    def test_mapping_case_collision_and_parent_collision_rejected(self):
        for targets in (('same', 'SAME'), ('same', 'same/child')):
            with self.subTest(targets=targets):
                data = resources.inventory(self.root)
                for item, target in zip(data['files'], targets):
                    item['target'] = target
                self.save_manifest(data)
                with self.assertRaisesRegex(ValueError, 'colliding'):
                    resources.verify_manifest(self.root)

    def test_legacy_and_current_readme_target_collision_rejected(self):
        self.write('templates/unity-workflow/README.md', 'legacy')
        self.write('templates/unity-workflow/harness/README.md', 'current')
        with self.assertRaisesRegex(ValueError, 'colliding'):
            resources.generate_manifest(self.root)

    def test_manifest_schema_duplicates_and_unsorted_rejected(self):
        original = resources.inventory(self.root)
        bad_manifests = [
            [], {'schema_version': True, 'files': []}, {'schema_version': 2, 'files': []},
            {'schema_version': 1, 'files': {}}, {'schema_version': 1, 'files': [{}]},
            {'schema_version': 1, 'files': [original['files'][0], original['files'][0]]},
            {'schema_version': 1, 'files': list(reversed(original['files']))},
        ]
        for data in bad_manifests:
            with self.subTest(data=data):
                self.save_manifest(data)
                with self.assertRaises(ValueError):
                    resources.verify_manifest(self.root)

    def test_self_entry_and_resource_root_readme_cannot_be_injected(self):
        for path in ('MANIFEST.json', 'README.md'):
            data = resources.inventory(self.root)
            data['files'].append({'path': path, 'target': 'harness/injected.md', 'sha256': '0' * 64})
            data['files'].sort(key=lambda item: item['path'])
            self.save_manifest(data)
            with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
                resources.verify_manifest(self.root)


class InstallTests(ResourceWorkspace):
    def test_default_dry_run_no_writes_even_to_new_project(self):
        self.project = self.base / 'does-not-exist'
        result = self.install(bootstrap=True)
        self.assertEqual(result['mode'], 'dry-run')
        self.assertGreater(result['count'], 0)
        self.assertFalse(self.project.exists())
        self.assertFalse(any(self.root.rglob('__pycache__')))

    def test_cli_dry_run_and_error_exit_codes(self):
        result = self.cli('install', '--project', self.project, '--bootstrap')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'], 'dry-run')
        self.assertFalse(any(self.project.iterdir()))
        result = self.cli('install', '--project', self.project)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unity project', result.stderr)

    def test_bootstrap_never_fabricates_unity_files_and_preserves_readme(self):
        readme = self.project / 'README.md'
        readme.write_text('游戏仓自己的说明\n', encoding='utf-8')
        result = self.install(bootstrap=True, apply=True)
        self.assertEqual(result['mode'], 'installed')
        self.assertEqual(readme.read_text(encoding='utf-8'), '游戏仓自己的说明\n')
        self.assertFalse((self.project / 'Packages').exists())
        self.assertFalse((self.project / 'ProjectSettings').exists())
        self.assertTrue((self.project / 'harness/scripts/workflow.py').is_file())
        self.assertTrue((self.project / '.agents/skills/asset-production/SKILL.md').is_file())
        self.assertTrue((self.project / '.gitignore').is_file())
        self.assertFalse((self.project / '.gitignore.workflow').exists())
        self.assertFalse((self.project / 'MANIFEST.json').exists())

    def test_install_requires_existing_unity_unless_bootstrap(self):
        with self.assertRaisesRegex(ValueError, 'Unity project'):
            self.install(apply=True)
        self.unity_project()
        before = (self.project / 'ProjectSettings/ProjectVersion.txt').read_bytes()
        result = self.install(apply=True)
        self.assertGreater(result['count'], 0)
        self.assertEqual((self.project / 'ProjectSettings/ProjectVersion.txt').read_bytes(), before)
        self.assertEqual((self.project / 'Packages/manifest.json').read_text(encoding='utf-8'), '{"dependencies":{}}')

    def test_conflict_preflight_copies_nothing(self):
        (self.project / 'AGENTS.md').write_text('Game-specific rules', encoding='utf-8')
        before = list(self.project.iterdir())
        with self.assertRaisesRegex(ValueError, 'Conflicting paths'):
            self.install(bootstrap=True, apply=True)
        self.assertEqual(list(self.project.iterdir()), before)
        self.assertEqual((self.project / 'AGENTS.md').read_text(encoding='utf-8'), 'Game-specific rules')

    def test_identical_files_are_skipped_idempotently(self):
        self.install(bootstrap=True, apply=True)
        result = self.install(bootstrap=True, apply=True)
        self.assertEqual(result['count'], 0)
        self.assertEqual(result['new_files'], [])

    def test_file_as_parent_is_rejected_before_any_copy(self):
        (self.project / 'harness').write_text('not a directory', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'not a directory'):
            self.install(bootstrap=True, apply=True)
        self.assertEqual([p.name for p in self.project.iterdir()], ['harness'])

    def test_source_ancestor_descendant_and_same_are_forbidden(self):
        for target in (self.root, self.root / 'game', self.base):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, 'ancestor/descendant'):
                    resources.install_resources(target, root=self.root, bootstrap=True, apply=True)
        self.assertFalse((self.root / 'game').exists())

    def test_unicode_project_path_and_cli_apply(self):
        self.project = self.base / '游戏 工作流'
        result = self.cli('install', '--project', self.project, '--bootstrap', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'], 'installed')
        self.assertTrue((self.project / 'AGENTS.md').is_file())

    def test_cli_relative_project_is_relative_to_callers_directory(self):
        result = self.cli('install', '--project', 'relative-game', '--bootstrap', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / 'relative-game/harness/scripts/workflow.py').is_file())
        self.assertFalse((self.root / 'relative-game').exists())

    def test_bootstrapped_workflow_check_passes_but_unity_is_not_invented(self):
        self.install(bootstrap=True, apply=True)
        result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(self.project / 'harness/scripts/workflow.py'),
                                 '--root', str(self.project), 'check'],
                                cwd=self.base, capture_output=True, text=True, encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.project / 'Packages').exists())
        self.assertFalse((self.project / 'ProjectSettings').exists())


class SymlinkTests(ResourceWorkspace):
    def test_source_file_symlink_refused(self):
        source = self.template / 'AGENTS.md'
        source.unlink()
        other = self.base / 'rules.md'
        other.write_text('external', encoding='utf-8')
        self.symlink(source, other)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            resources.generate_manifest(self.root)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.install(bootstrap=True, apply=True)

    def test_source_directory_symlink_and_dangling_symlink_refused(self):
        self.symlink(self.template / 'linked', self.base, directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            resources.generate_manifest(self.root)
        (self.template / 'linked').unlink()
        self.symlink(self.template / 'dangling', self.base / 'missing')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            resources.verify(self.root)

    def test_manifest_symlink_refused(self):
        manifest = self.root / 'MANIFEST.json'
        other = self.base / 'manifest.json'
        manifest.rename(other)
        self.symlink(manifest, other)
        for operation in (lambda: resources.generate_manifest(self.root), lambda: resources.verify(self.root)):
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                operation()

    def test_target_directory_and_target_root_symlink_refused(self):
        redirect = self.base / 'redirect'
        redirect.mkdir()
        self.symlink(self.project / 'harness', redirect, directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.install(bootstrap=True, apply=True)
        self.assertFalse(any(redirect.iterdir()))
        (self.project / 'harness').unlink()
        self.project.rmdir()
        self.symlink(self.project, redirect, directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.install(bootstrap=True, apply=True)

    def test_target_existing_identical_symlink_refused(self):
        external = self.base / 'rules'
        external.write_bytes((self.template / 'AGENTS.md').read_bytes())
        self.symlink(self.project / 'AGENTS.md', external)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.install(bootstrap=True, apply=True)

    def test_output_symlink_refused(self):
        redirect = self.base / 'redirect'
        redirect.mkdir()
        self.symlink(self.root / 'dist', redirect, directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            resources.package_skills(root=self.root)
        self.assertFalse(any(redirect.iterdir()))


class VerificationTests(ResourceWorkspace):
    def test_six_required_skills_and_no_license_gate(self):
        self.write('provenance/import.json', '{"license":null,"redistribution_status":"permission_required_before_public_release"}')
        self.assertEqual(resources.verify(self.root)['skills'], 6)
        self.assertFalse((self.root / 'LICENSE').exists())

    def test_required_skill_and_openai_yaml(self):
        shutil.rmtree(self.root / 'skills/design-change')
        resources.generate_manifest(self.root)
        with self.assertRaisesRegex(ValueError, 'six skills'):
            resources.verify(self.root)

    def test_frontmatter_required_and_name_must_match(self):
        for text in ('# no frontmatter', '---\nname: wrong\ndescription: valid\n---\n',
                     '---\nname: design-change\ndescription: \n---\n'):
            self.write('skills/design-change/SKILL.md', text)
            resources.generate_manifest(self.root)
            with self.assertRaisesRegex(ValueError, 'frontmatter'):
                resources.verify(self.root)

    def test_missing_openai_yaml_and_empty_required_field(self):
        path = self.root / 'skills/design-change/agents/openai.yaml'
        path.unlink()
        resources.generate_manifest(self.root)
        with self.assertRaises(OSError):
            resources.verify(self.root)
        self.write('skills/design-change/agents/openai.yaml', 'interface:\n  display_name: "Valid"\n  short_description: ""\n  default_prompt: "Valid"\n')
        resources.generate_manifest(self.root)
        with self.assertRaisesRegex(ValueError, 'short_description'):
            resources.verify(self.root)

    def test_duplicate_frontmatter_fields_are_rejected(self):
        self.write('skills/design-change/SKILL.md', '---\nname: design-change\nname: design-change\ndescription: valid\n---\n')
        resources.generate_manifest(self.root)
        with self.assertRaisesRegex(ValueError, 'Duplicate YAML'):
            resources.verify(self.root)

    def test_json_and_toml_parse_without_external_execution(self):
        self.write('templates/unity-workflow/bomb.py', 'raise RuntimeError("must never execute")\n')
        resources.generate_manifest(self.root)
        with patch.object(resources.subprocess, 'run', side_effect=AssertionError('No external scripts')):
            self.assertEqual(resources.verify(self.root)['status'], 'ok')
        for path, data in (('example.json', '{bad'), ('example.toml', 'key = [bad')):
            with self.subTest(path=path):
                bad = self.write(path, data)
                with self.assertRaises(ValueError):
                    resources.verify(self.root)
                bad.unlink()

    def test_duplicate_json_keys_refused(self):
        self.write('metadata.json', '{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            resources.verify(self.root)

    def test_catalog_optional_and_valid_unresolved_source(self):
        data = {'schema_version': 1, 'verification_date': '2026-11-17', 'resources': [
            {'id': 'reviewed', 'type': 'tool', 'source': 'https://example.invalid/tool', 'status': 'candidate'},
            {'id': 'unknown', 'type': 'provider', 'source': None, 'status': 'unresolved'},
        ]}
        self.write('catalog/resources.json', json.dumps(data))
        result = resources.verify(self.root)
        self.assertEqual(result['catalogs'], 1)

    def test_catalog_observations_only_require_valid_json(self):
        self.write('catalog/skill-observations.json', '{"repositories":[{"name":"candidate"}]}')
        self.write('catalog/tool-observations.json', '{"observations":[{"status":"unresolved"}]}')
        self.assertEqual(resources.verify(self.root)['catalogs'], 0)
        self.write('catalog/skill-observations.json', '{invalid')
        with self.assertRaises(ValueError):
            resources.verify(self.root)

    def test_catalog_requires_fields_and_explicit_unresolved_status(self):
        for item in ({'id': 'x'}, {'id': 'x', 'type': 'tool', 'source': None, 'status': 'available'},
                     {'id': 'x', 'type': 'tool', 'source': '', 'status': 'unresolved'}):
            self.write('catalog/resources.json', json.dumps({'resources': [item]}))
            with self.assertRaisesRegex(ValueError, 'catalog|source'):
                resources.verify(self.root)

    def test_markdown_inline_reference_images_root_and_percent_links(self):
        self.write('docs/a file(1).txt', 'exists')
        self.write('docs/linked.md', '# Target\n')
        self.write('docs/index.md', '''[inline](linked.md#target)
[image](a%20file%281%29.txt)
![image](<a file(1).txt>)
[reference][r]
[r]: linked.md "Title"
[root](/README.md)
[network](https://example.invalid/never-request)
[mail](mailto:example@example.invalid)
[anchor](#heading)
''')
        result = resources.verify(self.root)
        self.assertGreaterEqual(result['markdown_links'], 5)

    def test_markdown_broken_formatted_link_and_image_are_errors(self):
        for link in ('[missing](does-not-exist.md)', '![missing](missing.png)', '[ref]: missing.md'):
            self.write('docs/index.md', link)
            with self.assertRaisesRegex(ValueError, 'Markdown link'):
                resources.verify(self.root)

    def test_plain_paths_code_and_comments_are_not_links(self):
        self.write('docs/index.md', '''Plain relative/nonexistent.md is prose.
`[code](missing.md)`
````markdown
[fenced](missing.md)
````
<!-- [comment](missing.md) -->
''')
        self.assertEqual(resources.verify(self.root)['status'], 'ok')

    def test_markdown_escape_outside_repository_refused(self):
        (self.base / 'outside.md').write_text('exists', encoding='utf-8')
        self.write('README.md', '[escape](../outside.md)')
        with self.assertRaisesRegex(ValueError, 'escaping'):
            resources.verify(self.root)

    def test_cli_manifest_verify_and_invalid_source(self):
        (self.root / 'MANIFEST.json').unlink()
        result = self.cli('manifest')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('verify')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['skills'], 6)
        self.write('templates/unity-workflow/AGENTS.md', 'changed')
        result = self.cli('verify')
        self.assertEqual(result.returncode, 2)
        self.assertIn('SHA256', result.stderr)


class PackagingTests(ResourceWorkspace):
    def test_six_zip_layout_matches_sources_and_fixed_metadata(self):
        self.write('skills/README.md', 'Resource index excluded from archives')
        result = resources.package_skills(root=self.root)
        self.assertEqual(result['count'], 6)
        self.assertEqual(sorted(p.name for p in (self.root / 'dist/skills').iterdir()), [name + '.zip' for name in resources.SKILLS])
        for name, filename in zip(resources.SKILLS, result['archives']):
            with self.subTest(skill=name), zipfile.ZipFile(filename) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                self.assertIn(name + '/SKILL.md', archive.namelist())
                self.assertIn(name + '/agents/openai.yaml', archive.namelist())
                self.assertTrue(all(p.startswith(name + '/') for p in archive.namelist()))
                self.assertEqual(archive.comment, b'')
                for item in archive.infolist():
                    self.assertEqual(item.date_time, resources.ZIP_TIME)
                    self.assertEqual(item.create_system, 3)
                    self.assertEqual(item.external_attr >> 16, stat.S_IFREG | 0o644)
                    self.assertEqual(item.extra, b'')
                    self.assertEqual(archive.read(item), (self.root / 'skills' / item.filename).read_bytes())
        self.assertEqual(resources.verify(self.root)['status'], 'ok')

    def test_zip_bytes_reproducible_across_mtime_and_output_directory(self):
        first = resources.package_skills(root=self.root, out=self.base / 'first')
        for path in resources.walk_files(self.root / 'skills'):
            os.utime(path, (1_234_567_890, 1_234_567_890))
        second = resources.package_skills(root=self.root, out=self.base / 'second')
        for a, b in zip(first['archives'], second['archives']):
            self.assertEqual(Path(a).read_bytes(), Path(b).read_bytes())
        again = resources.package_skills(root=self.root, out=self.base / 'first')
        self.assertEqual(first['archives'], again['archives'])
        for a, b in zip(again['archives'], second['archives']):
            self.assertEqual(Path(a).read_bytes(), Path(b).read_bytes())

    def test_package_requires_current_manifest_and_no_partial_zip(self):
        self.write('skills/design-change/SKILL.md', 'changed')
        output = self.base / 'output'
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            resources.package_skills(root=self.root, out=output)
        self.assertFalse(output.exists())

    def test_output_cannot_be_in_source_trees_or_resource_ancestor(self):
        for output in (self.root, self.base, self.root / 'skills', self.template / 'archives'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                resources.package_skills(root=self.root, out=output)

    def test_cli_package_custom_output(self):
        output = self.base / 'archives'
        result = self.cli('package-skills', '--out', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['count'], 6)
        self.assertEqual(len(list(output.glob('*.zip'))), 6)

    def test_cli_errors_report_stderr(self):
        self.write('bad.json', '{bad')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = resources.main(['verify'], root=self.root)
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('ERROR:', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
