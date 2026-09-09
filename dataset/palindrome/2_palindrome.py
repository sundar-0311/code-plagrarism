def check_palindrome(word):
    reversed_word = word[::-1]

    return word == reversed_word


text = "level"

if check_palindrome(text):
    print("Palindrome")
else:
    print("Not a palindrome")