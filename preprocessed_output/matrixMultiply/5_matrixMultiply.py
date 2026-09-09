def VAR1(VAR2, VAR3):
VAR4 = len(VAR2)
VAR5 = len(VAR3[0])
VAR6 = len(VAR3)
VAR7 = [[0] * VAR5 for VAR8 in range(VAR4)]
VAR9 = 0
while VAR9 < VAR4:
VAR10 = 0
while VAR10 < VAR5:
VAR11 = 0
while VAR11 < VAR6:
VAR7[VAR9][VAR10] = VAR7[VAR9][VAR10] + VAR2[VAR9][VAR11] * VAR3[VAR11][VAR10]
VAR11 += 1
VAR10 += 1
VAR9 += 1
return VAR7
VAR2 = [[1, 2], [3, 4]]
VAR3 = [[5, 6], [7, 8]]
print(VAR1(VAR2, VAR3))