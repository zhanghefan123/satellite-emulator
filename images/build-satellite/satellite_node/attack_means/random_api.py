from string import ascii_letters
from typing import List, Callable, Any
from socket import inet_ntop, inet_ntoa, AF_INET6
from sys import maxsize
from struct import pack
from os import urandom
from contextlib import suppress


class RandomApi:
    letters: List[str] = list(ascii_letters)
    rand_str: Callable[[int], str] = lambda length=16: ''.join(
        RandomApi.rand_choice(*RandomApi.letters) for _ in range(length))
    rand_char: Callable[[int], chr] = lambda length=16: "".join(
        [chr(RandomApi.rand_int(0, 1000)) for _ in range(length)])
    rand_ipv4: Callable[[], str] = lambda: inet_ntoa(
        pack('>I', RandomApi.rand_int(1, 0xffffffff)))
    rand_ipv6: Callable[[], str] = lambda: inet_ntop(
        AF_INET6, pack('>QQ', RandomApi.rand_bits(64), RandomApi.rand_bits(64)))
    rand_int: Callable[[int, int],
                       int] = lambda minimum=0, maximum=maxsize: int(
                           RandomApi.rand_float(minimum, maximum))
    rand_choice: Callable[[List[Any]], Any] = lambda *data: data[
        (RandomApi.rand_int(maximum=len(data) - 2) or 0)]
    rand: Callable[
        [], int] = lambda: (int.from_bytes(urandom(7), 'big') >> 3) * (2**-53)

    @staticmethod
    def rand_bits(maximum: int = 255) -> int:
        numbytes = (maximum + 7) // 8
        return int.from_bytes(urandom(numbytes),
                              'big') >> (numbytes * 8 - maximum)

    @staticmethod
    def rand_float(minimum: float = 0.0,
                   maximum: float = (maxsize * 1.0)) -> float:
        with suppress(ZeroDivisionError):
            return abs((RandomApi.rand() * maximum) % (minimum -
                                                    (maximum + 1))) + minimum
        return 0.0


if __name__ == "__main__":
    print("rand ipv4: ", RandomApi.rand_ipv4())
    print("rand ipv6: ", RandomApi.rand_ipv6())
    print("rand 20 chars: ", RandomApi.rand_str(20))