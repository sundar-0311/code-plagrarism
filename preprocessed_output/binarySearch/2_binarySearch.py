def VAR1(VAR2, VAR3, VAR4, VAR5):
    if VAR4 > VAR5:
        return -1
    VAR6 = (VAR4 + VAR5) // 2
    if VAR2[VAR6] == VAR3:
        return VAR6
    if VAR3 < VAR2[VAR6]:
        return VAR1(VAR2, VAR3, VAR4, VAR6 - 1)
    return VAR1(VAR2, VAR3, VAR6 + 1, VAR5)
VAR7 = [10, 20, 30, 40, 50, 60, 70]
VAR8 = 60
VAR9 = VAR1(VAR7, VAR8, 0, len(VAR7) - 1)
if VAR9 >= 0:
    print('Element found at index', VAR9)
else:
    print('Element not found')