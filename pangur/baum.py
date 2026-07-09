import sys
from dataclasses import dataclass

from pangur.pangur import DirInfo, FileInfo, InfoEntry, SymlinkInfo, walk_tree


class Baum:
    OTHER_CHILD: str = "│   "  # prefix: pipe
    OTHER_ENTRY: str = "├── "  # connector: tee
    FINAL_CHILD: str = "    "  # prefix: no more siblings
    FINAL_ENTRY: str = "└── "  # connector: elbow

    PIPE: str = "|" # prefix
    TEE: str = "+"  # connector: tee
    BLANK: str = " " # prefix
    ELBOW: str = "-"  # connector: elbow

    Short2Long: dict[str, str] = {
        PIPE: OTHER_CHILD,
        BLANK: FINAL_CHILD,
        TEE: OTHER_ENTRY,
        ELBOW: FINAL_ENTRY,
    }

    @classmethod
    def expand_prefix(cls, prefix: str) -> str:
        return "".join(cls.Short2Long.get(c, c) for c in prefix)

    @dataclass
    class VisitResult:
        dirs: int
        files: int
        entries: list[tuple[str, InfoEntry]]

    # TODO: make a generator
    @classmethod
    def _visit(cls, dir: DirInfo, prefix: str) -> VisitResult:
        dirs = 1
        files = 0
        count = len(dir.entries)
        entries = []
        for entry in sorted(dir.entries, key=lambda e: e.name):
            count -= 1
            connector = cls.TEE if count else cls.ELBOW
            entries.append((prefix + connector, entry))
            if isinstance(entry, DirInfo):
                vr = cls._visit(entry, f"{prefix}{cls.PIPE if count else cls.BLANK}")
                dirs += vr.dirs
                files += vr.files
                entries.extend(vr.entries)
            elif isinstance(entry, SymlinkInfo):
                # TODO: special symlink handling?
                files += 1
            elif isinstance(entry, FileInfo):
                files += 1
        return cls.VisitResult(dirs, files, entries)

    @classmethod
    def visit(cls, dir: DirInfo) -> VisitResult:
        return cls._visit(dir, "")


def print_tree(root: str, dir: DirInfo) -> None:
    print(root)
    vr = Baum.visit(dir)
    for prefix, entry in vr.entries:
        print(f"{Baum.expand_prefix(prefix)}{entry.name}")
        # print(f"{prefix}{name}")
    print(f"\n{vr.dirs} directories, {vr.files} files")


if __name__ == "__main__":
    # import pprint

    # pprint.pprint(walk_tree(sys.argv[1]))
    print_tree("", walk_tree(sys.argv[1]))
