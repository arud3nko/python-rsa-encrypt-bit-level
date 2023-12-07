import random
import math
import logging
import aiofiles
import time

from app.utils import prime_numbers, euler_function, convert
from app.config import config

log = True


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG if log else logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


async def generate_rsa_keypair() -> [tuple[int, int], tuple[int, int]]:
    """

    Генерирует открытый и закрытый ключи

    :return:
    """
    P, Q = await prime_numbers.generate_pair(config.clx)
    D = await euler_function.euler_function(P, Q)
    N = P * Q

    del P, Q

    S = random.randint(2, D - 1)
    while math.gcd(S, D) != 1:
        S = random.randint(0, D - 1)

    E = pow(S, -1, D)

    assert E * S % D == 1

    return (N, S), (N, E)


async def encode_plaintext(plaintext: str, public_key: tuple[int, int]):
    """

    Шифрует текст с использованием открытого ключа

    :param plaintext:
    :param public_key:
    :return:
    """
    N, S = public_key[0], public_key[1]

    N_bit = await convert.int_to_bits(N)
    N_bits = len(N_bit)

    prev = 0

    encoded = ""

    iterations = len(plaintext) / N_bits

    iterations += 1 if len(plaintext) % N_bits != 0 else 0

    _ = 0
    i = 0

    keyword = "ENCODING"
    msg = "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1))) + keyword + "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1)))
    logger.debug(msg)

    cut = plaintext[prev:prev + N_bits]

    while i < iterations:
        marker = "00"

        if cut == '' or cut == ' ':
            break

        if len(cut) < N_bits:
            mod = (len(encoded) + len(cut)) % 8
            diff = int(((len(encoded) + len(cut)) / 8) + 1) * 8 - (len(encoded) + len(cut)) if mod else 0

            encoded += "".join("0" for _ in range(diff)) + cut if diff else cut

            encoded += await convert.int_to_bits(diff)
            logger.info(f"{i + 1}) {cut} (Final) -> {''.join('0' for _ in range(diff)) + cut} | {diff}")

            break

        cut_decimal = await convert.bits_to_int(cut)

        if cut_decimal > N:
            marker = "1" + cut[-1]
            cut = "0" + cut[:-1]
            cut_decimal = await convert.bits_to_int(cut)

        logger.debug(f"{i+1}) {cut}")

        cut_encoded = await encode_rsa(data=cut_decimal,
                                       N=N,
                                       S=S)

        cut_encoded_bits = await convert.int_to_bits(cut_encoded)

        logger.debug(f"--> {cut_encoded_bits}")

        if len(cut_encoded_bits) < N_bits:
            cut_encoded_bits = ''.join("0" for _ in range(N_bits - len(cut_encoded_bits))) + cut_encoded_bits

        cut_encoded_bits += marker

        logger.debug(f"----> {cut_encoded_bits}")

        encoded += cut_encoded_bits
        prev += N_bits
        i += 1
        cut = plaintext[prev:prev + N_bits]

    logger.debug(f"Plaintext: {plaintext}\n"
          f"Encoded: {encoded}\nPublic key: {public_key}\nPlaintext len: {len(plaintext)} "
          f"Encoded len: {len(encoded)}\nDifference: {len(encoded) - len(plaintext)} (")

    keyword = "ENCODING COMPLETED"
    msg = "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1))) + keyword + "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1)))
    logger.debug(msg)

    return encoded


