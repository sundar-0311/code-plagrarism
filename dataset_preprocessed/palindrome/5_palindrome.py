def VAR1(VAR2):
    VAR3 = len(VAR2)
    for VAR4 in range(VAR3 // 2):
        if VAR2[VAR4] != VAR2[VAR3 - VAR4 - 1]:
            return False
    return True
VAR5 = 'level'
print(VAR1(VAR5))