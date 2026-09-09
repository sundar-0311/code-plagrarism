def calculate(n):
    result = 1
    unused = 100

    for i in range(1, n + 1):
        result *= i

    message = "Done"

    return result


number = 5

print(calculate(number))