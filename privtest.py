import priv

class Ticker:
    def __init__(self):
        self.count = 0
        self.mutable = True
    
    def lock(self):
        self.mutable = False
    
    def increment(self):
        if self.mutable: self.count += 1
        return self.count

# clunky method
with priv.Scope() as s:
    class Ticker2:
        @priv.bind_scope(s)
        def __init__(self, *, pself):
            pself.count = 0
            pself.mutable = True

        @priv.bind_scope(s)
        def lock(self, *, pself):
            pself.mutable = False
        
        @priv.bind_scope(s)
        def increment(self, *, pself):
            if pself.mutable: pself.count += 1
            return pself.count
        
        @priv.bind_scope(s)
        @property
        def x(self, *, pself):
            return pself.count
        
        @priv.privatemethod(s)
        @classmethod
        def q(self, *, pself):
            pass

# better method
class Ticker3(metaclass=priv.ScopedMeta):
    def __init__(self, *, pself):
        pself.count = 0
        pself.mutable = True

    def lock(self, *, pself):
        pself.mutable = False
    
    def increment(self, *, pself):
        if pself.mutable: pself.count += 1
        return pself.count
    
    @priv.privatemethod
    @property
    def y(self):
        return 0
        
    @y.setter
    def y(self, v, *, pself):
        pself.count = v

    def expose(self, *, pself):
        return pself

    @priv.privatemethod
    def double_count(self, *, pself):
        return pself.count * 2

    def print_double_count(self, *, pself):
        print(pself.double_count())