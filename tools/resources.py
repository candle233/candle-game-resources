#!/usr/bin/env python3
"""Offline resource inventory, verification, create-only installation and skill ZIPs.

Python 3.11+ and the standard library only. Verification is structural/integrity
checking, not authentication, a license grant, or clearance for redistribution.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = PurePosixPath('templates/unity-workflow')
SKILLS = (
    'asset-production', 'design-change', 'release-review',
    'unity-implementation', 'unity-verification', 'workflow-orchestrator',
)
IGNORED_DIRS = frozenset({
    '.git', '.hg', '.svn', '__pycache__', '.pytest_cache', '.mypy_cache',
    '.ruff_cache', '.venv', 'venv',
})
IGNORED_FILES = frozenset({'.DS_Store', 'Thumbs.db', 'desktop.ini'})
IGNORED_SUFFIXES = ('.pyc', '.pyo', '.tmp', '.swp', '.swo', '~')
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def no_symlinks(path):
    """Do not let resolve() conceal a symlink or Windows junction/reparse point."""
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Symlink/reparse point is not allowed: ' + str(candidate))


def resource_root(root):
    root = Path(root)
    no_symlinks(root)
    if not root.is_dir():
        raise ValueError('Resource root is not a directory: ' + str(root))
    return root.resolve()


def ignored(path):
    return path.name in IGNORED_DIRS or path.name in IGNORED_FILES or path.name.endswith(IGNORED_SUFFIXES)


def walk_files(directory, *, repository=False):
    """Sorted, non-following walk. Even a dangling or ignored symlink is refused."""
    no_symlinks(directory)
    if not directory.is_dir():
        raise ValueError('Missing resource directory: ' + str(directory))
    for child in sorted(directory.iterdir(), key=lambda p: p.name):
        no_symlinks(child)
        if ignored(child) or (repository and child.name == 'dist'):
            continue
        if child.is_dir():
            yield from walk_files(child, repository=repository)
        elif child.is_file():
            yield child
        else:
            raise ValueError('Resource is not a regular file: ' + str(child))


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Expected a canonical relative POSIX path: ' + repr(value))
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or path.as_posix() != value or '..' in path.parts:
        raise ValueError('Expected a canonical relative POSIX path: ' + repr(value))
    return value


def unique_paths(paths, label):
    seen = set()
    for path in paths:
        normalized = relative_path(path).casefold()
        if normalized in seen or any(normalized.startswith(p + '/') or p.startswith(normalized + '/') for p in seen):
            raise ValueError('Duplicate/colliding ' + label + ': ' + path)
        seen.add(normalized)


def resource_files(root):
    template = root / TEMPLATE
    for path in walk_files(template):
        rel = path.relative_to(template).as_posix()
        # Superseded archival fragment; .gitignore itself is installed normally.
        if rel == '.gitignore.workflow':
            continue
        yield path, 'harness/README.md' if rel == 'README.md' else rel
    skill_root = root / 'skills'
    no_symlinks(skill_root)
    if not skill_root.is_dir():
        raise ValueError('Missing resource directory: ' + str(skill_root))
    for directory in sorted(skill_root.iterdir(), key=lambda p: p.name):
        no_symlinks(directory)
        # A resource-index README is not a skill and must not be installed.
        if ignored(directory) or not directory.is_dir():
            continue
        for path in walk_files(directory):
            yield path, '.agents/' + path.relative_to(root).as_posix()


def inventory(root):
    files = [
        {'path': path.relative_to(root).as_posix(), 'target': target, 'sha256': sha256(path)}
        for path, target in resource_files(root)
    ]
    files.sort(key=lambda item: item['path'])
    unique_paths((item['path'] for item in files), 'source path')
    unique_paths((item['target'] for item in files), 'mapped target')
    return {'schema_version': 1, 'files': files}


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    no_symlinks(path)
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=_json_object)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(str(path) + ': ' + str(exc)) from exc


def _atomic_json(path, data):
    no_symlinks(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        no_symlinks(path)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def generate_manifest(root=ROOT):
    root = resource_root(root)
    manifest = inventory(root)
    _atomic_json(root / 'MANIFEST.json', manifest)
    return manifest


def verify_manifest(root=ROOT):
    root = resource_root(root)
    manifest = read_json(root / 'MANIFEST.json')
    if not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1:
        raise ValueError('MANIFEST.json: expected schema_version=1')
    entries = manifest.get('files')
    if not isinstance(entries, list):
        raise ValueError('MANIFEST.json: files must be an array')
    for item in entries:
        if not isinstance(item, dict) or not {'path', 'target', 'sha256'} <= item.keys():
            raise ValueError('MANIFEST.json: entries require path, target and sha256')
        relative_path(item['path'])
        relative_path(item['target'])
        if not isinstance(item['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('Invalid manifest SHA256: ' + item['path'])
    unique_paths((item['path'] for item in entries), 'manifest source path')
    unique_paths((item['target'] for item in entries), 'manifest mapped target')
    if [item['path'] for item in entries] != sorted(item['path'] for item in entries):
        raise ValueError('MANIFEST.json: files must be sorted by path')
    expected = {item['path']: item for item in inventory(root)['files']}
    actual = {item['path']: item for item in entries}
    if expected.keys() != actual.keys():
        raise ValueError('Manifest inventory mismatch; missing=' + repr(sorted(expected.keys() - actual.keys()))
                         + ', unexpected=' + repr(sorted(actual.keys() - expected.keys())))
    for path, item in expected.items():
        if actual[path]['target'] != item['target']:
            raise ValueError('Manifest target mapping mismatch: ' + path)
        if actual[path]['sha256'] != item['sha256']:
            raise ValueError('Manifest SHA256 mismatch: ' + path)
    return manifest


def _scalar_fields(lines, indentation=0):
    """Read the required YAML scalar fields, without pretending to be a YAML parser."""
    fields = {}
    for index, line in enumerate(lines):
        match = re.match(r'^ {' + str(indentation) + r'}([a-z_]+):\s*(.*?)\s*$', line)
        if not match:
            continue
        key, value = match.groups()
        if key in fields:
            raise ValueError('Duplicate YAML scalar field: ' + key)
        if value in ('>', '|', '>-', '|-', '>+', '|+'):
            block = []
            for following in lines[index + 1:]:
                if following.strip() and len(following) - len(following.lstrip(' ')) <= indentation:
                    break
                block.append(following.strip())
            value = ' '.join(block).strip()
        elif value.startswith('"'):
            # These files use simple JSON-compatible quoted YAML scalars.
            try:
                value, trailing = json.JSONDecoder().raw_decode(value)
                if trailing < len(match.group(2)) and not match.group(2)[trailing:].lstrip().startswith('#'):
                    raise ValueError('Unexpected text after YAML scalar')
            except (ValueError, TypeError) as exc:
                raise ValueError('Invalid quoted YAML scalar: ' + key) from exc
        elif value.startswith("'"):
            quoted = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", value)
            if not quoted:
                raise ValueError('Invalid quoted YAML scalar: ' + key)
            value = quoted.group(1).replace("''", "'")
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].strip()
        fields[key] = value
    return fields


def verify_skills(root):
    directory = root / 'skills'
    names = sorted(p.name for p in directory.iterdir() if p.is_dir() and not ignored(p))
    if names != list(SKILLS):
        raise ValueError('Expected exactly six skills: ' + ', '.join(SKILLS) + '; found: ' + ', '.join(names))
    for name in SKILLS:
        skill = directory / name
        text = (skill / 'SKILL.md').read_text(encoding='utf-8-sig')
        lines = text.splitlines()
        if not lines or lines[0] != '---' or '---' not in lines[1:]:
            raise ValueError(name + '/SKILL.md: missing YAML frontmatter')
        fields = _scalar_fields(lines[1:lines.index('---', 1)])
        if fields.get('name') != name or not isinstance(fields.get('description'), str) or not fields['description'].strip():
            raise ValueError(name + '/SKILL.md: frontmatter requires matching name and nonempty description')
        yaml_path = skill / 'agents/openai.yaml'
        no_symlinks(yaml_path)
        yaml_lines = yaml_path.read_text(encoding='utf-8-sig').splitlines()
        if 'interface:' not in yaml_lines:
            raise ValueError(str(yaml_path) + ': missing interface')
        start = yaml_lines.index('interface:') + 1
        end = next((i for i in range(start, len(yaml_lines)) if yaml_lines[i] and not yaml_lines[i][0].isspace() and not yaml_lines[i].startswith('#')), len(yaml_lines))
        fields = _scalar_fields(yaml_lines[start:end], 2)
        for key in ('display_name', 'short_description', 'default_prompt'):
            if not isinstance(fields.get(key), str) or not fields[key].strip():
                raise ValueError(str(yaml_path) + ': missing interface.' + key)
    return len(SKILLS)


def _catalog(path, data):
    entries = data.get('resources') if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError(str(path) + ': catalog requires a resources array')
    ids = set()
    for item in entries:
        if not isinstance(item, dict) or not {'id', 'type', 'source', 'status'} <= item.keys():
            raise ValueError(str(path) + ': catalog items require id/type/source/status')
        for key in ('id', 'type', 'status'):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(str(path) + ': nonempty catalog field required: ' + key)
        if item['id'].casefold() in ids:
            raise ValueError(str(path) + ': duplicate catalog id: ' + item['id'])
        ids.add(item['id'].casefold())
        if item['source'] is None:
            if item['status'] != 'unresolved':
                raise ValueError(str(path) + ': null source requires status=unresolved')
        elif not isinstance(item['source'], str) or not item['source'].strip():
            raise ValueError(str(path) + ': source must be a string or unresolved null')


def _markdown_text(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            lines.append('')
        else:
            lines.append(line if fence is None else '')
    text = re.sub(r'<!--.*?-->', '', '\n'.join(lines), flags=re.S)
    return re.sub(r'(`+).*?\1', '', text, flags=re.S)


def _destination(text, start):
    if start >= len(text):
        return ''
    if text[start] == '<':
        end = text.find('>', start + 1)
        return text[start + 1:end] if end >= 0 else ''
    result = []
    depth = 0
    while start < len(text):
        char = text[start]
        if char == '\\' and start + 1 < len(text):
            result.extend(text[start:start + 2])
            start += 2
            continue
        if char.isspace() or (char == ')' and depth == 0):
            break
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        result.append(char)
        start += 1
    return ''.join(result)


def markdown_destinations(text):
    text = _markdown_text(text)
    definitions = {}
    for match in re.finditer(r'^ {0,3}\[([^\]\n]+)\]:\s*(.*)$', text, re.M):
        key = ' '.join(match.group(1).split()).casefold()
        definitions[key] = _destination(match.group(2), 0)
    for match in re.finditer(r'!?\[(?:\\.|[^\]\\\n])*\]\(\s*', text):
        yield _destination(text, match.end())
    for destination in definitions.values():
        yield destination
    # Full/collapsed/shortcut references are covered by checking definitions.


def check_markdown(root, path):
    checked = 0
    for destination in markdown_destinations(path.read_text(encoding='utf-8-sig')):
        destination = html.unescape(re.sub(r'\\([\\`*{}\[\]()#+.!_<> -])', r'\1', destination))
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue  # No network, anchor lookup, or external protocol handling.
        local = unquote(parsed.path)
        candidate = root / local.lstrip('/') if local.startswith('/') else path.parent / local
        no_symlinks(candidate)
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root) or not resolved.exists():
            raise ValueError(str(path.relative_to(root)) + ': broken/escaping local Markdown link: ' + destination)
        checked += 1
    return checked


def verify(root=ROOT):
    root = resource_root(root)
    manifest = verify_manifest(root)
    skill_count = verify_skills(root)
    counts = {'json_files': 0, 'toml_files': 0, 'catalogs': 0, 'markdown_links': 0}
    for path in walk_files(root, repository=True):
        if path.suffix.lower() == '.json':
            data = read_json(path)
            counts['json_files'] += 1
            if path.relative_to(root).as_posix() in ('catalog.json', 'catalog/resources.json'):
                _catalog(path, data)
                counts['catalogs'] += 1
        elif path.suffix.lower() == '.toml':
            try:
                tomllib.loads(path.read_text(encoding='utf-8-sig'))
            except (ValueError, UnicodeError) as exc:
                raise ValueError(str(path) + ': ' + str(exc)) from exc
            counts['toml_files'] += 1
        elif path.suffix.lower() == '.md':
            counts['markdown_links'] += check_markdown(root, path)
    return {'status': 'ok', 'files': len(manifest['files']), 'skills': skill_count, **counts}


def install_resources(project, *, root=ROOT, bootstrap=False, apply=False):
    root = resource_root(root)
    verify_manifest(root)
    # Resolve relative project paths against the caller's cwd, not subprocess cwd.
    project = Path(project).absolute()
    # Installation (unlike verify) runs the reviewed local create-only installer.
    # Its source is the resource root, not the template directory.
    command = [sys.executable, '-I', '-B', '-X', 'utf8', str(root / TEMPLATE / 'harness/scripts/install.py'),
               '--source', str(root), '--project', str(project)]
    if bootstrap:
        command.append('--bootstrap')
    if apply:
        command.append('--apply')
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', cwd=root, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Create-only installer failed')
    return json.loads(result.stdout)


def package_skills(*, root=ROOT, out=None):
    root = resource_root(root)
    verify(root)
    out = Path(out) if out is not None else root / 'dist/skills'
    no_symlinks(out)
    out = out.resolve()
    if out == root or root.is_relative_to(out) or any(out.is_relative_to(root / p) for p in ('skills', 'templates')):
        raise ValueError('ZIP output must not replace or be inside source resources')
    for name in SKILLS:
        archive = out / (name + '.zip')
        no_symlinks(archive)
        if archive.exists() and not archive.is_file():
            raise ValueError('ZIP output is not a regular file: ' + str(archive))
    # Read and pin all bytes before writing any archive.
    manifest = verify_manifest(root)
    payloads = {name: [] for name in SKILLS}
    for item in manifest['files']:
        parts = PurePosixPath(item['path']).parts
        if parts[0] != 'skills':
            continue
        path = root / item['path']
        no_symlinks(path)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Source changed during packaging: ' + item['path'])
        payloads[parts[1]].append(('/'.join(parts[1:]), data))
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.resources-zips-', dir=out) as temporary:
        for name, files in payloads.items():
            with zipfile.ZipFile(Path(temporary) / (name + '.zip'), 'w', compression=zipfile.ZIP_STORED) as archive:
                for arcname, data in sorted(files):
                    info = zipfile.ZipInfo(arcname, date_time=ZIP_TIME)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    info.compress_type = zipfile.ZIP_STORED
                    archive.writestr(info, data)
        for name in SKILLS:
            target = out / (name + '.zip')
            no_symlinks(target)
            os.replace(Path(temporary) / target.name, target)
    return {'status': 'ok', 'archives': [str(out / (name + '.zip')) for name in SKILLS], 'count': len(SKILLS)}


def main(argv=None, *, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('manifest', help='Regenerate root MANIFEST.json from local resources')
    installer = commands.add_parser('install', help='Create-only overlay; dry-run unless --apply is supplied')
    installer.add_argument('--project', type=Path, required=True)
    installer.add_argument('--bootstrap', action='store_true', help='Allow workflow setup before a Unity project exists')
    installer.add_argument('--apply', action='store_true')
    commands.add_parser('verify', help='Check structure, hashes and local links without executing scripts')
    packager = commands.add_parser('package-skills', help='Create six reproducible, offline skill ZIPs')
    packager.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'manifest':
            manifest = generate_manifest(root)
            result = {'status': 'ok', 'manifest': str(Path(root) / 'MANIFEST.json'), 'count': len(manifest['files'])}
        elif args.command == 'verify':
            result = verify(root)
        elif args.command == 'install':
            result = install_resources(args.project, root=root, bootstrap=args.bootstrap, apply=args.apply)
        else:
            result = package_skills(root=root, out=args.out)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
