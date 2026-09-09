def selection_sort(arr):
    n = len(arr)

    for i in range(n):
        smallest = i

        for j in range(i + 1, n):
            if arr[j] < arr[smallest]:
                smallest = j

        arr[i], arr[smallest] = arr[smallest], arr[i]

    return arr


numbers = [64, 34, 25, 12, 22, 11, 90]

print(selection_sort(numbers))