def binary_search(arr, target):
    left = 0
    right = len(arr) - 1

    while left <= right:
        middle = (left + right) // 2

        if arr[middle] == target:
            return middle

        if arr[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return -1


numbers = [10, 20, 30, 40, 50, 60, 70]
target = 40

result = binary_search(numbers, target)

if result != -1:
    print("Element found at index", result)
else:
    print("Element not found")