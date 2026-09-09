def factorial(num):
    ans = 1

    for x in range(1, num + 1):
        ans = ans * x

    return ans


n = 5

print("Factorial:", factorial(n))