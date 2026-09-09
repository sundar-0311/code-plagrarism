def VAR1(VAR2, VAR3):
VAR4 = len(VAR2)
VAR5 = len(VAR3[0])
VAR6 = len(VAR3)
VAR7 = [[0 for VAR8 in range(VAR5)] for VAR8 in range(VAR4)]
for VAR9 in range(VAR4):
for VAR10 in range(VAR5):
for VAR11 in range(VAR6):
VAR7[VAR9][VAR10] += VAR2[VAR9][VAR11] * VAR3[VAR11][VAR10]
return VAR7
VAR2 = [[1, 2], [3, 4]]
VAR3 = [[5, 6], [7, 8]]
VAR7 = VAR1(VAR2, VAR3)
for VAR12 in VAR7:
print(VAR12)