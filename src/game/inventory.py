from collections import deque

class Inventory:
    def __init__(self, capacity=5):
        self.items = deque()
        self.capacity = capacity

    def add(self, item):
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True

    def remove_left(self):
        if self.items:
            return self.items.popleft()
