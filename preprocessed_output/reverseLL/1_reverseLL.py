class Node:
def __init__(VAR1, VAR2):
VAR1.data = VAR2
VAR1.next = None
def VAR3(VAR4):
VAR5 = None
VAR6 = VAR4
while VAR6:
VAR7 = VAR6.next
VAR6.next = VAR5
VAR5 = VAR6
VAR6 = VAR7
return VAR5
def VAR8(VAR4):
while VAR4:
print(VAR4.data, end=' ')
VAR4 = VAR4.next
VAR4 = VAR9(1)
VAR4.next = VAR9(2)
VAR4.next.next = VAR9(3)
VAR4.next.next.next = VAR9(4)
VAR4 = VAR3(VAR4)
VAR8(VAR4)