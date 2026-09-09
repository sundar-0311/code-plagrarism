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
VAR7 = [5, 10, 15, 20, 25, 30]
print(VAR1(VAR7, 20))