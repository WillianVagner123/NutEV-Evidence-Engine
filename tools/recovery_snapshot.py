"""Lossless snapshot + restore rehearsals of a QUIESCED output tree.

Never restores over production. Caller must stop writers first. The persistent
snapshot remains a complete byte-for-byte copy. The automatic deploy rehearsal
uses a bounded streaming transport proof so it does not require a second full
copy of the scientific volume on the same filesystem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import tempfile
from urllib.parse import quote

DEFAULT_REHEARSAL_CHUNK_BYTES = 8 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError("unsafe filesystem entry")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
    return result


def filesystem_metadata(root: Path) -> dict:
    """Include empty directories and numeric ownership without reading contents."""
    entries = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not (
            stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
        ):
            raise ValueError("unsafe filesystem entry")
        entries[path.relative_to(root).as_posix()] = {
            "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file",
            "mode": stat.S_IMODE(info.st_mode),
            "uid": info.st_uid,
            "gid": info.st_gid,
        }
    return entries


def restore_metadata(root: Path, entries: dict) -> None:
    # Children first so a read-only parent does not prevent restoring its children.
    for name in sorted(
        entries, key=lambda value: len(PurePosixPath(value).parts), reverse=True
    ):
        path = root / name
        entry = entries[name]
        info = path.lstat()
        if (info.st_uid, info.st_gid) != (entry["uid"], entry["gid"]):
            os.chown(path, entry["uid"], entry["gid"], follow_symlinks=False)
        path.chmod(entry["mode"])
    if filesystem_metadata(root) != entries:
        raise ValueError("filesystem metadata restore mismatch")


def safe_destination(source: Path, dest: Path) -> None:
    if source.is_symlink() or dest.is_symlink():
        raise ValueError("symlink root")
    source = source.resolve()
    dest = dest.resolve()
    if dest == source or source in dest.parents or dest in source.parents:
        raise ValueError("overlapping source and destination")
    if dest.exists():
        raise ValueError("destination must not exist")
    if not source.is_dir():
        raise ValueError("source directory required")


def validate_snapshot(backup: Path) -> dict:
    if (
        backup.is_symlink()
        or (backup / "files").is_symlink()
        or (backup / "manifest.json").is_symlink()
    ):
        raise ValueError("symlink snapshot")
    if not (backup / "files").is_dir():
        raise ValueError("snapshot files directory required")
    manifest = json.loads((backup / "manifest.json").read_text())
    if (
        manifest.get("type") != "NUTEV_QUIESCED_SNAPSHOT"
        or manifest.get("version") != 2
    ):
        raise ValueError("unknown snapshot schema")
    for name in {*manifest["files"], *manifest["filesystem"]}:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError("unsafe manifest path")
    if inventory(backup / "files") != manifest["files"]:
        raise ValueError("snapshot integrity mismatch")
    if filesystem_metadata(backup / "files") != manifest["filesystem"]:
        raise ValueError("snapshot filesystem metadata mismatch")
    return manifest


def _database_connection(path: Path, *, read_only: bool) -> sqlite3.Connection:
    if not read_only:
        return sqlite3.connect(path)
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def database_checks(root: Path, *, read_only: bool = False) -> list:
    checks = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        with path.open("rb") as stream:
            header = stream.read(16)
        if header != b"SQLite format 3\x00":
            continue
        # Full restores may recover WAL on an isolated copy. Read-only callers
        # must already be operating on an isolated family because SQLite can
        # legitimately update shared-memory state while reading a WAL database.
        with _database_connection(path, read_only=read_only) as connection:
            if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("database integrity failure")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("database foreign key failure")
            names = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            counts = {
                name: connection.execute(
                    'SELECT count(*) FROM "' + name.replace('"', '""') + '"'
                ).fetchone()[0]
                for name in names
            }
            checks.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "integrity": "ok",
                    "row_counts": counts,
                }
            )
    return checks


def _sqlite_bases(root: Path) -> list[Path]:
    bases = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        with path.open("rb") as stream:
            if stream.read(16) == b"SQLite format 3\x00":
                bases.append(path)
    return bases


def database_checks_isolated_snapshot(root: Path, scratch_parent: Path) -> list:
    """Check snapshot SQLite state without mutating protected DB/WAL/SHM bytes.

    Large DB and WAL files are hard-linked into a same-filesystem scratch family,
    so they consume no second payload copy. The small SHM sidecar is copied because
    SQLite may update shared-memory coordination even for a read-only connection.
    The scratch family is removed after each database check.
    """
    checks = []
    for database in _sqlite_bases(root):
        relative = database.relative_to(root)
        with tempfile.TemporaryDirectory(
            prefix="nutev-sqlite-proof-", dir=scratch_parent
        ) as temp:
            scratch_root = Path(temp)
            target = scratch_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(database, target)

            for suffix in ("-wal", "-journal"):
                source_sidecar = Path(str(database) + suffix)
                if source_sidecar.is_file():
                    os.link(source_sidecar, Path(str(target) + suffix))

            source_shm = Path(str(database) + "-shm")
            if source_shm.is_file():
                shutil.copy2(source_shm, Path(str(target) + "-shm"))

            current = database_checks(scratch_root, read_only=True)
            if len(current) != 1:
                raise ValueError("isolated database rehearsal mismatch")
            checks.extend(current)
    return checks


def rehearse_restore(backup: Path, destination: Path) -> dict:
    """Materialize a complete isolated restore tree.

    This remains the strongest manual/container rehearsal and intentionally needs
    enough free space for a complete second copy of the snapshot.
    """
    manifest = validate_snapshot(backup)
    safe_destination(backup, destination)
    shutil.copytree(backup / "files", destination)
    restore_metadata(destination, manifest["filesystem"])
    if inventory(destination) != manifest["files"]:
        raise ValueError("restore byte mismatch")
    return {
        "status": "PASS",
        "strategy": "FULL_TREE_MATERIALIZATION",
        "files_verified": len(manifest["files"]),
        "databases": database_checks(destination),
        "production_overwritten": False,
        "filesystem_metadata_verified": True,
        "content_transport_verified": True,
    }


def _create_metadata_skeleton(destination: Path, entries: dict) -> None:
    destination.mkdir(parents=True, mode=0o700)
    directories = [
        name for name, entry in entries.items() if entry["kind"] == "directory"
    ]
    for name in sorted(directories, key=lambda value: len(PurePosixPath(value).parts)):
        if name == ".":
            continue
        (destination / name).mkdir(parents=True, exist_ok=True)
    files = [name for name, entry in entries.items() if entry["kind"] == "file"]
    for name in sorted(files):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=False)


def _stream_transport_proof(
    files_root: Path, destination_parent: Path, manifest_files: dict, *, chunk_bytes: int
) -> tuple[int, int]:
    if chunk_bytes <= 0:
        raise ValueError("positive rehearsal chunk size required")
    total_bytes = 0
    peak_payload = 0
    # Reuse one bounded spool. Every byte is written, fsynced and read back, but
    # no second full scientific tree is retained on disk.
    with tempfile.TemporaryFile(dir=destination_parent) as spool:
        for name in sorted(manifest_files):
            source = files_root / name
            expected = manifest_files[name]
            file_bytes = 0
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                while True:
                    chunk = stream.read(chunk_bytes)
                    if not chunk:
                        break
                    digest.update(chunk)
                    spool.seek(0)
                    spool.truncate(0)
                    spool.write(chunk)
                    spool.flush()
                    os.fsync(spool.fileno())
                    spool.seek(0)
                    if spool.read(len(chunk)) != chunk:
                        raise ValueError("restore transport byte mismatch")
                    peak_payload = max(peak_payload, len(chunk))
                    file_bytes += len(chunk)
                    total_bytes += len(chunk)
            if file_bytes != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
                raise ValueError("restore transport manifest mismatch")
    return total_bytes, peak_payload


def rehearse_restore_space_bounded(
    backup: Path,
    destination: Path,
    *,
    chunk_bytes: int = DEFAULT_REHEARSAL_CHUNK_BYTES,
) -> dict:
    """Prove complete restoreability with bounded additional disk usage.

    The protected snapshot is already a complete lossless copy. This rehearsal:
    1) revalidates every snapshot byte and metadata entry;
    2) transports every file byte through a bounded write/fsync/read-back spool;
    3) materializes the full directory/file *structure* as zero-byte placeholders
       and restores/verifies numeric ownership and modes;
    4) checks SQLite/FK/counts through isolated DB/WAL families, copying only SHM;
    5) revalidates the protected snapshot after all database checks.

    It therefore exercises every byte and every path/metadata entry without
    retaining another full-volume copy on the deployment filesystem.
    """
    manifest = validate_snapshot(backup)
    safe_destination(backup, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    transported_bytes, peak_payload = _stream_transport_proof(
        backup / "files",
        destination.parent,
        manifest["files"],
        chunk_bytes=chunk_bytes,
    )

    _create_metadata_skeleton(destination, manifest["filesystem"])
    restore_metadata(destination, manifest["filesystem"])
    databases = database_checks_isolated_snapshot(
        backup / "files", destination.parent
    )
    # SQLite is allowed to touch only scratch SHM. Any mutation of the protected
    # snapshot, including WAL/SHM, is a release-blocking failure.
    if validate_snapshot(backup) != manifest:
        raise ValueError("snapshot changed during database rehearsal")

    return {
        "status": "PASS",
        "strategy": "SPACE_BOUNDED_STREAM_RESTORE_REHEARSAL",
        "files_verified": len(manifest["files"]),
        "bytes_transport_verified": transported_bytes,
        "peak_rehearsal_payload_bytes": peak_payload,
        "databases": databases,
        "production_overwritten": False,
        "filesystem_metadata_verified": True,
        "content_transport_verified": True,
        "snapshot_revalidated_after_database_checks": True,
        "full_tree_materialized": False,
    }


def create_snapshot(source: Path, backup: Path, *, quiesced: bool = False) -> dict:
    if not quiesced:
        raise ValueError("writers must be stopped before snapshot")
    safe_destination(source, backup)
    before = inventory(source)
    metadata = filesystem_metadata(source)
    backup.mkdir(parents=True, mode=0o700)
    shutil.copytree(source, backup / "files", symlinks=False)
    restore_metadata(backup / "files", metadata)
    if (
        inventory(source) != before
        or inventory(backup / "files") != before
        or filesystem_metadata(source) != metadata
    ):
        raise ValueError("source changed during snapshot; no consistent backup produced")
    manifest = {
        "type": "NUTEV_QUIESCED_SNAPSHOT",
        "version": 2,
        "writers_stopped_by_caller": True,
        "files": before,
        "filesystem": metadata,
    }
    path = backup / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    path.chmod(0o600)
    with tempfile.TemporaryDirectory(
        prefix="nutev-restore-proof-", dir=backup.parent
    ) as temp:
        proof = rehearse_restore_space_bounded(backup, Path(temp) / "restored")
    proof_path = backup / "restore-proof.json"
    proof_path.write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    proof_path.chmod(0o600)
    # Do not print private paths, table names, or file contents in CI/deploy logs.
    return {
        "status": "PASS",
        "files_verified": proof["files_verified"],
        "databases_verified": len(proof["databases"]),
        "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "production_overwritten": False,
        "filesystem_metadata_verified": True,
        "restore_rehearsal_strategy": proof["strategy"],
        "peak_rehearsal_payload_bytes": proof["peak_rehearsal_payload_bytes"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--quiesced", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            create_snapshot(args.source, args.backup, quiesced=args.quiesced),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
