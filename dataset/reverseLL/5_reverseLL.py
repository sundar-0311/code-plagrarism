class Node:
    def __init__(self, item):
        self.item = item
        self.next = None


def reverse_nodes(head):
    old = None
    node = head

    while node != None:
        saved = node.next
        node.next = old
        old = node
        node = saved

    return old


head = Node(1)
head.next = Node(2)
head.next.next = Node(3)
head.next.next.next = Node(4)

head = reverse_nodes(head)

current = head
while current:
    print(current.item, end=" ")
    current = current.next