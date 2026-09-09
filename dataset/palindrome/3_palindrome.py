def palindrome(text):
    reverse = ""

    for character in text:
        reverse = character + reverse

    if text == reverse:
        return True

    return False


word = "radar"

print("Palindrome" if palindrome(word) else "Not a palindrome")