def compute_factorial(n):
    product = 1
    counter = n

    while counter > 1:
        product *= counter
        counter -= 1

    return product


number = 5

print("Factorial:", compute_factorial(number))