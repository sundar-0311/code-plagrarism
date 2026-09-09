def prime_number(number):
    divisor_count = 0

    for value in range(1, number + 1):
        if number % value == 0:
            divisor_count += 1

    return divisor_count == 2


number = 29

if prime_number(number):
    print("Prime")
else:
    print("Not Prime")