class VAR1:
    def __init__(VAR2, VAR3):
        VAR2.val = VAR3
        VAR2.next = None
def VAR4(VAR5):
    VAR6 = None
    VAR7 = VAR5
    while VAR7 is not None:
        VAR8 = VAR7.next
        VAR7.next = VAR6
        VAR6 = VAR7
        VAR7 = VAR8
    return VAR6
def VAR9(VAR5):
    while VAR5:
        print(VAR5.val, end=' ')
        VAR5 = VAR5.next
VAR5 = VAR1(1)
VAR5.next = VAR1(2)
VAR5.next.next = VAR1(3)
VAR5.next.next.next = VAR1(4)
VAR5 = VAR4(VAR5)
VAR9(VAR5)