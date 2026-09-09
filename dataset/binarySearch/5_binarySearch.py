def locate(items, key):
    low = 0
    high = len(items) - 1

    while low <= high:
        center = (low + high) // 2

        if items[center] == key:
            return center

        if items[center] < key:
            low = center + 1
        else:
            high = center - 1

    return -1


values = [5, 10, 15, 20, 25, 30]

print(locate(values, 20))