"""GBT-SCA command IDs; 0x00 and 0xFF are reserved."""


def next_sca_transaction_id(previous):
    previous = int(previous)
    return previous + 1 if 0 <= previous < 0xFE else 1


def validate_sca_transaction_id(value):
    value = int(value)
    if not 1 <= value <= 0xFE:
        raise ValueError(
            f"Invalid SCA transaction ID {value:#x}: expected 0x01..0xFE; "
            "0x00 and 0xFF are reserved"
        )
    return value
