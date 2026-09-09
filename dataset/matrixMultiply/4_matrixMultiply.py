def matrix_multiply(first, second):
    m = len(first)
    n = len(second[0])
    p = len(second)

    output = [[0] * n for _ in range(m)]

    for r in range(m):
        for c in range(n):
            for x in range(p):
                output[r][c] += first[r][x] * second[x][c]

    return output


X = [[1, 2], [3, 4]]
Y = [[5, 6], [7, 8]]

answer = matrix_multiply(X, Y)

for row in answer:
    print(row)