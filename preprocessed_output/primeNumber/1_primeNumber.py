def VAR1(VAR2):
    if VAR2 <= 1:
        return False
    for VAR3 in range(2, VAR2):
        if VAR2 % VAR3 == 0:
            return False
    return True
VAR4 = 29
if VAR1(VAR4):
    print('Prime number')
else:
    print('Not a prime number')