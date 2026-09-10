class VAR1:
    def __init__(VAR2, VAR3):
        VAR2.item = VAR3
        VAR2.next = None
def VAR4(VAR5):
    VAR6 = None
    VAR7 = VAR5
    while VAR7 != None:
        VAR8 = VAR7.next
        VAR7.next = VAR6
        VAR6 = VAR7
        VAR7 = VAR8
    return VAR6
VAR5 = VAR1(1)
VAR5.next = VAR1(2)
VAR5.next.next = VAR1(3)
VAR5.next.next.next = VAR1(4)
VAR5 = VAR4(VAR5)
VAR9 = VAR5
while VAR9:
    print(VAR9.item, end=' ')
    VAR9 = VAR9.next