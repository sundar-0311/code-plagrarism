def VAR1(VAR2):
    VAR3 = 1
    VAR4 = VAR2
    while VAR4 > 1:
        VAR3 *= VAR4
        VAR4 -= 1
    return VAR3
VAR5 = 5
print('Factorial:', VAR1(VAR5))