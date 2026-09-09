def reverse_nodes(head):
    old = None
    node = head

    while node != None:
        saved = node.next
        node.next = old
        old = node
        node = saved

    return old