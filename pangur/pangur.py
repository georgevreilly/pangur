#!/usr/bin/env python3

"""Pangur Bán is a poem written in Old Irish by a copyist (scribe)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import auto, Enum


@dataclass
class FileEntry:
    name: str
    timestamp: float
    size: int
    mode: int
    # TODO: user, group, xattrs


@dataclass
class DirEntry:
    name: str
    mode: int
    entries: list[FileEntry | DirEntry]
    # TODO: user, group, xattrs


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

    def compare_time(self, t1: float, t2: float):
        delta = t2 - t1
        if self.modify_window and -self.modify_window <= delta < self.modify_window:
            return 0
        if delta > 0:
            return 1
        elif delta < 0:
            return -1
        else:
            return 0

    def compare_names(self, n1: str, n2: str):
        # TODO: case-insensitive, case-preserving, Unicode normalization
        if n1 == n2:
            return 0
        elif n1 < n2:
            return -1
        else:
            return +1


def compare_tree(path: str, srcdir: DirEntry, dstdir: DirEntry, policy: Policy):
    srcs = sorted(srcdir.entries, key=lambda e: e.name)
    dsts = sorted(dstdir.entries, key=lambda e: e.name)
    results: list[tuple[str, FileEntry | DirEntry, State]] = []
    i = j = 0
    while i < len(srcs) and j < len(dsts):
        src = srcs[i]
        dst = dsts[j]
        name_cmp = policy.compare_names(src.name, dst.name)
        if name_cmp < 0:
            if isinstance(src, DirEntry):
                # TODO: Pre
                results.extend(
                    compare_tree(
                        path + src.name + "/",
                        src,
                        DirEntry(".", mode=0, entries=[]),
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
                        DirEntry(".", mode=0, entries=[]),
                        dst,
                        policy,
                    )
                )
                # TODO: Post
            else:
                results.append((path, dst, State.DstOnly))
            # TODO: DirEntry
            j += 1
        elif name_cmp == 0:
            if isinstance(src, DirEntry) and isinstance(dst, DirEntry):
                # TODO: Pre
                results.extend(compare_tree(path + src.name + "/", src, dst, policy))
                # TODO: Post
            elif isinstance(src, FileEntry) and isinstance(dst, FileEntry):
                time_diff = policy.compare_time(src.timestamp, dst.timestamp)
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
            i += 1
            j += 1
        else:
            print(f"Huh: i={i}, j={i}")

    while i < len(srcs):
        results.append((path, srcs[i], State.SrcOnly))
        i += 1
    while j < len(dsts):
        results.append((path, dsts[j], State.DstOnly))
        j += 1

    return results
