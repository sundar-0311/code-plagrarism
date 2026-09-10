def VAR1(VAR2, VAR3):
    VAR4 = 0
    VAR5 = len(VAR2) - 1
    VAR6 = 100
    while VAR4 <= VAR5:
        VAR7 = (VAR4 + VAR5) // 2
        if VAR2[VAR7] == VAR3:
            VAR8 = 'Found'
            return VAR7
        if VAR2[VAR7] < VAR3:
            VAR4 = VAR7 + 1
        else:
            VAR5 = VAR7 - 1
    return -1
VAR9 = [2, 4, 6, 8, 10, 12]
VAR10 = VAR1(VAR9, 8)
print(VAR10)