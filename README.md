# Python Private Variables

Little toy project just to implement private variables in Python.

## Introduction

Private variables are stored within `Scope`s. A scope's variables are accessible until the scope is closed.

```py
import priv

with priv.Scope() as (_, priv):
    priv().a = 1
    b = priv().a * 2

assert b == 2 # True
priv().a # Err
```

Functions can also be declared private with the `@s.register` decorator. (Note that classes cannot be declared private, because the classes would be accessible through objects of the class.)

```py
with priv.Scope() as (s, priv):
    @s.register
    def foo():
        print("hello!")
    
    @s.register
    priv().foo() # hello!

priv().foo() # Err
```

Alternatively, the `@s.statics` decorator can be used to declare variables and functions under a scoped block.

```py
with priv.Scope() as (s, priv):
    @s.statics
    class _:
        a = 1
        b = 4

        def c(): return 9
    
    d = priv().a + priv().b + priv().c()

assert d == 14 # True
priv().a # Err
```

Caution should be taken if a variable is set to `priv()`. Anything that can access that reference will be able to access all private internals forever.

```py
with priv.Scope() as (s, priv):
    leak = priv()
    leak.a = 1

leak.a # 1... uh oh
```

## Private Variables in Functions

In order to use a private variable within a function, access needs to be granted to the function with the `@s.bind_access()` decorator.

Functions with private variable access can reference their variables through a specified `priv` parameter.

```py
with priv.Scope() as s:
    @s.statics
    class _:
        a = 1
        b = 2
        c = 3
    
    @s.bind_access()
    def print_sum(*, priv):
        _sum = priv().a + priv().b + priv().c
        print(_sum)

print_sum() # 6
```

Private functions implicitly obtain private variable access.

```py
with priv.Scope() as s:
    @s.statics
    class _:
        a = 1
        b = 2
        c = 3
    
        def get_sum(*, priv):
            return priv().a + priv().b + priv().c
    
    d = priv().get_sum()

assert d == 6 # True
```

## Private Variables in Classes

The `ScopedMeta` metaclass can be used to create a class with private variables.

Instance private variables are then accessed through `priv(o)`.

All methods are implicitly granted private variable access within the class.

```py
class Counter(metaclass=priv.ScopedMeta):
    def __init__(self, name: str, *, priv):
        self.name = name
        priv(self).counter = 0
    
    def increment(self, *, priv):
        priv(self).counter += 1

    def edit_name(self, new_name):
        self.name = new_name

    def __eq__(self, other, *, priv):
        return self.name == other.name and priv(self).name == priv(other).name

    def __str__(self, *, priv):
        return f"{self.name}: {priv(self).counter}"
```

Class private variables can be created and accessed similarly to static private variables:

```py
class Symbol(metaclass=priv.ScopedMeta):
    @priv.privatestatics
    class _:
        registry = set()
    
    def __init__(self, desc: str, *, priv):
        self.desc = desc
        priv(Symbol).registry.add(self)
    
    @classmethod
    def reg_size(cls, *, priv):
        return len(priv(cls).registry)
```

Private methods can also be created, through the `@privatemethod` decorator.

```py
class Raffle(metaclass=priv.ScopedMeta):
    def __init__(self, *, priv):
        priv(self).raffle_list = []
        priv(self).complete = False

    def enter(self, name, *, priv):
        tno = priv(self).add_ticket(name)
        print(f"Your ticket no. is {tno}")
    
    def pick(self, *, priv):
        ...

    @priv.privatemethod
    def add_ticket(self, name, *, priv): 
        ...
    
    @priv.privatemethod
    @property
    def participants(self, *, priv):
        len(priv(self).raffle_list)

    @priv.privatemethod
    @staticmethod
    def select_from(lst): 
        ...
    
    @priv.privatestatics
    class _:
        raffle_winners = []
    
    @priv.privatemethod
    @classmethod
    def add_raffle_winner(cls, winner, *, priv):
        priv(cls).raffle_winners.push(winner)
```

Inheritance is borked. Oh well.

## Multi-class Private Variables

Anything within the scope can access anything else within the scope. Thus: classes that share scopes can access each others' variables!

```py
with priv.Scope() as s:
    @s.statics
    class _:
        forced_barks = 0
        forced_meows = 0
    
    class Cat(metaclass=priv.ScopedMeta, scope=s):
        @priv.privatemethod
        def meow(self): 
            ...
        
        def make_dog_bark(self, dog, *, priv):
            priv(dog).bark()
            priv().forced_barks += 1
    
    class Dog(metaclass=priv.ScopedMeta, scope=s):
        @priv.privatemethod
        def bark(self): 
            ...
        
        def make_cat_meow(self, cat, *, priv):
            priv(cat).meow()
            priv().forced_meows += 1
```
