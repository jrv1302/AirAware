import gc

class Node:
    def __init__(self, name):
        self.name = name
        self.ref = None

    def __del__(self):
        print(f"Object {self.name} is being garbage collected")

gc.enable()

print("GC enabled:", gc.isenabled())

a = Node("A")
b = Node("B")

a.ref = b
b.ref = a

a = None
b = None

print("Objects before gc.collect():", gc.get_count())

collected = gc.collect()

print("Garbage objects collected:", collected)
print("Objects after gc.collect():", gc.get_count())