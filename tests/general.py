import unittest
import priv

class Ticker:
    """
    Example of a ticker without private variables.
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
        Example of a ticker with private variables (using `priv.bind_scope`).
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

class TickerTest(unittest.TestCase):
    def test_nonprivate(self):
        # incrementing works
        # private variables are accessible
        # private properties are accessible
        t = Ticker()
        t.increment()
        t.increment()
        t.increment()
        self.assertEqual(t.increment(), 4)
        self.assertEqual(t.double_count, 8)

        # global count works
        # private static variables are accessible
        u = Ticker()
        u.increment()
        u.increment()
        self.assertEqual(u.global_count(), 6)

        # unlock check works
        with self.assertRaises(ValueError):
            u.unlock()
        
        # lock/unlock works
        u.lock()
        u.unlock()
        self.assertEqual(u.global_count(), 4)

        # variables are still accessible and modifiable
        t._count = 999
        t._mutable = False
        t.unlock()
        self.assertEqual(t.global_count(), -995)

        # private methods are accessible
        t._count = 999
        t._rm_from_global()
        self.assertEqual(t.global_count(), -1994)
    
    def test_scoped_meta(self):
        # incrementing works
        # private variables are accessible
        # private properties are accessible
        t = Ticker2()
        t.increment()
        t.increment()
        t.increment()
        self.assertEqual(t.increment(), 4)
        self.assertEqual(t.double_count, 8)

        # global count works
        # private static variables are accessible
        u = Ticker2()
        u.increment()
        u.increment()
        self.assertEqual(u.global_count(), 6)

        # unlock check works
        with self.assertRaises(ValueError):
            u.unlock()
        
        # lock/unlock works
        u.lock()
        u.unlock()
        self.assertEqual(u.global_count(), 4)

        ######### DIFFERENCE

        # variables are not accessible or modifiable
        with self.assertRaises(AttributeError): t.count
        with self.assertRaises(AttributeError): t._count
        with self.assertRaises(AttributeError): t.pself.count
        with self.assertRaises(AttributeError): t._mutable
        with self.assertRaises(AttributeError): t.mutable
        # private methods are inaccessible
        with self.assertRaises(AttributeError): t.rm_from_global()
    
    def test_scoped_bind(self):
        # incrementing works
        # private variables are accessible
        # private properties are accessible
        t = Ticker3()
        t.increment()
        t.increment()
        t.increment()
        self.assertEqual(t.increment(), 4)
        self.assertEqual(t.double_count, 8)

        # global count works
        # private static variables are accessible
        u = Ticker3()
        u.increment()
        u.increment()
        self.assertEqual(u.global_count(), 6)

        # unlock check works
        with self.assertRaises(ValueError):
            u.unlock()
        
        # lock/unlock works
        u.lock()
        u.unlock()
        self.assertEqual(u.global_count(), 4)

        ######### DIFFERENCE
        
        # variables are not accessible or modifiable
        with self.assertRaises(AttributeError): t.count
        with self.assertRaises(AttributeError): t._count
        with self.assertRaises(AttributeError): t.pself.count
        with self.assertRaises(AttributeError): t._mutable
        with self.assertRaises(AttributeError): t.mutable
        # private methods are inaccessible
        with self.assertRaises(AttributeError): t.rm_from_global()

if __name__ == "__main__":
    unittest.main()
