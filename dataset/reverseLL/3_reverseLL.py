class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


def reverse_linked_list(head):
    values = []

    current = head

    while current:
        values.append(current.data)
        current = current.next

    values.reverse()

    new_head = None
    tail = None

    for value in values:
        node = Node(value)

        if new_head is None:
            new_head = node
            tail = node
        else:
            tail.next = node
            tail = node

    return new_head


head = Node(1)
head.next = Node(2)
head.next.next = Node(3)

head = reverse_linked_list(head)

current = head
while current:
    print(current.data, end=" ")
    current = current.next