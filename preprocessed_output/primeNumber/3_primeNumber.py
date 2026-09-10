def VAR1(VAR2):
    VAR3 = 0
    for VAR4 in range(1, VAR2 + 1):
        if VAR2 % VAR4 == 0:
            VAR3 += 1
    return VAR3 == 2
VAR2 = 29
if VAR1(VAR2):
    print('Prime')
else:
    print('Not Prime')