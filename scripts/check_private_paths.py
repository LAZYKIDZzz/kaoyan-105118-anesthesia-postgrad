#!/usr/bin/env python3
"""Reject local home paths without printing their contents. Standard library only."""

import argparse
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIVATE_DIR = ".privacy-local"
PATH_PATTERNS = (
    re.compile(r"(?<![\w:/])/(?:Users|home)/[^\s/\\\"'<>]+(?=/|[\s\"'<>]|$)", re.I),
    re.compile(r"(?<![\w])(?:[A-Z]:[\\/]|\\\\)[Uu]sers[\\/][^\s\\/\"'<>]+", re.I),
    re.compile(r"file:///(?:Users|home)/[^\s/\\\"'<>]+", re.I),
)
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def private_terms():
    path = ROOT / PRIVATE_DIR / "blocked-terms.txt"
    if not path.is_file():
        return []
    return [line.strip().casefold() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def public_source_hashes():
    path = ROOT / ".privacy-public-sources.json"
    if not path.is_file():
        return set()
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["sha256"] for entry in entries}


def text_views(data):
    yield data.decode("utf-8", errors="replace")
    if b"\x00" in data:
        for encoding in ("utf-16-le", "utf-16-be"):
            yield data.decode(encoding, errors="replace")


def scan(data, label, terms=(), depth=0, approved_hashes=(), approved_source=False):
    """Return locations/categories only; matched values must never reach logs."""
    findings = set()
    approved_source = approved_source or hashlib.sha256(data).hexdigest() in approved_hashes
    for text in text_views(data):
        for pattern in PATH_PATTERNS:
            if approved_source:
                continue
            for match in pattern.finditer(text):
                # ASP.NET URLs can contain parentheses before their home segment.
                if re.search(r"https?://[^\s\"'<>]*$", text[:match.start()], re.I):
                    continue
                findings.add((label, text.count("\n", 0, match.start()) + 1, "local home path"))
        folded = text.casefold()
        for term in terms:
            pos = folded.find(term)
            if pos >= 0:
                findings.add((label, folded.count("\n", 0, pos) + 1, "local private term"))
    if zipfile.is_zipfile(io.BytesIO(data)):
        if depth >= 4:
            findings.add((label, 0, "archive nesting limit; manual review required"))
            return findings
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(info.file_size for info in archive.infolist()) > MAX_ARCHIVE_BYTES:
                    findings.add((label, 0, "archive size limit; manual review required"))
                    return findings
                for info in archive.infolist():
                    member = label + "!" + info.filename
                    findings.update(scan(info.filename.encode("utf-8"), member, terms))
                    if not info.is_dir():
                        findings.update(scan(archive.read(info), member, terms, depth + 1,
                                             approved_hashes, approved_source))
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, NotImplementedError):
            findings.add((label, 0, "unreadable archive; manual review required"))
    return findings


def safe_label(label, terms):
    for term in terms:
        label = re.sub(re.escape(term), "[private]", label, flags=re.I)
    for pattern in PATH_PATTERNS:
        label = pattern.sub("[private-path]", label)
    return label


def index_entries(staged):
    changed = None
    if staged:
        changed = set(git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").split(b"\0"))
    for record in git("ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        metadata, filename = record.split(b"\t", 1)
        mode, sha, stage = metadata.split()
        if changed is not None and filename not in changed:
            continue
        if stage != b"0":
            raise ValueError("resolve unmerged index entries first")
        if mode == b"160000":
            continue
        yield sha.decode("ascii"), filename.decode("utf-8", errors="replace")


def history_entries():
    # Private editor snapshots/backups are local; inspect refs that can be published.
    for record in git("rev-list", "--objects", "--branches", "--tags", "--remotes", "HEAD", "--").splitlines():
        sha, _, filename = record.partition(b" ")
        yield sha.decode("ascii"), filename.decode("utf-8", errors="replace") or "commit metadata"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true", help="scan exactly the staged Git blobs")
    modes.add_argument("--history", action="store_true", help="also scan branch, tag and remote-tracking history")
    args = parser.parse_args(argv)
    terms = private_terms()
    approved_hashes = public_source_hashes()
    findings = set()
    entries = list(index_entries(args.staged))
    if args.history:
        entries.extend(history_entries())
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
    checked = set()
    try:
        for sha, filename in entries:
            findings.update(scan(filename.encode("utf-8"), filename, terms))
            if PRIVATE_DIR in pathlib.PurePosixPath(filename).parts:
                findings.add((filename, 0, "private configuration must not be tracked"))
            if sha in checked:
                continue
            checked.add(sha)
            process.stdin.write((sha + "\n").encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3:
                raise ValueError("cannot read Git object")
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            if len(data) != size:
                raise ValueError("incomplete Git object")
            if header[1] in (b"blob", b"commit", b"tag"):
                findings.update(scan(data, filename, terms, approved_hashes=approved_hashes))
    finally:
        process.stdin.close()
        process.stdout.close()
        if process.wait() != 0:
            raise ValueError("Git object reader failed")
    if findings:
        print("Privacy check failed. Matched values are withheld.", file=sys.stderr)
        for label, line, category in sorted(findings):
            print(f"  {safe_label(label, terms)}:{line}: {category}", file=sys.stderr)
        return 1
    print(f"Privacy check passed ({len(checked)} unique Git objects).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("Privacy check could not finish; resolve Git/index/configuration errors before retrying.",
              file=sys.stderr)
        sys.exit(2)
