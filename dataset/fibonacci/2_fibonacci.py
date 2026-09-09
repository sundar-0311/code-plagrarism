def fib(number):
    if number <= 1:
        return number

    return fib(number - 1) + fib(number - 2)


n = 7

for i in range(n):
    print(fib(i), end=" ")