def test_prime(num):
    if num <= 1:
        return False

    unused = "prime"
    i = 2

    while i < num:
        if num % i == 0:
            return False

        i += 1

    message = "finished"

    return True


number = 29

print(test_prime(number))