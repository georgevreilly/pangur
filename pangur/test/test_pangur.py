from ..pangur import (
    DirInfo,
    FileInfo,
    FileMode,
    Policy,
    State,
    TimeStamp,
    compare_entries,
    compare_tree,
)

FileMode_File = FileMode(0o644)
FileMode_Dir = FileMode(0o755)


def check_expected(actual, expected):
    results = [(path, e.name, state) for path, e, state in actual]
    assert results == expected


def test_compare_entries():
    policy = Policy()
    foo = FileInfo("foo", FileMode_File, TimeStamp(1000), 500)
    bar = FileInfo("bar", FileMode_File, TimeStamp(2000), 800)
    assert 0 == compare_entries(policy, foo, foo)
    assert 0 == compare_entries(policy, None, None)
    assert +1 == compare_entries(policy, None, foo)
    assert -1 == compare_entries(policy, bar, None)
    assert -1 == compare_entries(policy, bar, foo)
    assert +1 == compare_entries(policy, foo, bar)


def test_pangur_same():
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("/", src_dir, src_dir, Policy())
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.Same)])


def test_pangur_newer():
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("/", src_dir, dst_dir, Policy())
    check_expected(actual, [("/", "bar", State.Same), ("/", "foo", State.SrcNewer)])


def test_pangur_newer_more():
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            FileInfo("baz", FileMode_File, TimeStamp(5000), 800),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
            FileInfo("miz", FileMode_File, TimeStamp(6000), 800),
            FileInfo("wiz", FileMode_File, TimeStamp(6000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
            FileInfo("quux", FileMode_File, TimeStamp(4000), 800),
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
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode(0o775),
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            DirInfo(
                "baz",
                mode=FileMode(0o775),
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(4000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
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
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode(0o775),
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 50),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
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
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode(0o775),
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    DirInfo(
                        "beta",
                        mode=FileMode(0o775),
                        entries=[
                            DirInfo(
                                "gamma",
                                mode=FileMode(0o775),
                                entries=[
                                    FileInfo("kappa", FileMode_File, TimeStamp(6000), 500),
                                    FileInfo("lambda", FileMode_File, TimeStamp(6000), 500),
                                ],
                            ),
                            FileInfo("epsilon", FileMode_File, TimeStamp(6000), 500),
                            FileInfo("omega", FileMode_File, TimeStamp(6000), 500),
                        ],
                    ),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
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
    src_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "/",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            DirInfo(
                "baz",
                mode=FileMode(0o775),
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
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
