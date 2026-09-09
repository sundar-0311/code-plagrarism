def fibonacci_series(limit):
    x = 0
    y = 1
    values = []
    counter = 0

    while counter < limit:
        values.append(x)

        temp = x
        x = y
        y = temp + y

        counter += 1

    return values


n = 7

print(fibonacci_series(n))