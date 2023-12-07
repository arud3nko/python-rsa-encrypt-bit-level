async def string_to_bits(string: str) -> str:
    """

    Конвертирует строку в биты

    :param string:
    :return:
    """
    bytes_data = string.encode("utf-8")
    bits_data = ''.join(format(byte, '08b') for byte in bytes_data)
    return bits_data


async def bits_to_string(bits_data: str) -> str:
    """

    Конвертирует биты в строку

    :param bits_data:
    :return:
    """
    bytes_data = [int(bits_data[i:i + 8], 2) for i in range(0, len(bits_data), 8)]
    string = bytes(bytes_data).decode("utf-8")
    return string


async def int_to_bits(number: int) -> str:
    """

    Конвертирует int в биты

    :param number:
    :return:
    """
    return '{0:08b}'.format(number)


async def bits_to_int(bits_data: str) -> int:
    """

    Конвертирует биты в int

    :param bits_data:
    :return:
    """
    return int(bits_data, base=2)


async def bytes_to_bits(byte_data):
    """

    Байты в биты

    :param byte_data:
    :return:
    """
    bits = ''.join(format(byte, '08b') for byte in byte_data)
    return bits


async def bits_to_bytes(bits):
    """

    Биты в байты

    :param bits:
    :return:
    """

    bytes_data = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]

    bytes_array = bytearray(bytes_data)

    return bytes_array
