def matrix_product(first, second):
    return [
        [
            sum(x * y for x, y in zip(row, column))
            for column in zip(*second)
        ]
        for row in first
    ]


matrix1 = [
    [1, 2],
    [3, 4]
]

matrix2 = [
    [5, 6],
    [7, 8]
]

answer = matrix_product(matrix1, matrix2)

for row in answer:
    print(row)