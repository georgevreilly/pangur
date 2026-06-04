#!/usr/bin/env python3

"""pangur implementation"""

from __future__ import annotations

import datetime
import os
import sys
from dataclasses import dataclass
from enum import Enum, auto
from functools import cmp_to_key


@dataclass
class FileMode:
    mode: int

    def __repr__(self) -> str:
        return f"{self.mode:o}"


@dataclass
class TimeStamp:
    time: float

    def isotime(self) -> str:
        ts = datetime.datetime.fromtimestamp(self.time)
        return ts.strftime("%Y-%m-%dt%H:%M:%S.%f")[:-3]

    __repr__ = isotime


@dataclass
class Entry:
    name: str
    mode: FileMode
    # TODO: user, group, xattrs


@dataclass
class DirEntry(Entry):
    entries: list[Entry]


@dataclass
class FileEntry(Entry):
    mtime: TimeStamp
    size: int  # bytes

    def __repr__(self):
        return f"FileEntry('{self.name}', {self.mode}, {self.mtime}, {self.size})"


@dataclass
class SymlinkEntry(Entry):
    # Symlink: relative only, within tree
    target: str

    def __repr__(self):
        return f"SymlinkEntry('{self.name}', {self.mode:o}, -> '{self.target}')"


class Operation(Enum):
    NoOp = auto()
    SrcCopy = auto()
    DstCopy = auto()
    SrcDelete = auto()
    DstDelete = auto()


class State(Enum):
    Same = auto()
    SrcNewer = auto()
    DstNewer = auto()
    SrcOnly = auto()
    DstOnly = auto()
    SizeDiffer = auto()
    Weird = auto()


@dataclass
class Policy:
    modify_window: int = 0

    def compare_times(self, t1: TimeStamp, t2: TimeStamp):
        delta = t2.time - t1.time
        if self.modify_window and -self.modify_window <= delta < self.modify_window:
            return 0
        if delta > 0:
            return 1
        elif delta < 0:
            return -1
        else:
            return 0

    def compare_names(self, e1: Entry, e2: Entry):
        # TODO: case-insensitive, case-preserving, Unicode normalization
        if e1.name == e2.name:
            return 0
        elif e1.name < e2.name:
            return -1
        else:
            return +1


def compare_entries(policy: Policy, e1: Entry | None, e2: Entry | None):
    if e1 is None:
        return 1 if e2 is not None else 0
    elif e2 is None:
        return -1
    return policy.compare_names(e1, e2)


def compare_tree(path: str, srcdir: DirEntry, dstdir: DirEntry, policy: Policy):
    key_func = cmp_to_key(policy.compare_names)
    srcs = sorted(srcdir.entries, key=key_func)
    dsts = sorted(dstdir.entries, key=key_func)
    results: list[tuple[str, Entry | None, State]] = []
    i = j = 0

    while i < len(srcs) or j < len(dsts):
        src = srcs[i] if i < len(srcs) else None
        dst = dsts[j] if j < len(dsts) else None
        name_cmp = compare_entries(policy, src, dst)

        if name_cmp < 0:
            if isinstance(src, DirEntry):
                # TODO: Pre
                results.extend(
                    compare_tree(
                        path + src.name + "/",
                        src,
                        DirEntry("", mode=FileMode(0), entries=[]),
                        policy,
                    )
                )
                # TODO: Post
            elif isinstance(src, SymlinkEntry):
                # TODO: validate that symlink is relative and within src
                pass
            else:
                results.append((path, src, State.SrcOnly))
            i += 1
        elif name_cmp > 0:
            if isinstance(dst, DirEntry):
                # TODO: Pre
                results.extend(
                    compare_tree(
                        path + dst.name + "/",
                        DirEntry("", mode=FileMode(0), entries=[]),
                        dst,
                        policy,
                    )
                )
                # TODO: Post
            elif isinstance(dst, SymlinkEntry):
                # TODO: validate
                pass
            else:
                results.append((path, dst, State.DstOnly))
            j += 1
        elif name_cmp == 0:
            if isinstance(src, DirEntry) and isinstance(dst, DirEntry):
                # TODO: Pre
                results.extend(compare_tree(path + src.name + "/", src, dst, policy))
                # TODO: Post
            elif isinstance(src, SymlinkEntry) and isinstance(dst, SymlinkEntry):
                # TODO: something
                pass
            elif isinstance(src, FileEntry) and isinstance(dst, FileEntry):
                time_cmp = policy.compare_times(src.mtime, dst.mtime)
                if time_cmp == 0 and src.size == dst.size:
                    results.append((path, src, State.Same))
                elif time_cmp < 0:
                    results.append((path, src, State.SrcNewer))
                elif time_cmp > 0:
                    results.append((path, dst, State.DstNewer))
                elif src.size != dst.size:
                    results.append((path, src, State.SizeDiffer))
                else:
                    results.append((path, src, State.Weird))
                # TODO: modes, user, group, etc
            i += 1
            j += 1
        else:
            print(f"Huh: {path=}, {src=}, {dst=}")

    return results


def walk_tree(root: str) -> DirEntry:
    entries: list[Entry] = []
    for e in os.scandir(root):
        sr = e.stat(follow_symlinks=False)
        if e.is_dir():
            entry = walk_tree(e.path)
        elif e.is_symlink():
            # TODO: capture symlinks only within the tree
            entry = SymlinkEntry(e.name, FileMode(sr.st_mode), os.readlink(e.path))
        else:
            entry = FileEntry(e.name, FileMode(sr.st_mode), TimeStamp(sr.st_mtime), sr.st_size)
        entries.append(entry)
    sr = os.stat(root, follow_symlinks=False)
    return DirEntry(os.path.basename(root), FileMode(sr.st_mode), entries)


if __name__ == "__main__":
    import pprint

    pprint.pprint(walk_tree(sys.argv[1]))
