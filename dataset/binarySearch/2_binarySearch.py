def search(values, key, low, high):
    if low > high:
        return -1

    mid = (low + high) // 2

    if values[mid] == key:
        return mid

    if key < values[mid]:
        return search(values, key, low, mid - 1)

    return search(values, key, mid + 1, high)


numbers = [10, 20, 30, 40, 50, 60, 70]
target = 60

position = search(numbers, target, 0, len(numbers) - 1)

if position >= 0:
    print("Element found at index", position)
else:
    print("Element not found")