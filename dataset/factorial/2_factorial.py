def find_factorial(n):
    if n == 0 or n == 1:
        return 1

    return n * find_factorial(n - 1)


number = 5

print("Factorial:", find_factorial(number))