async def decode_ciphertext(ciphertext: str, secret_key: tuple[int, int]):
    """

    Дешифрует текст с использованием закрытого ключа

    :param secret_key:
    :param ciphertext:
    :return:
    """
    N, E = secret_key[0], secret_key[1]

    N_bit = await convert.int_to_bits(N)
    N_bits = len(N_bit)

    final = len(ciphertext) / 8 < (N_bits + 2) * 8

    prev = 0
    decoded = ""
    i = 0

    iterations = (len(ciphertext) - 8) // (N_bits + 2)

    iterations += 1 if (len(ciphertext) - 8 - iterations * (N_bits + 2)) > 0 else 0

    keyword = "DECODING"
    msg = "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1))) + keyword + "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1)))
    logger.debug(msg)

    while i < iterations:
        cut = ciphertext[prev:prev + (N_bits + 2)]

        prev += N_bits + 2

        if i + 1 >= iterations and final:
            diff = ciphertext[-8:]
            diff = await convert.bits_to_int(diff)

            cut = ciphertext[prev - N_bits - 2 + diff:-8]

            decoded += cut

            logger.info(f"{i + 1}) {cut} (Final)")

            break

        marker = int(cut[-2])
        mean = cut[-1]

        cut_decimal = await convert.bits_to_int(cut[:-2])

        cut_encoded = await decode_rsa(encoded_data=cut_decimal,
                                       N=N,
                                       E=E)

        cut_encoded_bits = await convert.int_to_bits(cut_encoded)

        if (len(cut_encoded_bits) < N_bits) or (len(cut_encoded_bits) < N_bits and i + 1 != iterations):
            cut_encoded_bits = ''.join("0" for _ in range(N_bits - len(cut_encoded_bits))) + cut_encoded_bits

        if marker:
            cut_encoded_bits = cut_encoded_bits[1:]
            cut_encoded_bits += mean

        logger.debug(f"{i+1}) {cut_encoded_bits} | Marker: {bool(marker)}")

        decoded += cut_encoded_bits

        i += 1

    logger.debug(f"Decoded: {decoded}\nSecret key: {secret_key}\nEncoded len: {len(ciphertext)} "
          f"Plaintext len: {len(decoded)}\nDifference: {len(decoded) - len(ciphertext)} ("
          f"{int(100 - 100 / len(decoded) * len(ciphertext))}%)")

    keyword = "DECODING COMPLETED"
    msg = "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1))) + keyword + "".join("=" for _ in range(int(100 / 2 - len(keyword) / 2 - 1)))
    logger.debug(msg)

    return decoded


async def rfb(file_path, block_size):
    async with aiofiles.open(file_path, 'rb') as file:
        while True:
            block = await file.read(block_size)
            if not block:
                break
            yield block


async def encode_file(file_path: str, public: tuple, output: str) -> None:
    N = public[0]
    N_bit = await convert.int_to_bits(N)
    N_bits = len(N_bit)

    start = time.time()

    plain_len = 0
    enc_len = 0

    async with aiofiles.open(file=output, mode="wb") as output_file:
        async for block in rfb(file_path=file_path, block_size=N_bits * 8):
            block_bits = await convert.bytes_to_bits(block)
            plain_len += len(block_bits)
            encoded_block = await encode_plaintext(block_bits, public)
            enc_len += len(encoded_block)
            encoded_block = await convert.bits_to_bytes(encoded_block)
            await output_file.write(encoded_block)

    end = time.time()
    logger.info(f"===== Encoding | Time taken: {end-start} =====")


async def decode_file(file_path: str, secret: tuple, output: str) -> None:
    N = secret[0]
    N_bit = await convert.int_to_bits(N)
    N_bits = len(N_bit)

    start = time.time()

    enc_len = 0
    plain_len = 0

    async with aiofiles.open(file=output, mode="wb") as output_file:
        async for block in rfb(file_path=file_path, block_size=(N_bits + 2) * 8):
            block_bits = await convert.bytes_to_bits(block)
            enc_len += len(block_bits)
            encoded_block = await decode_ciphertext(block_bits, secret)
            plain_len += len(encoded_block)
            encoded_block = await convert.bits_to_bytes(encoded_block)
            await output_file.write(encoded_block)

    end = time.time()
    logger.info(f"===== Decoding | Time taken: {end-start} =====")


async def main():
    pass


async def encode_rsa(data: int, N: int, S: int) -> int:
    return pow(data, S, N)


async def decode_rsa(encoded_data: int, N: int, E: int) -> int:
    return pow(encoded_data, E, N)


async def decode_bytes(bytes_int: int) -> str:
    recovered_bytes = bytes_int.to_bytes((bytes_int.bit_length() + 7) // 8, 'little')
    recovered_string = recovered_bytes.decode("utf-8")
    return recovered_string


if __name__ == "__main__":
    pass
