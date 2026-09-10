def VAR1(VAR2):
    VAR3 = 0
    VAR4 = len(VAR2) - 1
    VAR5 = 'hello'
    while VAR3 < VAR4:
        if VAR2[VAR3] != VAR2[VAR4]:
            return False
        VAR3 += 1
        VAR4 -= 1
    VAR6 = True
    return VAR6
VAR7 = 'radar'
print(VAR1(VAR7))