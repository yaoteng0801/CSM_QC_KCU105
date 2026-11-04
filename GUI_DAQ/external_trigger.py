"""GUI-configurable four-input trigger logic; register 71 is writable only while stopped."""
import ast
import time

ADDRESS = 71
SIGNATURE = 0x54524731  # TRG1
DEFAULT_CONFIG = 0xAAAA11  # A only, channel 0 active-low
DEFAULT_EDITOR_CONFIG = 0xAAAAF1  # Fresh GUI settings: A only, all channels active-low.


class UnsupportedTriggerFirmwareError(RuntimeError):
    """Connected firmware does not advertise the programmable trigger registers."""


def compile_lut(expression, enabled=0xF):
    """Compile A..D, &, | and ~. Disabled operands are removed from the tree."""
    if not isinstance(enabled, int) or not 0 <= enabled <= 15:
        raise ValueError("Enable mask must be between 0 and 15")
    if len(expression) > 256:
        raise ValueError("Expression is too long")
    try:
        tree = ast.parse(expression.strip(), mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise ValueError("Use A, B, C, D, &, |, ~ and parentheses") from exc

    def simplify(node):
        if isinstance(node, ast.Name) and node.id in ("A", "B", "C", "D"):
            i = ord(node.id) - ord("A")
            return ("input", i) if enabled & (1 << i) else None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
            child = simplify(node.operand)
            return ("not", child) if child is not None else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.BitAnd, ast.BitOr)):
            left, right = simplify(node.left), simplify(node.right)
            if left is None:
                return right
            if right is None:
                return left
            return ("and" if isinstance(node.op, ast.BitAnd) else "or", left, right)
        raise ValueError("Use only A, B, C, D, &, |, ~ and parentheses")

    root = simplify(tree)

    def evaluate(node, inputs):
        if node is None:
            return False
        if node[0] == "input":
            return bool(inputs & (1 << node[1]))
        if node[0] == "not":
            return not evaluate(node[1], inputs)
        a, b = evaluate(node[1], inputs), evaluate(node[2], inputs)
        return a and b if node[0] == "and" else a or b

    return sum(int(evaluate(root, inputs)) << inputs for inputs in range(16))


def pack_config(enabled, active_low, lut):
    for name, value, maximum in (("Enable mask", enabled, 15),
                                 ("Polarity mask", active_low, 15),
                                 ("Truth table", lut, 65535)):
        if not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"{name} must be between 0 and {maximum}")
    return enabled | (active_low << 4) | (lut << 8)


def read_config(read):
    status = read(ADDRESS)
    signature = (status >> 32) & 0xFFFFFFFF
    if signature != SIGNATURE:
        raise UnsupportedTriggerFirmwareError(
            "Programmable four-input trigger logic is unavailable in the FPGA readback. "
            f"Register 71 signature: 0x{signature:08X}; expected 0x{SIGNATURE:08X} (TRG1). "
            "Build and program the updated MiniDAQ firmware. If it is already loaded, "
            "check that the GUI is connected to the intended board.")
    return status & 0xFFFFFF, bool(status & (1 << 24))


def apply_config(read, write, config, timeout=1.0):
    """Caller holds the Ethernet lock for this complete transaction."""
    if not isinstance(config, int) or not 0 <= config <= 0xFFFFFF:
        raise ValueError("Trigger configuration must be a 24-bit value")
    if read(1) & (1 << 25):
        raise RuntimeError("Stop acquisition before changing external triggers")
    read_config(read)  # Check firmware capability before writing.
    write(ADDRESS, config)
    deadline = time.monotonic() + timeout
    while True:
        actual, busy = read_config(read)
        if actual != config:
            raise RuntimeError("External-trigger configuration readback mismatch")
        if not busy:
            return actual
        if time.monotonic() >= deadline:
            raise RuntimeError("External-trigger LUT programming timed out")
        time.sleep(0.005)
