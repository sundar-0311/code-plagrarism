def is_prime(n):
    if n <= 1:
        return False

    for i in range(2, n):
        if n % i == 0:
            return False

    return True


number = 29

if is_prime(number):
    print("Prime number")
else:
    print("Not a prime number")