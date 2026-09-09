def search_number(numbers, value):
    start = 0
    end = len(numbers) - 1

    while start <= end:
        mid = (start + end) // 2

        if numbers[mid] == value:
            return mid
        elif numbers[mid] < value:
            start = mid + 1
        else:
            end = mid - 1

    return -1


data = [10, 20, 30, 40, 50, 60, 70]

print(search_number(data, 40))