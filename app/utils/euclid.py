async def gcd_extended(A,B):
    """

    Расширенный алгоритм Евклида

    :param A:
    :param B:
    :return:
    """
    if A == 0:
        return B, 0, 1
    _gcd, v, u = await gcd_extended(B % A, A)
    return _gcd, u - (B // A) * v, v