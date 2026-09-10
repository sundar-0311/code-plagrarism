def VAR1(VAR2):
    VAR3 = [0, 1]
    while len(VAR3) < VAR2:
        VAR4 = VAR3[-1] + VAR3[-2]
        VAR3.append(VAR4)
    return VAR3[:VAR2]
VAR5 = 7
print(VAR1(VAR5))