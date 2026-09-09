def VAR1(VAR2):
VAR3 = 0
VAR4 = 1
VAR5 = []
for VAR6 in range(VAR2):
VAR5.append(VAR3)
VAR3, VAR4 = (VAR4, VAR3 + VAR4)
return VAR5
VAR2 = 7
print('Fibonacci series:', VAR1(VAR2))