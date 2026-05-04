#!/usr/bin/env python3

"""Pangur Bán is a poem written in Old Irish by a copyist (scribe)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import auto, Enum


@dataclass
class Entry:
    name: str
    mode: int
    # TODO: user, group, xattrs



@dataclass
class FileEntry(Entry):
    timestamp: float
    size: int


@dataclass
class DirEntry(Entry):
    entries: list[FileEntry | DirEntry]
    # TODO: user, group, xattrs


@dataclass
class SymlinkEntry(Entry):
    target: str

# TODO: Symlink: relative only, within tree


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

    def compare_times(self, t1: float, t2: float):
        delta = t2 - t1
        if self.modify_window and -self.modify_window <= delta < self.modify_window:
            return 0
        if delta > 0:
            return 1
        elif delta < 0:
            return -1
        else:
            return 0

    def compare_names(self, e1: FileEntry | DirEntry, e2: FileEntry | DirEntry):
        # TODO: case-insensitive, case-preserving, Unicode normalization
        if e1 is None:
            return 1
        elif e2 is None:
            return -1
        if e1.name == e2.name:
            return 0
        elif e1.name < e2.name:
            return -1
        else:
            return +1


def compare_tree(path: str, srcdir: DirEntry, dstdir: DirEntry, policy: Policy):
    srcs = sorted(srcdir.entries, key=lambda e: e.name)
    dsts = sorted(dstdir.entries, key=lambda e: e.name)
    results: list[tuple[str, FileEntry | DirEntry, State]] = []
    i = j = 0

    while i < len(srcs) or j < len(dsts):
        src = srcs[i] if i < len(srcs) else None
        dst = dsts[j] if j < len(dsts) else None
        name_cmp = policy.compare_names(src, dst)

        if name_cmp < 0:
            if isinstance(src, DirEntry):
                # TODO: Pre
                results.extend(
                    compare_tree(
                        path + src.name + "/",
                        src,
                        DirEntry("", mode=0, entries=[]),
                        policy,
                    )
                )
                # TODO: Post
            else:
                results.append((path, src, State.SrcOnly))
            i += 1
        elif name_cmp > 0:
            if isinstance(dst, DirEntry):
                # TODO: Pre
                results.extend(
                    compare_tree(
                        path + dst.name + "/",
                        DirEntry("", mode=0, entries=[]),
                        dst,
                        policy,
                    )
                )
                # TODO: Post
            else:
                results.append((path, dst, State.DstOnly))
            j += 1
        elif name_cmp == 0:
            if isinstance(src, DirEntry) and isinstance(dst, DirEntry):
                # TODO: Pre
                results.extend(compare_tree(path + src.name + "/", src, dst, policy))
                # TODO: Post
            elif isinstance(src, FileEntry) and isinstance(dst, FileEntry):
                time_diff = policy.compare_times(src.timestamp, dst.timestamp)
                if time_diff == 0 and src.size == dst.size:
                    results.append((path, src, State.Same))
                elif time_diff < 0:
                    results.append((path, src, State.SrcNewer))
                elif time_diff > 0:
                    results.append((path, dst, State.DstNewer))
                elif src.size != dst.size:
                    results.append((path, src, State.SizeDiffer))
                else:
                    results.append((path, src, State.Weird))
                # TODO: modes, user, group, etc
            i += 1
            j += 1
        else:
            print(f"Huh: i={i}, j={i}")

    return results
