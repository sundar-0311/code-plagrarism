def generate_series(count):
    numbers = [0, 1]

    while len(numbers) < count:
        next_value = numbers[-1] + numbers[-2]
        numbers.append(next_value)

    return numbers[:count]


n = 7

print(generate_series(n))