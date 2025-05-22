"""Module with utility functions for data conversion."""


def bytes_to_gb(bytes_value: int) -> float:
    """
    Convert bytes to gigabytes.

    Args:
        bytes_value (int): Value in bytes.

    Returns:
        float: Value converted to gigabytes (rounded to 2 decimal places).
    """
    return round(bytes_value / (1024 ** 3), 2)
