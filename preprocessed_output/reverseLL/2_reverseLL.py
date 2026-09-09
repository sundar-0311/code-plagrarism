class Node:
def __init__(VAR1, VAR2):
VAR1.value = VAR2
VAR1.next = None
def VAR3(VAR4):
if VAR4 is None or VAR4.next is None:
return VAR4
VAR5 = VAR3(VAR4.next)
VAR4.next.next = VAR4
VAR4.next = None
return VAR5
def VAR6(VAR4):
while VAR4:
print(VAR4.value, end=' ')
VAR4 = VAR4.next
VAR4 = VAR7(1)
VAR4.next = VAR7(2)
VAR4.next.next = VAR7(3)
VAR4.next.next.next = VAR7(4)
VAR4 = VAR3(VAR4)
VAR6(VAR4)