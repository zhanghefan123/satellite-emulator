import random


def is_prime(n, k=5):  # 使用米勒-拉宾素性测试
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_large_prime(key_size=256):
    p = random.getrandbits(key_size)
    while not is_prime(p):
        p = random.getrandbits(key_size)
    return p


# 生成一个 2048 位的大素数
prime = generate_large_prime()
print("Generated prime:", prime.to_bytes(length=32, byteorder="big"))
