from __future__ import annotations

import pangur


def main():
    print("Hello from pangur!")
    print(dir(pangur))
    e = pangur.pangur.FileInfo("foo", mode=pangur.pangur.FileMode(0o644), mtime=pangur.pangur.TimeStamp(7), size=123)
    print(e)


if __name__ == "__main__":
    main()
