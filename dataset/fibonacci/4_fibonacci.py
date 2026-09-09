def create_fibonacci(count):
    first = 0
    second = 1
    output = []

    for position in range(count):
        output.append(first)
        first, second = second, first + second

    return output


number = 7

print(create_fibonacci(number))