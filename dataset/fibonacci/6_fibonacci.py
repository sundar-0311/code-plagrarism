def make_series(n):
    a = 0
    b = 1
    result = []

    unused = 999

    for i in range(n):
        result.append(a)
        a, b = b, a + b

    message = "completed"

    return result


number = 7

print(make_series(number))