n = int(input("Enter a number: "))

digits = len(str(n))
total = 0

for digit in str(n):
    total += int(digit) ** digits

if total == n:
    print("Armstrong Number")
else:
    print("Not an Armstrong Number")