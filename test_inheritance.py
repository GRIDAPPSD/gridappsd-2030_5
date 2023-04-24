from typing import Dict


class Base:
    __count__: int = 0
    __config__: Dict = {}

    @classmethod
    def do_it(kls):
        kls.__count__ += 1

    @staticmethod
    def config_update(key, value):
        Base.__config__[key] = value
        return Base.__config__


class A(Base):

    def get_count(self):
        return A.__count__

    def increment_count(self):
        A.__count__ += 1


class B(Base):

    def get_count(self):
        return B.__count__

    def increment_count(self):
        B.__count__ += 1


class C(Base):
    pass


a = A()
print(a.get_count())
a.increment_count()
print(a.get_count())
b = B()
print(f"b: {b.get_count()}")
b.increment_count()
b.increment_count()
print(B.__count__)
print(A.__count__)
B.do_it()
print(B.__count__)
print(A.__count__)

print(C.config_update('foo', 'bar'))
print(C.config_update('woot', 'here_ i am'))
print(A.config_update('alpha', 'beta'))