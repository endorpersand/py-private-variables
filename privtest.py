import priv
import doctest

class Ticker:
    """
    Example of a ticker without private variables.

    Everything works as intended. We can increment the ticker.
    >>> t = Ticker()
    >>> t.increment()
    1
    >>> t.increment()
    2

    Properties work.
    >>> t.double_count
    4

    The global ticker works.
    >>> u = Ticker()
    >>> u.increment()
    1
    >>> u.global_count()
    3

    Lock & unlock mechanics!
    >>> u.unlock()
    Traceback (most recent call last):
        ...
    ValueError: Ticker is not locked!
    >>> u.lock()
    >>> u.unlock()
    >>> u.global_count()
    2
    >>> u.double_count
    0

    But hidden variables are still accessible! We can edit them!
    >>> t._count = 999
    >>> t._mutable = False
    >>> t.unlock()
    >>> t.global_count()
    -997
    >>> t._rm_from_global()
    """
    _global_count = 0

    def __init__(self):
        self._count = 0
        self._mutable = True
    
    def lock(self):
        self._mutable = False
    
    def increment(self):
        if self._mutable: 
            self._count += 1
            self.__class__._global_count += 1
        return self._count

    @property
    def double_count(self):
        return self._count * 2
    
    @classmethod
    def global_count(cls):
        return cls._global_count
    
    def _rm_from_global(self):
        cls = self.__class__
        cls._global_count -= self._count
    
    def unlock(self):
        if self._mutable: raise ValueError("Ticker is not locked!")

        self._rm_from_global()
        self._count = 0
        self._mutable = True

class Ticker2(metaclass=priv.ScopedMeta, scope=priv.Scope(static={"global_count": 0})):
    """
    Example of a ticker with private variables (using `priv.ScopedMeta`).

    Everything works as intended. We can increment the ticker.
    >>> t = Ticker2()
    >>> t.increment()
    1
    >>> t.increment()
    2

    Properties work.
    >>> t.double_count
    4

    The global ticker works.
    >>> u = Ticker2()
    >>> u.increment()
    1
    >>> u.global_count()
    3

    Lock & unlock mechanics!
    >>> u.unlock()
    Traceback (most recent call last):
        ...
    ValueError: Ticker is not locked!
    >>> u.lock()
    >>> u.unlock()
    >>> u.global_count()
    2
    >>> u.double_count
    0

    But hidden variables are no longer accessible!
    >>> t.count
    Traceback (most recent call last):
        ...
    AttributeError: 'Ticker2' object has no attribute 'count'
    >>> t._count
    Traceback (most recent call last):
        ...
    AttributeError: 'Ticker2' object has no attribute '_count'
    >>> t.mutable
    Traceback (most recent call last):
        ...
    AttributeError: 'Ticker2' object has no attribute 'mutable'
    >>> t.rm_from_global()
    Traceback (most recent call last):
        ...
    AttributeError: 'Ticker2' object has no attribute 'rm_from_global'
    """

    def __init__(self, *, pself):
        pself.count = 0
        pself.mutable = True
    
    def lock(self, *, pself):
        pself.mutable = False
    
    def increment(self, *, pself):
        if pself.mutable: 
            pself.count += 1
            pself.static.global_count += 1
        return pself.count

    @property
    def double_count(self, *, pself):
        return pself.count * 2
    
    @classmethod
    def global_count(cls, *, pself):
        return pself.static.global_count
    
    @priv.privatemethod
    def rm_from_global(self, *, pself):
        pself.static.global_count -= pself.count
    
    def unlock(self, *, pself):
        if pself.mutable: raise ValueError("Ticker is not locked!")

        pself.rm_from_global()
        pself.count = 0
        pself.mutable = True

# clunky method
with priv.Scope(static={"global_count": 0}) as s:
    class Ticker3:
        """
        Example of a ticker with private variables (using `bind_scope`).

        Everything works as intended. We can increment the ticker.
        >>> t = Ticker3()
        >>> t.increment()
        1
        >>> t.increment()
        2

        Properties work.
        >>> t.double_count
        4

        The global ticker works.
        >>> u = Ticker3()
        >>> u.increment()
        1
        >>> u.global_count()
        3

        Lock & unlock mechanics!
        >>> u.unlock()
        Traceback (most recent call last):
            ...
        ValueError: Ticker is not locked!
        >>> u.lock()
        >>> u.unlock()
        >>> u.global_count()
        2
        >>> u.double_count
        0

        But hidden variables are no longer accessible!
        >>> t.count
        Traceback (most recent call last):
            ...
        AttributeError: 'Ticker3' object has no attribute 'count'
        >>> t._count
        Traceback (most recent call last):
            ...
        AttributeError: 'Ticker3' object has no attribute '_count'
        >>> t.mutable
        Traceback (most recent call last):
            ...
        AttributeError: 'Ticker3' object has no attribute 'mutable'
        >>> t.rm_from_global()
        Traceback (most recent call last):
            ...
        AttributeError: 'Ticker3' object has no attribute 'rm_from_global'
        """

        @priv.bind_scope(s)
        def __init__(self, *, pself):
            pself.count = 0
            pself.mutable = True
        
        @priv.bind_scope(s)
        def lock(self, *, pself):
            pself.mutable = False
        
        @priv.bind_scope(s)
        def increment(self, *, pself):
            if pself.mutable: 
                pself.count += 1
                pself.static.global_count += 1
            return pself.count

        @priv.bind_scope(s)
        @property
        def double_count(self, *, pself):
            return pself.count * 2
        
        @priv.bind_scope(s)
        @classmethod
        def global_count(cls, *, pself):
            return pself.static.global_count
        
        @priv.privatemethod(s)
        def rm_from_global(self, *, pself):
            pself.static.global_count -= pself.count
        
        @priv.bind_scope(s)
        def unlock(self, *, pself):
            if pself.mutable: raise ValueError("Ticker is not locked!")

            pself.rm_from_global()
            pself.count = 0
            pself.mutable = True

if __name__ == "__main__":
    doctest.testmod()