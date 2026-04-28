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


@dataclass
class DirEntry:
    name: str
    entries: list[ FileEntry | DirEntry]


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


def compare_time(ts1: float, ts2: float, window: float = 0.0):
    diff = ts2 - ts1
    if diff > window:
        return 1
    elif diff < -window:
        return -1
    else:
        return 0


def compare_tree(path: str, srcdir: DirEntry, dstdir: DirEntry, window: float = 0.0):
    srcs = sorted(srcdir.entries, key=lambda e: e.name)
    dsts = sorted(dstdir.entries, key=lambda e: e.name)
    results: list[tuple[str, FileEntry | DirEntry, State]] = []
    i = j = 0
    while i < len(srcs) and j < len(dsts):
        src = srcs[i]
        dst = dsts[j]
        if src.name < dst.name:
            results.append((path, src, State.SrcOnly))
            i += 1
        elif src.name > dst.name:
            results.append((path, dst, State.DstOnly))
            j += 1
        elif src.name == dst.name:
            if isinstance(src, DirEntry) and isinstance(dst, DirEntry):
                results.extend(compare_tree(path + "/" + src.name, src, dst, window))
            elif isinstance(src, FileEntry) and isinstance(dst, FileEntry):
                time_diff = compare_time(src.timestamp, dst.timestamp, window)
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
            i += 1; j += 1
        else:
            print(f"Huh: i={i}, j={i}")

    while i < len(srcs):
        results.append((path, srcs[i], State.SrcOnly))
        i += 1
    while j < len(dsts):
        results.append((path, dsts[j], State.DstOnly))
        j += 1

    return results
