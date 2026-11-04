import unittest
from unittest.mock import Mock, patch

from external_trigger import (
    ADDRESS, DEFAULT_CONFIG, SIGNATURE, apply_config, compile_lut,
    pack_config, read_config,
)


class ExternalTriggerTest(unittest.TestCase):
    def test_boolean_tables_and_bit_order(self):
        for expression, expected in (("A", 0xAAAA), ("B", 0xCCCC),
                                     ("C", 0xF0F0), ("D", 0xFF00),
                                     ("~A", 0x5555), ("A & B", 0x8888),
                                     ("A | B", 0xEEEE),
                                     ("(A & ~B) | (C & D)", 0xF222)):
            with self.subTest(expression=expression):
                self.assertEqual(compile_lut(expression), expected)

    def test_disabled_terms_are_removed_before_negation(self):
        self.assertEqual(compile_lut("A & (~B | C)", 0b0101), 0xA0A0)
        self.assertEqual(compile_lut("A & ~B", 1), 0xAAAA)
        self.assertEqual(compile_lut("~B", 1), 0)
        self.assertEqual(compile_lut("~(A | B)", 0), 0)

    def test_rejects_non_boolean_input(self):
        for expression in ("", "a", "E", "A ^ B", "A and B", "A + B",
                           "A()", "A.attr", "__import__('os')", "1", "A[0]"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                compile_lut(expression)

    def test_pack_and_validate(self):
        self.assertEqual(pack_config(1, 1, 0xAAAA), DEFAULT_CONFIG)
        for values in ((16, 0, 0), (1, -1, 0), (1, 0, 65536)):
            with self.assertRaises(ValueError):
                pack_config(*values)

    def test_apply_verifies_capability_busy_and_configuration(self):
        config = pack_config(15, 5, 0xF222)
        status = (SIGNATURE << 32) | config
        read = Mock(side_effect=[0, SIGNATURE << 32, status | (1 << 24), status])
        write = Mock()
        with patch("external_trigger.time.sleep"):
            self.assertEqual(apply_config(read, write, config), config)
        write.assert_called_once_with(ADDRESS, config)

    def test_running_or_old_firmware_never_written(self):
        for replies in ([1 << 25], [0, 0]):
            write = Mock()
            with self.assertRaises(RuntimeError):
                apply_config(Mock(side_effect=replies), write, DEFAULT_CONFIG)
            write.assert_not_called()

    def test_mismatch_and_timeout(self):
        base = SIGNATURE << 32
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            apply_config(Mock(side_effect=[0, base, base]), Mock(), DEFAULT_CONFIG)
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            apply_config(Mock(side_effect=[0, base, base | DEFAULT_CONFIG | (1 << 24)]),
                         Mock(), DEFAULT_CONFIG, timeout=-1)

    def test_read_signature_and_busy(self):
        self.assertEqual(read_config(lambda _: (SIGNATURE << 32) | DEFAULT_CONFIG),
                         (DEFAULT_CONFIG, False))


if __name__ == "__main__":
    unittest.main()
