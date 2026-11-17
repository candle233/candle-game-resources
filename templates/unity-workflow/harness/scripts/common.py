"""Shared local helpers. Python 3.11+, no third-party dependencies."""
from __future__ import annotations
import hashlib, json, os, subprocess, tempfile
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[2]

def now(): return datetime.now(timezone.utc).isoformat()
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def save(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def safe(root, rel):
    root = Path(root).resolve(); rel = str(rel)
    if Path(rel).is_absolute() or "\\" in rel or ":" in rel:
        raise ValueError("Use a relative POSIX path inside this project")
    p = (root / rel).resolve()
    if not p.is_relative_to(root): raise ValueError("Path escapes project root")
    return p

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024*1024), b""): h.update(part)
    return h.hexdigest()

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def fingerprint(root, extra_paths=()):
    root = Path(root).resolve(); c=load(root/"harness/project.json"); entries={}
    for rel in dict.fromkeys(c["fingerprint_paths"] + list(extra_paths)):
        p=safe(root, rel)
        if not p.exists(): entries[rel]="MISSING"; continue
        paths=[p] if p.is_file() else sorted(p.rglob("*"))
        for q in paths:
            if "__pycache__" in q.parts or q.suffix in (".pyc", ".tmp"): continue
            if q.is_symlink(): raise ValueError("Fingerprint roots must not contain symlinks: "+str(q))
            if q.is_file(): entries[q.relative_to(root).as_posix()]=sha(q)
    return digest(entries)

def git_head(root):
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,stderr=subprocess.DEVNULL,text=True,timeout=5).strip()
    except (OSError,subprocess.SubprocessError): return None
