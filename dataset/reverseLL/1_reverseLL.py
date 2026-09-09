class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


def reverse_list(head):
    previous = None
    current = head

    while current:
        next_node = current.next
        current.next = previous
        previous = current
        current = next_node

    return previous


def display(head):
    while head:
        print(head.data, end=" ")
        head = head.next


head = Node(1)
head.next = Node(2)
head.next.next = Node(3)
head.next.next.next = Node(4)

head = reverse_list(head)

display(head)