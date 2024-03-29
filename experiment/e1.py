name = '函数外边'


# 局部变量-->函数里面定义的变量--函数里print从里到外找name
def change_name():
    name = '函数里边'

    print('在', name, id(name))


change_name()
print(name, id(name))


d = [0] * 5
print(d)
d[2] = 2

d = {}
d['123'] = 31
print(len(d))

a = 21.50005
b = round(None, 1)
print(b)

import time
start = time.time()
print(start)
time.sleep(10)
end = time.time()
print(end)
print("Execution Time: ", end - start)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x},{self.y})"

    def show(self):
        return self

    __repr__ = __str__


p1 = Point(4, 5)
p2 = Point(3, 2)

print(repr(p1), repr(p2), sep='\n')
print(p1.__dict__)
setattr(p1, 'x', 5)
setattr(p1, 'u', 5)
print(getattr(p1, '__dict__'))

if hasattr(p1, 'x'):
    print('Yes, i have')
    print(getattr(p1, 'xx', 2000))

if not hasattr(Point, 'add'):
    setattr(Point, 'add', lambda self, other: Point(self.x + other.x, self.y + other.y))

print(Point.add)
print(p1.add)
print(p1.add(p2))

if not hasattr(p1, 'sub'):
    setattr(p1, 'sub', lambda self, other: Point(self.x - other.x, self.y - other.y))

print(p1.sub)
print(p1.sub(p1, p2))
print(p1.__dict__)
print(Point.__dict__)
