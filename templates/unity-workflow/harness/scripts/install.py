#!/usr/bin/env python3
"""Create-only overlay installer. Conflicts are detected before any file is copied."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load, safe, sha

DIST_ONLY = ('package-reports/', 'skill-packages/')


def _no_symlinks(path):
    """Check the lexical path before resolve() can hide a redirect (also junctions)."""
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Symlink/reparse point is not allowed: ' + str(candidate))


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Use a relative POSIX path inside this project')
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(p in ('.', '..') for p in path.parts):
        raise ValueError('Use a canonical relative POSIX path inside this project: ' + value)
    if not path.parts:
        raise ValueError('An empty mapped path is not allowed')
    return value


def _manifest(source):
    _no_symlinks(source / 'MANIFEST.json')
    manifest = load(source / 'MANIFEST.json')
    if not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1:
        raise ValueError('Unknown package manifest')
    if not isinstance(manifest.get('files'), list):
        raise ValueError('Package manifest files must be an array')
    seen = set()
    for item in manifest['files']:
        if not isinstance(item, dict):
            raise ValueError('Invalid package manifest entry')
        rel = _relative(item.get('path'))
        digest = item.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid package SHA256: ' + rel)
        if rel.casefold() in seen:
            raise ValueError('Duplicate package path: ' + rel)
        seen.add(rel.casefold())
        if 'target' in item:
            _relative(item['target'])
    return manifest


def _target_path(path):
    _no_symlinks(path)
    for ancestor in path.parents:
        if ancestor.exists() and not ancestor.is_dir():
            raise ValueError('Target parent is not a directory: ' + str(ancestor))


def package_plan(source, target, allow_bootstrap=False):
    source = Path(source)
    target = Path(target)
    _no_symlinks(source)
    _no_symlinks(target)
    source = source.resolve()
    target = target.resolve()
    if target == source or target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError('Extract package outside the target project; do not install into an ancestor/descendant of the package')
    if not source.is_dir():
        raise ValueError('Package source is not a directory')
    if target.exists() and not target.is_dir():
        raise ValueError('Target project is not a directory')
    for rel in (() if allow_bootstrap else ('Assets', 'Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt')):
        path = target / rel
        _no_symlinks(path)
        if not (path.is_dir() if rel == 'Assets' else path.is_file()):
            raise ValueError('Target is not an existing Unity project: missing ' + rel)
    manifest = _manifest(source)
    plan = []
    conflicts = []
    targets = set()
    for item in manifest['files']:
        rel = item['path']
        _no_symlinks(source / rel)
        src = safe(source, rel)
        if not src.is_file() or sha(src) != item['sha256']:
            raise ValueError('Package integrity failure: ' + rel)
        if rel.startswith(DIST_ONLY):
            continue
        outrel = _relative(item.get('target', 'harness/README.md' if rel == 'README.md' else rel))
        normalized = outrel.casefold()
        if normalized in targets or any(normalized.startswith(p + '/') or p.startswith(normalized + '/') for p in targets):
            raise ValueError('Duplicate mapped target or file/directory collision: ' + outrel)
        targets.add(normalized)
        # Bootstrap adds workflow files, never an invented Unity project/version.
        if allow_bootstrap and normalized.split('/')[0] in ('packages', 'projectsettings'):
            raise ValueError('Bootstrap cannot create Unity Packages or ProjectSettings: ' + outrel)
        dest = target / outrel
        _target_path(dest)
        if dest.exists():
            if not dest.is_file() or sha(dest) != item['sha256']:
                conflicts.append(outrel)
        else:
            plan.append((src, dest))
    if conflicts:
        raise ValueError('No files copied. Conflicting paths:\n' + '\n'.join(conflicts))
    return plan


def install(source, target, dry_run=True, allow_bootstrap=False):
    source = Path(source)
    target = Path(target)
    _no_symlinks(source)
    # Pin the manifest before preflight. Never compare copied bytes to a second
    # hash of the same (possibly changed) source file.
    root = source.resolve()
    expected = {root / item['path']: item['sha256'] for item in _manifest(root)['files']}
    plan = package_plan(source, target, allow_bootstrap)
    if not dry_run:
        created = []
        try:
            for src, dest in plan:
                _no_symlinks(src)
                data = src.read_bytes()
                if hashlib.sha256(data).hexdigest() != expected.get(src):
                    raise ValueError('Source changed during installation: ' + str(src))
                _target_path(dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                _target_path(dest)
                with dest.open('xb') as stream:
                    created.append(dest)
                    stream.write(data)
        except Exception:
            for dest in reversed(created):
                dest.unlink(missing_ok=True)
            raise
    return [str(dest.relative_to(target.resolve())) for _, dest in plan]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--bootstrap', action='store_true')
    p.add_argument('--apply', action='store_true')
    a = p.parse_args(argv)
    try:
        paths = install(a.source, a.project, not a.apply, a.bootstrap)
        print(json.dumps({'mode': 'installed' if a.apply else 'dry-run', 'new_files': paths, 'count': len(paths)}, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
