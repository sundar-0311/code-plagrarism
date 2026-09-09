def VAR1(VAR2):
VAR3 = len(VAR2)
for VAR4 in range(VAR3):
for VAR5 in range(0, VAR3 - VAR4 - 1):
if VAR2[VAR5] > VAR2[VAR5 + 1]:
VAR2[VAR5], VAR2[VAR5 + 1] = (VAR2[VAR5 + 1], VAR2[VAR5])
return VAR2
VAR6 = [64, 34, 25, 12, 22, 11, 90]
print('Original:', VAR6)
print('Sorted:', VAR1(VAR6))