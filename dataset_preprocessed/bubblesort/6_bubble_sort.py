def VAR1(VAR2):
    VAR3 = len(VAR2)
    for VAR4 in range(VAR3 - 1):
        for VAR5 in range(VAR3 - VAR4 - 1):
            if VAR2[VAR5] > VAR2[VAR5 + 1]:
                VAR6 = VAR2[VAR5]
                VAR2[VAR5] = VAR2[VAR5 + 1]
                VAR2[VAR5 + 1] = VAR6
    return VAR2
VAR7 = [5, 1, 4, 2, 8]
VAR8 = VAR1(VAR7)
print('Sorted list:', VAR8)