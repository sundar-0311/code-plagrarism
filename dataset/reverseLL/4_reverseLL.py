class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def reverse(head):
    prev = None
    curr = head

    while curr is not None:
        temp = curr.next
        curr.next = prev
        prev = curr
        curr = temp

    return prev


def print_list(head):
    while head:
        print(head.val, end=" ")
        head = head.next


head = Node(1)
head.next = Node(2)
head.next.next = Node(3)
head.next.next.next = Node(4)

head = reverse(head)

print_list(head)