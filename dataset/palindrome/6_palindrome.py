def test_palindrome(data):
    left = 0
    right = len(data) - 1
    unused = "hello"

    while left < right:

        if data[left] != data[right]:
            return False

        left += 1
        right -= 1

    result = True
    return result


word = "radar"

print(test_palindrome(word))