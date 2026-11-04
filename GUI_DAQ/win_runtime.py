"""Windows: load the newest MSVC C++ runtime before PyQt5 does.

PyQt5-Qt5 5.15.2 bundles msvcp140.dll 14.26.  Windows keeps one msvcp140.dll
per process, so every C++ extension imported after PyQt5 gets that old copy.
Extensions built with MSVC 17.10+ (awkward_cpp, used by uproot to read ROOT
RT files; our native_decoder_cpp without its compile flag) then crash with an
access violation.  The runtime in System32 is newer and backward compatible,
so loading it first serves every module in the process.

Import this module before PyQt5.  It does nothing on other platforms.

    python -m win_runtime [unittest args]   runs the unit tests with the fix
"""

import os
import sys


def preload_msvc_runtime():
    if sys.platform != "win32":
        return None
    import ctypes

    system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    loaded = None
    for name in ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll"):
        path = os.path.join(system32, name)
        if os.path.isfile(path):
            try:
                handle = ctypes.WinDLL(path)
            except OSError:
                continue
            if loaded is None:
                loaded = handle
    return loaded


preload_msvc_runtime()


if __name__ == "__main__":
    import unittest

    argv = sys.argv[1:] or ["discover", "-p", "test_*.py"]
    unittest.main(module=None, argv=["python -m win_runtime"] + argv)
