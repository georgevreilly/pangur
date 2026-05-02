import pytest

from ..pangur import compare_tree, FileEntry, DirEntry, State, Policy


def check_expected(actual, expected):
    results = [(path, e.name, state) for path, e, state in actual]
    assert results == expected


def test_pangur_same():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, src_dir, Policy())
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.Same)])


def test_pangur_newer():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.SrcNewer)])


def test_pangur_newer_more():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            FileEntry("baz", 5000, 800, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
            FileEntry("miz", 6000, 800, 0o664),
            FileEntry("wiz", 6000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
            FileEntry("quux", 4000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(
        actual,
        [
            ("/", "bar", State.Same),
            ("/", "baz", State.SrcOnly),
            ("/", "foo", State.SrcNewer),
            ("/", "miz", State.SrcOnly),
            ("/", "quux", State.DstOnly),
            ("/", "wiz", State.SrcOnly),
        ],
    )


def test_pangur_updated_subdir():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            DirEntry(
                "baz",
                mode=0o775,
                entries=[
                    FileEntry("alpha", 6000, 500, 0o664),
                    FileEntry("beta", 5000, 500, 0o664),
                ],
            ),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            DirEntry(
                "baz",
                mode=0o775,
                entries=[
                    FileEntry("alpha", 4000, 500, 0o664),
                    FileEntry("beta", 5000, 500, 0o664),
                ],
            ),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(
        actual,
        [
            ("/", "bar", State.Same),
            ("/baz/", "alpha", State.SrcNewer),
            ("/baz/", "beta", State.Same),
            ("/", "foo", State.SrcNewer),
        ],
    )


def test_pangur_new_subdir():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            DirEntry(
                "baz",
                mode=0o775,
                entries=[
                    FileEntry("alpha", 6000, 500, 0o664),
                    FileEntry("beta", 5000, 500, 0o664),
                ],
            ),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(
        actual,
        [
            ("/", "bar", State.Same),
            ("/baz/", "alpha", State.SrcOnly),
            ("/baz/", "beta", State.SrcOnly),
            ("/", "foo", State.SrcNewer),
        ],
    )


def test_pangur_nested_subdirs():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            DirEntry(
                "baz",
                mode=0o775,
                entries=[
                    FileEntry("alpha", 6000, 500, 0o664),
                    DirEntry(
                        "beta",
                        mode=0o775,
                        entries=[
                            DirEntry(
                                "gamma",
                                mode=0o775,
                                entries=[
                                    FileEntry("kappa", 6000, 500, 0o664),
                                    FileEntry("lambda", 6000, 500, 0o664),
                                ],
                            ),
                            FileEntry("epsilon", 6000, 500, 0o664),
                            FileEntry("omega", 6000, 500, 0o664),
                        ],
                    ),
                ],
            ),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(
        actual,
        [
            ("/", "bar", State.Same),
            ("/baz/", "alpha", State.SrcOnly),
            ("/baz/beta/", "epsilon", State.SrcOnly),
            ("/baz/beta/gamma/", "kappa", State.SrcOnly),
            ("/baz/beta/gamma/", "lambda", State.SrcOnly),
            ("/baz/beta/", "omega", State.SrcOnly),
            ("/", "foo", State.SrcNewer),
        ],
    )


def test_pangur_removed_subdir():
    src_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 3000, 500, 0o664),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    dst_dir = DirEntry(
        "/",
        mode=0o755,
        entries=[
            FileEntry("foo", 1000, 500, 0o664),
            DirEntry(
                "baz",
                mode=0o775,
                entries=[
                    FileEntry("alpha", 6000, 500, 0o664),
                    FileEntry("beta", 5000, 500, 0o664),
                ],
            ),
            FileEntry("bar", 2000, 800, 0o664),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(
        actual,
        [
            ("/", "bar", State.Same),
            ("/baz/", "alpha", State.DstOnly),
            ("/baz/", "beta", State.DstOnly),
            ("/", "foo", State.SrcNewer),
        ],
    )
