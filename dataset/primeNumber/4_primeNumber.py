def check_number(value):
    if value <= 1:
        return False

    for divisor in range(2, value):
        if value % divisor == 0:
            return False

    return True


n = 29

print(check_number(n))