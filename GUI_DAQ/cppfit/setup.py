import os
import sys

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

# Optional OpenMP: enable if your compiler supports it.
# If you don't want OpenMP yet, set USE_OPENMP = False.
USE_OPENMP = False

compile_args = ["-O3", "-DNDEBUG", "-ffast-math", "-fno-math-errno", "-funroll-loops"]
link_args = []

# This gives best speed on *this machine*.
# If you plan to run on different CPUs, you may want to remove -march=native.
compile_args += ["-march=native"]

if sys.platform == "win32":
    # MSVC: equivalent options; ssize_t comes from msvc_compat.h, and the mutex
    # define avoids a crash against PyQt5's older msvcp140.dll (see native_decoder).
    compile_args = ["/O2", "/DNDEBUG", "/fp:fast", "/D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR",
                    "/FI" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "msvc_compat.h")]

if USE_OPENMP:
    compile_args += ["-fopenmp"]
    link_args += ["-fopenmp"]

ext_modules = [
    Pybind11Extension(
        "trackfit_cpp",                 # import trackfit_cpp
        ["trackfit_cpp.cpp"],
        cxx_std=17,
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    ),
]

setup(
    name="trackfit_cpp",
    version="0.1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
