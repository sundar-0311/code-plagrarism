def verify(text):
    n = len(text)

    for i in range(n // 2):
        if text[i] != text[n - i - 1]:
            return False

    return True


value = "level"

print(verify(value))