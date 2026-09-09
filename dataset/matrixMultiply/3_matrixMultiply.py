def multiply(A, B, i=0, j=0, k=0, result=None):
    if result is None:
        result = [[0] * len(B[0]) for _ in A]

    if i == len(A):
        return result

    if j == len(B[0]):
        return multiply(A, B, i + 1, 0, 0, result)

    if k == len(B):
        return multiply(A, B, i, j + 1, 0, result)

    result[i][j] += A[i][k] * B[k][j]

    return multiply(A, B, i, j, k + 1, result)


A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]

result = multiply(A, B)

for row in result:
    print(row)