def multiply(A, B):
    rows = len(A)
    columns = len(B[0])
    common = len(B)

    result = [[0] * columns for _ in range(rows)]

    i = 0

    while i < rows:
        j = 0

        while j < columns:
            k = 0

            while k < common:
                result[i][j] = result[i][j] + A[i][k] * B[k][j]
                k += 1

            j += 1

        i += 1

    return result


A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]

print(multiply(A, B))