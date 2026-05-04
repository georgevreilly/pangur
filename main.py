from __future__ import annotations

import pangur


def main():
    print("Hello from pangur!")
    print(dir(pangur))
    e = pangur.pangur.FileEntry("foo", timestamp=7, mode=0o744, size=123)
    print(e)


if __name__ == "__main__":
    main()
