from ..pangur import (
    DirInfo,
    FileInfo,
    FileMode,
    InfoEntry,
    Operation,
    PathOperation,
    PathState,
    Policy,
    State,
    TimeStamp,
    compare_entries,
    compare_tree,
    compute_operations,
)

FileMode_File = FileMode(0o644)
FileMode_Dir = FileMode(0o755)


def check_expected_path_states(actual: list[PathState], expected):
    results = [(a.path, a.entry.name, a.state, a.count) for a in actual]
    assert results == expected


def check_expected_path_operations(actual: list[PathOperation], expected):
    results = [(a.path, a.entry.name, a.operation) for a in actual]
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


def test_modify_window():
    policy0 = Policy(modify_window=0)
    t0 = TimeStamp(1000)
    t1 = TimeStamp(1500)
    t2 = TimeStamp(2100)
    assert 0 == policy0.compare_times(t0, t0)
    assert -1 == policy0.compare_times(t0, t1)
    assert +1 == policy0.compare_times(t1, t0)

    policy1 = Policy(modify_window=1000)
    assert 0 == policy1.compare_times(t0, t0)
    assert 0 == policy1.compare_times(t0, t1)
    assert 0 == policy1.compare_times(t1, t0)
    assert -1 == policy0.compare_times(t0, t2)
    assert +1 == policy0.compare_times(t2, t0)


def test_pangur_same():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, src_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 0),
            ("", "bar", State.Same, -1),
            ("", "foo", State.Same, -1),
            ("", "", State.DirLeave, 0),
        ],
    )


def test_pangur_newer():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 1),
            ("", "bar", State.Same, -1),
            ("", "foo", State.SrcNewer, -1),
            ("", "", State.DirLeave, 0),
        ],
    )


def test_pangur_newer_more():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),  # updated
            FileInfo("baz", FileMode_File, TimeStamp(5000), 800),  # new
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),  # same
            FileInfo("miz", FileMode_File, TimeStamp(6000), 800),  # new
            FileInfo("wiz", FileMode_File, TimeStamp(6000), 800),  # new
        ],
    )
    dst_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),  # old
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),  # same
            FileInfo("quux", FileMode_File, TimeStamp(4000), 800),  # removed
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 4),
            ("", "bar", State.Same, -1),
            ("", "baz", State.SrcOnly, -1),
            ("", "foo", State.SrcNewer, -1),
            ("", "miz", State.SrcOnly, -1),
            ("", "quux", State.DstOnly, -1),
            ("", "wiz", State.SrcOnly, -1),
            ("", "", State.DirLeave, 1),  # quux
        ],
    )


def test_pangur_updated_subdir():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode_Dir,
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            DirInfo(
                "baz",
                mode=FileMode_Dir,
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(4000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 1),
            ("", "bar", State.Same, -1),
            ("", "baz", State.DirEnter, 1),
            ("baz", "alpha", State.SrcNewer, -1),
            ("baz", "beta", State.Same, -1),
            ("", "baz", State.DirLeave, 0),
            ("", "foo", State.SrcNewer, -1),
            ("", "", State.DirLeave, 0),
        ],
    )


def test_pangur_new_subdir():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode_Dir,
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 50),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 2),
            ("", "bar", State.Same, -1),
            ("", "baz", State.DirEnter, 2),
            ("baz", "alpha", State.SrcOnly, -1),
            ("baz", "beta", State.SrcOnly, -1),
            ("", "baz", State.DirLeave, 0),
            ("", "foo", State.SrcNewer, -1),
            ("", "", State.DirLeave, 0),
        ],
    )


