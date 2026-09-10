def VAR1(VAR2, VAR3):
    VAR4 = 0
    VAR5 = len(VAR2) - 1
    while VAR4 <= VAR5:
        VAR6 = (VAR4 + VAR5) // 2
        if VAR2[VAR6] == VAR3:
            return VAR6
        if VAR2[VAR6] < VAR3:
            VAR4 = VAR6 + 1
        else:
            VAR5 = VAR6 - 1
    return -1
VAR7 = [10, 20, 30, 40, 50, 60, 70]
VAR3 = 40
VAR8 = VAR1(VAR7, VAR3)
if VAR8 != -1:
    print('Element found at index', VAR8)
else:
    print('Element not found')