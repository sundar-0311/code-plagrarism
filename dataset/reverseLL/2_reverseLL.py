class Node:
    def __init__(self, value):
        self.value = value
        self.next = None


def reverse(head):
    if head is None or head.next is None:
        return head

    new_head = reverse(head.next)

    head.next.next = head
    head.next = None

    return new_head


def show(head):
    while head:
        print(head.value, end=" ")
        head = head.next


head = Node(1)
head.next = Node(2)
head.next.next = Node(3)
head.next.next.next = Node(4)

head = reverse(head)

show(head)