def test_pangur_nested_subdirs():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            DirInfo(
                "baz",
                mode=FileMode_Dir,
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    DirInfo(
                        "beta",
                        mode=FileMode_Dir,
                        entries=[
                            DirInfo(
                                "gamma",
                                mode=FileMode_Dir,
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
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 2),
            ("", "bar", State.Same, -1),
            ("", "baz", State.DirEnter, 2),
            ("baz", "alpha", State.SrcOnly, -1),
            ("baz", "beta", State.DirEnter, 3),
            ("baz/beta", "epsilon", State.SrcOnly, -1),
            ("baz/beta", "gamma", State.DirEnter, 2),
            ("baz/beta/gamma", "kappa", State.SrcOnly, -1),
            ("baz/beta/gamma", "lambda", State.SrcOnly, -1),
            ("baz/beta", "gamma", State.DirLeave, 0),
            ("baz/beta", "omega", State.SrcOnly, -1),
            ("baz", "beta", State.DirLeave, 0),
            ("", "baz", State.DirLeave, 0),
            ("", "foo", State.SrcNewer, -1),
            ("", "", State.DirLeave, 0),
        ],
    )


def test_pangur_removed_subdir():
    src_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(3000), 500),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    dst_dir = DirInfo(
        "",
        mode=FileMode_Dir,
        entries=[
            FileInfo("foo", FileMode_File, TimeStamp(1000), 500),
            DirInfo(  # not present in src
                "baz",
                mode=FileMode_Dir,
                entries=[
                    FileInfo("alpha", FileMode_File, TimeStamp(6000), 500),
                    FileInfo("beta", FileMode_File, TimeStamp(5000), 500),
                ],
            ),
            FileInfo("bar", FileMode_File, TimeStamp(2000), 800),
        ],
    )
    actual = compare_tree("", src_dir, dst_dir, Policy())
    check_expected_path_states(
        actual,
        [
            ("", "", State.DirEnter, 1),
            ("", "bar", State.Same, -1),
            ("", "baz", State.DirEnter, 0),
            ("baz", "alpha", State.DstOnly, -1),
            ("baz", "beta", State.DstOnly, -1),
            ("", "baz", State.DirLeave, 2),  # alpha, beta
            ("", "foo", State.SrcNewer, -1),
            ("", "", State.DirLeave, 1),  # baz
        ],
    )


def make_path_states(data: list[tuple[str, str, State, int]]) -> list[PathState]:
    path_states = []
    for p, n, s, c in data:
        if s in (State.DirEnter, State.DirLeave):
            e = DirInfo(n, FileMode_Dir, [])
        else:
            e = FileInfo(n, FileMode_File, TimeStamp(0), 0)
        path_states.append(PathState(p, e, s, c))
    return path_states


def test_compute_operations():
    path_states = make_path_states([
        ("", "", State.DirEnter, 2),
        ("", "bar", State.Same, -1),
        ("", "baz", State.DirEnter, 2),
        ("baz", "alpha", State.SrcOnly, -1),
        ("baz", "beta", State.DirEnter, 3),
        ("baz/beta", "epsilon", State.SrcOnly, -1),
        ("baz/beta", "gamma", State.DirEnter, 2),
        ("baz/beta/gamma", "kappa", State.SrcOnly, -1),
        ("baz/beta/gamma", "lambda", State.SrcOnly, -1),
        ("baz/beta", "gamma", State.DirLeave, 0),
        ("baz/beta", "omega", State.SrcOnly, -1),
        ("baz", "beta", State.DirLeave, 0),
        ("", "baz", State.DirLeave, 0),
        ("", "foo", State.SrcNewer, -1),
        ("", "", State.DirLeave, 0),
    ])
    actual = compute_operations(path_states)
    check_expected_path_operations(
        actual,
        [
            ("baz", "alpha", Operation.SrcCopy),
            ("baz/beta", "epsilon", Operation.SrcCopy),
            ("baz/beta/gamma", "kappa", Operation.SrcCopy),
            ("baz/beta/gamma", "lambda", Operation.SrcCopy),
            ("baz/beta", "omega", Operation.SrcCopy),
            ("", "foo", Operation.SrcCopy),
        ],
    )
