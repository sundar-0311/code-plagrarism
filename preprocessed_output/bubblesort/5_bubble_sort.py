def VAR1(VAR2):
VAR3 = len(VAR2)
for VAR4 in range(VAR3):
VAR5 = False
for VAR6 in range(VAR3 - VAR4 - 1):
if VAR2[VAR6] > VAR2[VAR6 + 1]:
VAR2[VAR6], VAR2[VAR6 + 1] = (VAR2[VAR6 + 1], VAR2[VAR6])
VAR5 = True
if not VAR5:
break
return VAR2
VAR7 = [64, 34, 25, 12, 22, 11, 90]
print('Sorted:', VAR1(VAR7))