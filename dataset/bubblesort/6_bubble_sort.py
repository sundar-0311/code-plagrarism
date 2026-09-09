def arrange_list(items):
    length = len(items)

    for pass_count in range(length - 1):
        for position in range(length - pass_count - 1):

            if items[position] > items[position + 1]:
                temporary = items[position]
                items[position] = items[position + 1]
                items[position + 1] = temporary

    return items


numbers = [5, 1, 4, 2, 8]

result = arrange_list(numbers)

print("Sorted list:", result)