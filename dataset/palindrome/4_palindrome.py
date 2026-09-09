def check_word(value):
    start = 0
    end = len(value) - 1

    while start < end:
        if value[start] != value[end]:
            return False

        start += 1
        end -= 1

    return True


word = "madam"

print("Palindrome" if check_word(word) else "Not a palindrome")