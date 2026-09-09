def verify_prime(number):
    if number <= 1:
        return False

    divisor = 2

    while divisor < number:
        if number % divisor == 0:
            return False

        divisor += 1

    return True


value = 29

if verify_prime(value):
    print("Prime")
else:
    print("Not Prime")