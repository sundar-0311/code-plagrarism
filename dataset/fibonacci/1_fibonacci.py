def fibonacci(n):
    a = 0
    b = 1

    result = []

    for i in range(n):
        result.append(a)

        a, b = b, a + b

    return result


n = 7

print("Fibonacci series:", fibonacci(n))