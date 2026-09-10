def VAR1(VAR2):
    VAR3 = ''
    for VAR4 in VAR2:
        VAR3 = VAR4 + VAR3
    if VAR2 == VAR3:
        return True
    return False
VAR5 = 'radar'
print('Palindrome' if VAR1(VAR5) else 'Not a palindrome')