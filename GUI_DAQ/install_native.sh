#!/usr/bin/env bash

# Source this script to install MiniDAQ and leave its environment active:
#   source ./install_native.sh

_minidaq_install_usage() {
    cat <<'EOF'
Usage:
  source ./install_native.sh [options]
  ./install_native.sh [options]

Build cppfit, native_decoder, and native_capture using GUI_DAQ/.venv.

Options:
  --install-system-deps  Install required OS packages. This is intentionally
                         off by default after the initial machine setup.
  --skip-system-deps     Do not install OS packages (default; retained for
                         compatibility with existing commands).
  --skip-verify          Do not run decoder/capture parity checks or the
                         Ethernet frame-I/O helper self-test.
  --skip-python-deps     Do not install or update Python packages.
  --skip-setcap          Do not grant live packet-capture capabilities.
  -h, --help             Show this help.

Sourcing the script leaves GUI_DAQ/.venv active in the current shell.
EOF
}

_minidaq_install_error() {
    printf 'ERROR: %s\n' "$*" >&2
}

_minidaq_require_command() {
    local command_name=$1
    local package_hint=$2
    if ! command -v "$command_name" >/dev/null 2>&1; then
        _minidaq_install_error "'$command_name' is required. Install $package_hint."
        return 1
    fi
}

_minidaq_run_as_root() {
    if (( EUID == 0 )); then
        "$@"
        return $?
    fi

    _minidaq_require_command sudo "sudo, or run this installer as root" || return 1
    sudo "$@"
}

_minidaq_install_system_dependencies() {
    if command -v dnf >/dev/null 2>&1; then
        printf 'Installing MiniDAQ system dependencies with dnf...\n'
        _minidaq_run_as_root dnf install -y \
            python3-devel gcc-c++ make libpcap-devel libcap
        return $?
    fi

    if command -v apt-get >/dev/null 2>&1; then
        printf 'Updating apt package metadata...\n'
        _minidaq_run_as_root apt-get update || return 1
        printf 'Installing MiniDAQ system dependencies with apt-get...\n'
        _minidaq_run_as_root apt-get install -y \
            python3-dev python3-venv g++ make libpcap-dev libcap2-bin
        return $?
    fi

    _minidaq_install_error \
        "cannot install system dependencies: neither dnf nor apt-get is available"
    return 1
}

_minidaq_apply_capture_capabilities() {
    local executable=$1

    _minidaq_require_command setcap "libcap on RHEL-family systems or libcap2-bin on Debian-family systems" ||
        return 1

    if command -v getcap >/dev/null 2>&1; then
        local current_caps
        current_caps=$(getcap "$executable" 2>/dev/null || true)
        if [[ "$current_caps" == *cap_net_raw* && "$current_caps" == *cap_net_admin* ]]; then
            printf 'Capture capabilities already set: %s\n' "$current_caps"
            return 0
        fi
    fi

    printf 'Granting packet-capture capabilities to %s\n' "$executable"
    if (( EUID == 0 )); then
        setcap cap_net_raw,cap_net_admin=eip "$executable"
        return $?
    fi

    _minidaq_require_command sudo "sudo, or run setcap as root" || return 1
    sudo setcap cap_net_raw,cap_net_admin=eip "$executable"
}

