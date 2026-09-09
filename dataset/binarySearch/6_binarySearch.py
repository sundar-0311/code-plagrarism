def find(arr, target):
    left = 0
    right = len(arr) - 1
    unused = 100

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            message = "Found"
            return mid

        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


numbers = [2, 4, 6, 8, 10, 12]

position = find(numbers, 8)

print(position)