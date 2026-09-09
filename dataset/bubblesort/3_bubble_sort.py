def arrange(numbers):
    n = len(numbers)
    i = 0

    while i < n:
        j = 0

        while j < n - i - 1:
            if numbers[j] > numbers[j + 1]:
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]

            j += 1

        i += 1

    return numbers


values = [64, 34, 25, 12, 22, 11, 90]

print(arrange(values))