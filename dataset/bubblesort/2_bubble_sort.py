def sort_numbers(values):
    size = len(values)

    for pass_no in range(size):
        for index in range(size - pass_no - 1):
            if values[index] > values[index + 1]:
                temp = values[index]
                values[index] = values[index + 1]
                values[index + 1] = temp

    return values


data = [64, 34, 25, 12, 22, 11, 90]

print("Original:", data)
print("Sorted:", sort_numbers(data))