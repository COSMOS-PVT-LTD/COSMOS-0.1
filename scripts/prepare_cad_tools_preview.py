"""Create a task-only preview copy with SQLite online backups; never migrate source."""
import argparse
import json
import shutil
import sqlite3
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,required=True);p.add_argument("--target",type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();target=a.target.resolve();repo=Path(__file__).resolve().parents[1]
    if not source.is_dir() or target.exists() or repo/"output" not in target.parents or source==target:raise ValueError("Existing explicit source and NEW task output target required; no overwrite/migration")
    if any(v.is_symlink() for v in source.rglob("*")):raise ValueError("Preview copy refuses source symlinks")
    shutil.copytree(source,target,ignore=shutil.ignore_patterns("*-wal","*-shm"))
    databases=[]
    for path in source.rglob("*"):
        if path.suffix not in {".sqlite",".sqlite3",".db"}:continue
        with sqlite3.connect(path.as_uri()+"?mode=ro",uri=True) as original,sqlite3.connect(target/path.relative_to(source)) as copied:
            original.backup(copied)
            if copied.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite preview backup failed integrity check")
        databases.append(str(path.relative_to(source)))
    print(json.dumps({"source_unchanged":True,"preview_root":str(target),"sqlite_backups":databases,"runtime_switched_on_source":False}))


if __name__=="__main__":main()
