import pytest

from ..pangur import compare_tree, FileEntry, DirEntry, State


def check_expected(actual, expected):
    results = [(path, e.name, state) for path, e, state in actual]
    assert results == expected


def test_pangur_same():
    src_dir = DirEntry("/", entries=[
        FileEntry("foo", 1000, 500, 0o664),
        FileEntry("bar", 2000, 800, 0o664),
    ])
    actual = compare_tree("/", src_dir, src_dir)
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.Same)])


def test_pangur_newer():
    src_dir = DirEntry("/", entries=[
        FileEntry("foo", 3000, 500, 0o664),
        FileEntry("bar", 2000, 800, 0o664),
    ])
    dst_dir = DirEntry("/", entries=[
        FileEntry("foo", 1000, 500, 0o664),
        FileEntry("bar", 2000, 800, 0o664),
    ])
    actual = compare_tree("/", src_dir, dst_dir)
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.SrcNewer)])


def test_pangur_newer_more():
    src_dir = DirEntry("/", entries=[
        FileEntry("foo", 3000, 500, 0o664),
        FileEntry("baz", 5000, 800, 0o664),
        FileEntry("bar", 2000, 800, 0o664),
        FileEntry("miz", 6000, 800, 0o664),
        FileEntry("wiz", 6000, 800, 0o664),
    ])
    dst_dir = DirEntry("/", entries=[
        FileEntry("foo", 1000, 500, 0o664),
        FileEntry("bar", 2000, 800, 0o664),
        FileEntry("quux", 4000, 800, 0o664),
    ])
    actual = compare_tree("/", src_dir, dst_dir)
    check_expected(actual, [
        ("/", "bar", State.Same),
        ("/", "baz", State.SrcOnly),
        ("/", "foo", State.SrcNewer),
        ("/", "miz", State.SrcOnly),
        ("/", "quux", State.DstOnly),
        ("/", "wiz", State.SrcOnly),
    ])
