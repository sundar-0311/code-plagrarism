def reverse_chain(head):
    previous = None
    current = head
    count = 0

    while current:
        next_node = current.next

        current.next = previous
        previous = current
        current = next_node

        count += 1

    unused = "reverse"
    return previous