import bisect


def find_element(numbers, value):
    position = bisect.bisect_left(numbers, value)

    if position < len(numbers) and numbers[position] == value:
        return position

    return -1


data = [10, 20, 30, 40, 50, 60, 70]

answer = find_element(data, 50)

print("Index:", answer)