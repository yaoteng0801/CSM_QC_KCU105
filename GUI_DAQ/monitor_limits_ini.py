"""Read and atomically save monitoring limits in a user-editable INI file."""

import configparser
import math
import os
from pathlib import Path
import tempfile

MONITOR_LIMITS_INI = Path(__file__).resolve().with_name('monitor_limits.ini')


def _read(path):
    config = configparser.ConfigParser(interpolation=None)
    if path.exists():
        with path.open() as source:
            config.read_file(source)
    return config


def _location(metric):
    (csm, chip, index), name, unit, column = metric
    source = {-1: 'SCA', 0: 'master', 1: 'slave'}[chip]
    return f'CSM{csm}.{source}', name.rsplit(' ', 1)[-1]


def _bounds(text):
    low, high = (float(value.strip()) for value in text.split(','))
    if not (math.isfinite(low) and math.isfinite(high) and -1e6 <= low <= high <= 1e6):
        raise ValueError('expected finite minimum <= maximum within editor range')
    return low, high


def load_csm_limits(metrics, path=MONITOR_LIMITS_INI):
    path = Path(path)
    try:
        config = _read(path)
    except (OSError, UnicodeError, configparser.Error) as exc:
        print(f'WARNING: Cannot load monitoring limits from {path}: {exc}')
        return {}
    limits = {}
    for metric in metrics:
        key = metric[0]
        section, label = _location(metric)
        default_label = 'SCA_temp' if label in [f'SCA{i}_Temp' for i in range(4)] else label
        text = config.get(section, label, fallback=None)
        if text is None:
            text = config.get('CSM.defaults', default_label, fallback=None)
        if text is not None:
            try:
                limits[key] = _bounds(text)
            except ValueError as exc:
                print(f'WARNING: Ignoring invalid monitoring limit {section}/{label}: {exc}')
    return limits


def save_csm_limits(metrics, limits, path=MONITOR_LIMITS_INI):
    path = Path(path)
    config = _read(path)
    _set_csm_limits(config, metrics, limits)
    _write(config, path)


def _set_csm_limits(config, metrics, limits):
    for metric in metrics:
        key = metric[0]
        if limits.get(key) is None:
            continue
        section, label = _location(metric)
        low, high = _bounds(','.join(str(value) for value in limits[key]))
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, label, f'{low:.12g}, {high:.12g}')


def load_mezz_limits(path=MONITOR_LIMITS_INI):
    from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS
    limits = dict(DEFAULT_MONITOR_LIMITS)
    try:
        config = _read(Path(path))
        for label in limits:
            text = config.get('Mezz', label, fallback=None)
            if text is not None:
                try:
                    low, high = _bounds(text)
                    minimum, maximum = (-273.15, 1000) if label == 'Temp' else (-100, 100)
                    if not minimum <= low <= high <= maximum:
                        raise ValueError('limits outside editor range')
                    limits[label] = (low, high)
                except ValueError as exc:
                    print(f'WARNING: Ignoring invalid Mezz monitoring limit {label}: {exc}')
    except (OSError, UnicodeError, configparser.Error) as exc:
        print(f'WARNING: Cannot load monitoring limits from {path}: {exc}')
    return limits


def save_mezz_limits(limits, path=MONITOR_LIMITS_INI):
    path = Path(path)
    config = _read(path)
    _set_mezz_limits(config, limits)
    _write(config, path)


def _set_mezz_limits(config, limits):
    if not config.has_section('Mezz'):
        config.add_section('Mezz')
    for label, bounds in limits.items():
        low, high = _bounds(','.join(str(value) for value in bounds))
        config.set('Mezz', label, f'{low:.12g}, {high:.12g}')


def save_monitor_limits(metrics, csm_limits, mezz_limits, path=MONITOR_LIMITS_INI):
    """Save all range groups in one atomic update."""
    path = Path(path)
    config = _read(path)
    _set_csm_limits(config, metrics, csm_limits)
    _set_mezz_limits(config, mezz_limits)
    _write(config, path)


def load_monitor_limits(metrics, path=MONITOR_LIMITS_INI):
    """Validate a complete import before applying any ranges in the GUI."""
    from csm_monitor_limits import default_bounds
    from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    config = _read(path)
    if not any(section == 'Mezz' or section == 'CSM.defaults' or section.startswith(('CSM0.', 'CSM1.'))
               for section in config.sections()):
        raise ValueError('No monitoring range sections found in this INI file')
    csm_limits = {}
    for metric in metrics:
        section, label = _location(metric)
        default_label = 'SCA_temp' if label in [f'SCA{i}_Temp' for i in range(4)] else label
        text = config.get(section, label, fallback=None)
        if text is None:
            text = config.get('CSM.defaults', default_label, fallback=None)
        csm_limits[metric[0]] = _bounds(text) if text is not None else default_bounds(label)
    mezz_limits = dict(DEFAULT_MONITOR_LIMITS)
    for label in mezz_limits:
        text = config.get('Mezz', label, fallback=None)
        if text is not None:
            low, high = _bounds(text)
            minimum, maximum = (-273.15, 1000) if label == 'Temp' else (-100, 100)
            if not minimum <= low <= high <= maximum:
                raise ValueError(f'Mezz {label}: limits outside editor range')
            mezz_limits[label] = (low, high)
    return csm_limits, mezz_limits


def _write(config, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix=path.name + '.',
                                         suffix='.tmp', delete=False) as target:
            temporary = Path(target.name)
            config.write(target)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
