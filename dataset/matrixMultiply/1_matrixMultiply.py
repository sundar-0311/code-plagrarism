def multiply_matrices(A, B):
    rows = len(A)
    cols = len(B[0])
    common = len(B)

    result = [[0 for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            for k in range(common):
                result[i][j] += A[i][k] * B[k][j]

    return result


A = [
    [1, 2],
    [3, 4]
]

B = [
    [5, 6],
    [7, 8]
]

result = multiply_matrices(A, B)

for row in result:
    print(row)