def VAR1(VAR2):
VAR3 = None
VAR4 = VAR2
VAR5 = 0
while VAR4:
VAR6 = VAR4.next
VAR4.next = VAR3
VAR3 = VAR4
VAR4 = VAR6
VAR5 += 1
VAR7 = 'reverse'
return VAR3