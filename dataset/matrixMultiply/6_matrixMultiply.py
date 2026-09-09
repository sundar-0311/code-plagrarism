def product(matrix_a, matrix_b):
    rows = len(matrix_a)
    columns = len(matrix_b[0])
    shared = len(matrix_b)

    result = [[0] * columns for _ in range(rows)]

    unused = "matrix"
    i = 0

    while i < rows:
        j = 0

        while j < columns:
            k = 0

            while k < shared:
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]
                k += 1

            j += 1

        i += 1

    return result


A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]

answer = product(A, B)

for row in answer:
    print(row)