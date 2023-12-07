import random
import asyncio
import sympy


async def generate_prime(limit: int):
    """

    Генерируем простое число

    :param limit: число десятичных знаков
    :return: простое число
    """
    num = random.randint(10 ** (limit // 2), 10 ** (limit // 2 + 1) - 1)
    while not sympy.isprime(num):
        num = random.randint(10 ** (limit // 2), 10 ** (limit // 2 + 1) - 1)
        continue
    return num


async def generate_pair(limit: int) -> [int, int]:
    """

    Генерирует пару множителей

    :param limit: число десятичных знаков
    :return: пара множителей
    """
    pair: tuple | None = None

    while not pair:
        N = asyncio.create_task(generate_prime(limit=limit))
        M = asyncio.create_task(generate_prime(limit=limit))

        N = await N
        M = await M

        if len(str(N*M)) == limit:
            pair = (N, M)
            break

    return pair[0], pair[1]


if __name__ == '__main__':
    pass
