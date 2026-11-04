// Force-included on Windows only (cppfit/setup.py, /FI): POSIX types MSVC lacks.
#pragma once
#if defined(_MSC_VER)
#include <cstddef>
using ssize_t = std::ptrdiff_t;
#endif
