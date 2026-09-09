import math


def check_prime(value):
    if value < 2:
        return False

    limit = int(math.sqrt(value)) + 1

    for divisor in range(2, limit):
        if value % divisor == 0:
            return False

    return True


number = 29

print("Prime" if check_prime(number) else "Not Prime")