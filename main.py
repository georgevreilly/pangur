from __future__ import annotations

from pangur.pangur import FileInfo, FileMode, TimeStamp


def main():
    print("Hello from pangur!")
    e = FileInfo("foo", mode=FileMode(0o644), mtime=TimeStamp(7), size=123)
    print(e)


if __name__ == "__main__":
    main()
