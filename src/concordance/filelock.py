"""A portable, self-healing cross-process file lock — one honest copy of the pattern proven in
stigmergy (its 4-process test). Whoever creates the lock file (O_EXCL) holds it; a lock older than
`stale` seconds is presumed left by a dead worker and stolen, so a crash can never deadlock a shared
store. No fcntl/msvcrt — works the same on the Linux box and on Windows dev.

    with locked(path):        # blocks (bounded) until held, or gives up and yields False
        ...                    # read-modify-write a shared file safely
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

_TIMEOUT_S = 5.0
_STALE_S = 15.0


def acquire(lockpath: Union[str, Path], timeout: float = _TIMEOUT_S, stale: float = _STALE_S) -> bool:
    lockpath = str(lockpath)
    start = time.time()
    while True:
        try:
            fd = os.open(lockpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode())
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lockpath) > stale:
                    try:
                        os.unlink(lockpath)
                    except OSError:
                        pass
                    continue
            except OSError:
                continue
            if time.time() - start > timeout:
                return False
            time.sleep(0.02)
        except OSError:
            return False


def release(lockpath: Union[str, Path]) -> None:
    try:
        os.unlink(str(lockpath))
    except OSError:
        pass


@contextmanager
def locked(lockpath: Union[str, Path], timeout: float = _TIMEOUT_S, stale: float = _STALE_S) -> Iterator[bool]:
    """Context manager: yields True if the lock was held (release is automatic), False if it could not
    be had within the timeout (the caller then skips its write and retries later — never a clobber)."""
    got = acquire(lockpath, timeout, stale)
    try:
        yield got
    finally:
        if got:
            release(lockpath)