_minidaq_install_main() {
    # OS prerequisites are machine-wide and should be installed once. Running
    # dnf/apt on every branch rebuild can otherwise try to downgrade a newer
    # system library to the repository's matching development-package version.
    local install_system_deps=0
    local verify=1
    local install_python_deps=1
    local apply_setcap=1

    while (($#)); do
        case "$1" in
            --skip-system-deps)
                install_system_deps=0
                ;;
            --skip-verify)
                verify=0
                ;;
            --install-system-deps)
                install_system_deps=1
                ;;
            --verify)
                verify=1
                ;;
            --skip-python-deps)
                install_python_deps=0
                ;;
            --skip-setcap)
                apply_setcap=0
                ;;
            -h|--help)
                _minidaq_install_usage
                return 0
                ;;
            *)
                _minidaq_install_error "unknown option: $1"
                _minidaq_install_usage >&2
                return 2
                ;;
        esac
        shift
    done

    local root_dir
    root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || return 1
    local venv_dir="$root_dir/.venv"
    local venv_python="$venv_dir/bin/python"
    local capture_executable="$root_dir/native_capture/minidaq_capture"
    local ethernet_executable="$root_dir/native_capture/ethernet_frame_io"

    if (( install_system_deps )); then
        _minidaq_install_system_dependencies || return 1
    fi

    _minidaq_require_command make "make" || return 1
    _minidaq_require_command g++ "gcc-c++ on RHEL-family systems or g++ on Debian-family systems" ||
        return 1

    if [[ ! -x "$venv_python" ]]; then
        _minidaq_require_command python3 "Python 3 and its venv package" || return 1
        printf 'Creating virtual environment: %s\n' "$venv_dir"
        python3 -m venv "$venv_dir" || {
            _minidaq_install_error "failed to create $venv_dir"
            return 1
        }
    fi

    # When this installer is sourced, activation remains in the caller's shell.
    source "$venv_dir/bin/activate" || return 1
    printf 'Using Python: %s\n' "$("$venv_python" --version 2>&1)"

    if (( install_python_deps )); then
        printf 'Installing Python dependencies...\n'
        "$venv_python" -m pip install --upgrade pip setuptools wheel || return 1
        "$venv_python" -m pip install -r "$root_dir/requirements.txt" || return 1
    else
        printf 'Skipping Python dependency installation.\n'
    fi

    printf 'Building C++ track fitter...\n'
    if "$venv_python" -c "import wheel" >/dev/null 2>&1; then
        "$venv_python" -m pip install --no-build-isolation -e "$root_dir/cppfit" || {
            _minidaq_install_error "C++ track fitter build failed"
            return 1
        }
    else
        printf 'wheel is unavailable; using setuptools develop fallback.\n'
        (
            cd "$root_dir/cppfit" &&
                "$venv_python" setup.py develop
        ) || {
            _minidaq_install_error "C++ track fitter fallback build failed"
            return 1
        }
    fi

    printf 'Building native decoder...\n'
    (
        cd "$root_dir/native_decoder" &&
            "$venv_python" setup.py build_ext --inplace
    ) || {
        _minidaq_install_error "native decoder build failed"
        return 1
    }

    printf 'Building native capture...\n'
    make -C "$root_dir/native_capture" || {
        _minidaq_install_error "native capture build failed; install libpcap development headers"
        return 1
    }

    if (( apply_setcap )); then
        _minidaq_apply_capture_capabilities "$capture_executable" || return 1
        _minidaq_apply_capture_capabilities "$ethernet_executable" || return 1
    else
        printf 'Skipping packet-capture capabilities.\n'
    fi

    printf 'Checking C++ extension imports...\n'
    (
        cd "$root_dir" &&
            "$venv_python" -c \
                "import trackfit_cpp; print(trackfit_cpp.__file__)" &&
            "$venv_python" -c \
                "import sys; sys.path.insert(0, 'native_decoder'); import native_decoder_cpp; print(native_decoder_cpp.__file__)"
    ) || {
        _minidaq_install_error "C++ extension import failed"
        return 1
    }

    if (( verify )); then
        printf 'Running short native decoder parity check...\n'
        "$venv_python" "$root_dir/native_decoder/benchmark_decoder.py" --events 1000 || return 1

        printf 'Running short native capture parity check...\n'
        "$venv_python" "$root_dir/native_capture/benchmark_capture.py" \
            --packets 1000 --iterations 1 || return 1

        printf 'Running Ethernet frame-I/O helper self-test...\n'
        "$ethernet_executable" --self-test || return 1
    fi

    printf '\nNative components installed successfully.\n'
    if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
        printf 'Activate the environment before running MiniDAQ:\n'
        printf '  source %q\n' "$venv_dir/bin/activate"
    else
        printf 'Virtual environment remains active in this shell: %s\n' "$VIRTUAL_ENV"
    fi
}

_minidaq_install_sourced=0
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    _minidaq_install_sourced=1
fi

_minidaq_install_status=0
_minidaq_install_main "$@" || _minidaq_install_status=$?

unset -f _minidaq_install_usage
unset -f _minidaq_install_error
unset -f _minidaq_require_command
unset -f _minidaq_run_as_root
unset -f _minidaq_install_system_dependencies
unset -f _minidaq_apply_capture_capabilities
unset -f _minidaq_install_main

if (( _minidaq_install_sourced )); then
    unset _minidaq_install_sourced
    return "$_minidaq_install_status"
fi

exit "$_minidaq_install_status"
