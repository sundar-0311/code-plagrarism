def VAR1(VAR2):
    if VAR2 <= 1:
        return VAR2
    return VAR1(VAR2 - 1) + VAR1(VAR2 - 2)
VAR3 = 7
for VAR4 in range(VAR3):
    print(VAR1(VAR4), end=' ')