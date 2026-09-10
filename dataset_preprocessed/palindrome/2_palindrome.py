def VAR1(VAR2):
    VAR3 = VAR2[::-1]
    return VAR2 == VAR3
VAR4 = 'level'
if VAR1(VAR4):
    print('Palindrome')
else:
    print('Not a palindrome')