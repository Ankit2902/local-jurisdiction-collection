"""Windows startup for the live collectors.

POSIX builds keep the real fcntl module. Windows has no fcntl, and its default
text encoding rejects the catalog, so entry points call boot() before reading
files or locking a publisher gate.
"""
import errno
import hashlib
import os
import sys
from pathlib import Path

LOCK_SH = 1
LOCK_EX = 2
LOCK_NB = 4
LOCK_UN = 8


def gate_dir(env_name, posix_default, env=None):
    """Use the explicit environment directory, otherwise a per-user Windows folder."""
    source = os.environ if env is None else env
    override = source.get(env_name)
    if override:
        return Path(override)
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA') or os.environ.get('TEMP') or str(Path.home())
        return Path(base) / 'local-jurisdiction-collection' / Path(posix_default).name
    return Path(posix_default)


class _Fcntl:
    LOCK_SH = LOCK_SH
    LOCK_EX = LOCK_EX
    LOCK_NB = LOCK_NB
    LOCK_UN = LOCK_UN

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self._kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self._kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self._kernel.CreateMutexW.restype = wintypes.HANDLE
        self._kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel.WaitForSingleObject.restype = wintypes.DWORD
        self._kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self._kernel.ReleaseMutex.restype = wintypes.BOOL
        self._handles = {}
        self._WAIT_OBJECT_0 = 0
        self._WAIT_ABANDONED = 0x80
        self._WAIT_TIMEOUT = 0x102
        self._INFINITE = 0xFFFFFFFF

    def _mutex(self, fileobj):
        try:
            path = os.path.abspath(fileobj.name)
        except Exception:
            path = 'fd-%s' % fileobj.fileno()
        name = 'Local\\ljc-flock-' + hashlib.sha256(path.encode('utf-8')).hexdigest()
        handle = self._handles.get(name)
        if handle:
            return handle
        handle = self._kernel.CreateMutexW(None, False, name)
        if not handle:
            raise OSError(ctypes_error(), 'CreateMutexW failed')
        self._handles[name] = handle
        return handle

    def flock(self, fileobj, operation):
        handle = self._mutex(fileobj)
        if operation & LOCK_UN:
            if not self._kernel.ReleaseMutex(handle):
                error = ctypes_error()
                if error == 288:
                    return
                raise OSError(error, 'ReleaseMutex failed')
            return
        timeout = 0 if operation & LOCK_NB else self._INFINITE
        result = self._kernel.WaitForSingleObject(handle, timeout)
        if result in (self._WAIT_OBJECT_0, self._WAIT_ABANDONED):
            return
        if result == self._WAIT_TIMEOUT:
            raise BlockingIOError(errno.EAGAIN, 'Resource temporarily unavailable')
        raise OSError(ctypes_error() or int(result), 'WaitForSingleObject failed')


def ctypes_error():
    import ctypes
    return ctypes.get_last_error()


def ensure_fcntl():
    """Install the Windows lock shim once. POSIX imports the standard module."""
    if 'fcntl' in sys.modules:
        return sys.modules['fcntl']
    try:
        import fcntl
    except ModuleNotFoundError:
        fcntl = _Fcntl()
        sys.modules['fcntl'] = fcntl
    return fcntl


def boot(module=None):
    """Restart this process in UTF-8 mode on Windows, then provide fcntl.

    os.execv splits on the space in "Program Files", so Windows relaunches
    through subprocess with a real argument list.
    """
    if os.name == 'nt':
        os.environ['PYTHONUTF8'] = '1'
        if not sys.flags.utf8_mode:
            import subprocess
            if module:
                argv = [sys.executable, '-X', 'utf8', '-m', module, *sys.argv[1:]]
            else:
                argv = [sys.executable, '-X', 'utf8', *sys.argv]
            raise SystemExit(subprocess.call(argv))
    ensure_fcntl()
