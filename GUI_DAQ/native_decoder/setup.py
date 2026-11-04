import sys

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


if sys.platform == "win32":
    # MSVC.  PyQt5-Qt5 5.15.2 loads an old msvcp140.dll first; std::mutex built
    # with MSVC >= 17.10 then crashes on import unless the constexpr constructor
    # is disabled (Microsoft's documented workaround).
    compile_args = ["/O2", "/DNDEBUG", "/D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR"]
else:
    compile_args = ["-O3", "-DNDEBUG", "-march=native"]

ext_modules = [
    Pybind11Extension(
        "native_decoder_cpp",
        ["native_decoder.cpp"],
        cxx_std=17,
        extra_compile_args=compile_args,
    ),
]


setup(
    name="native_decoder_cpp",
    version="0.1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
