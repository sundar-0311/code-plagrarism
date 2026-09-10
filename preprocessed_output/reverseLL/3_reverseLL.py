class VAR1:
    def __init__(VAR2, VAR3):
        VAR2.data = VAR3
        VAR2.next = None
def VAR4(VAR5):
    VAR6 = []
    VAR7 = VAR5
    while VAR7:
        VAR6.append(VAR7.data)
        VAR7 = VAR7.next
    VAR6.reverse()
    VAR8 = None
    VAR9 = None
    for VAR10 in VAR6:
        VAR11 = VAR1(VAR10)
        if VAR8 is None:
            VAR8 = VAR11
            VAR9 = VAR11
        else:
            VAR9.next = VAR11
            VAR9 = VAR11
    return VAR8
VAR5 = VAR1(1)
VAR5.next = VAR1(2)
VAR5.next.next = VAR1(3)
VAR5 = VAR4(VAR5)
VAR7 = VAR5
while VAR7:
    print(VAR7.data, end=' ')
    VAR7 = VAR7.next