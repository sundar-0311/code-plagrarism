def get_result(value):
    total = 1

    for count in range(1, value + 1):
        total *= count

    return total


number = 5

print(get_result(number))