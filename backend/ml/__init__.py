"""
POLARIS-EMS — Machine Learning Engine Package
SIH26061: Polar Energy Management & Resilience System

Provides cross-version and cross-platform compatibility shims for unpickling
artifacts between Python 3.12 / 3.13 and Windows / Linux environments.
"""

import sys
import pathlib

# Python 3.13 moved Path implementations into internal module pathlib._local.
# Python 3.12 and earlier do not have pathlib._local, raising ModuleNotFoundError on unpickling.
if "pathlib._local" not in sys.modules:
    try:
        import pathlib._local  # type: ignore
    except (ImportError, ModuleNotFoundError):
        if not hasattr(pathlib, "__path__"):
            pathlib.__path__ = []  # Mark module as package for submodule lookups
        sys.modules["pathlib._local"] = pathlib

# When unpickling artifacts on Linux that were serialized on Windows, WindowsPath cannot be instantiated.
if not hasattr(pathlib, "WindowsPath") or sys.platform != "win32":
    try:
        pathlib.WindowsPath = pathlib.PureWindowsPath  # type: ignore
    except Exception:
        pass
