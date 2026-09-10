def VAR1(VAR2):
    VAR3 = len(VAR2)
    VAR4 = 0
    while VAR4 < VAR3:
        VAR5 = 0
        while VAR5 < VAR3 - VAR4 - 1:
            if VAR2[VAR5] > VAR2[VAR5 + 1]:
                VAR2[VAR5], VAR2[VAR5 + 1] = (VAR2[VAR5 + 1], VAR2[VAR5])
            VAR5 += 1
        VAR4 += 1
    return VAR2
VAR6 = [64, 34, 25, 12, 22, 11, 90]
print(VAR1(VAR6))