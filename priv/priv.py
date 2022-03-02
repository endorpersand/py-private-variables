"""
03/01/2022
"""
from collections import ChainMap
import types
from typing import Any
import inspect

__all__ = ('Scope', 'bind_scope', 'ScopedMeta', 'privatemethod')

class Scope:
    """
    Stores information for private variables
    """
    def __init__(self, values: dict[str, Any] = None, *, static: dict[str, Any] = None):
        _open = True
        self.is_open = lambda: _open
        
        def _close():
            nonlocal _open
            _open = False
        self.close = _close

        if values is None: values = {}
        if static is None: static = {}
        _access = {}
        self._make_oa = lambda: OpenAccess(_access, values, static) if _open else None

    # references instance of values that is always open
    def access(self):
        if self.is_open():
            return self._make_oa()
        
        raise TypeError("Cannot access a closed scope")

    def __getitem__(self, k):
        return getattr(self.access()(None), k)
    
    def __setitem__(self, k, v):
        setattr(self.access()(None), k, v)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()
    
    def __repr__(self) -> str:
        if self.is_open():
            return f"<open {self.__class__.__qualname__} at {hex(id(self))}>"
        return f"<closed {self.__class__.__qualname__} at {hex(id(self))}>"

class OpenAccess:
    """
    Gives full access to scope forever (and should NOT be revealed or exposed)
    """
    def __init__(self, _access: dict[int, dict], values: dict[str, Any], static: dict[str, Any]):
        _base = ChainMap(static)
        
        def make_chain_map(accessor):
            if accessor is None: return _base
            return _access.setdefault(id(accessor), _base.new_child(values))
        self._chain_map = make_chain_map
    
    def __call__(self, accessor):
        return _DictWrapper(self._chain_map(accessor))

class _DictWrapper:
    """
    Converts __getattribute__ and __setattribute__ calls to __getitem__ and __setitem__
    """
    def __init__(self, dct: dict):
        object.__setattr__(self, "_get", lambda it: dct[it])

        def _set(it, v):
            dct[it] = v
        object.__setattr__(self, "_set", _set)

        def _del(it):
            del dct[it]
        object.__setattr__(self, "_del", _del)
    
    def __getattribute__(self, i):
        try:
            return object.__getattribute__(self, "_get")(i)
        except KeyError as e:
            raise AttributeError(str(e))
    
    def __setattr__(self, i, v):
        try:
            return object.__getattribute__(self, "_set")(i, v)
        except KeyError as e:
            raise AttributeError(str(e))
    
    def __delattr__(self, i):
        try:
            return object.__getattribute__(self, "_del")(i)
        except KeyError as e:
            raise AttributeError(str(e))
    
def kw_in_signature(f, name):
    """
    Check if keyword is valid in the signature
    """
    try:
        inspect.signature(f).bind_partial(**{name: 0})
    except TypeError:
        return False
    return True
    
# enable pself for the method
def bind_scope(scope: Scope, name: str = "pself", *, check_valid = True, implicit_drop = False):
    """
    Decorator. Expose private variables to this method (through parameter `pself`).
    Does not work on properties yet.
    """
    oa = scope.access()
    def decorator(o):
        if isinstance(o, types.FunctionType):
            f = o
            if implicit_drop and not kw_in_signature(f, name):
                return o
            def func(self, *args, **kwargs):
                values = oa(self)
                nkwargs = {**kwargs, name: values}
                return f(self, *args, **nkwargs)
            return func

        elif isinstance(o, (classmethod, staticmethod)):
            f = o.__func__
            if implicit_drop and not kw_in_signature(f, name):
                return o
            def func(*args, **kwargs):
                values = oa(None)
                nkwargs = {**kwargs, name: values}
                return f(*args, **nkwargs)
            return type(o)(func)

        # does not work on properties
        elif check_valid:
            raise TypeError("Cannot bind scope here")

        else:
            return o
    return decorator

class ScopedMeta(type):
    """
    Metaclass that handles private variables, 
    avoiding need for a scope context manager and bind_scope together.
    """
    def __new__(cls, clsname, bases, attrs, *, scope = None, name="pself"):
        if scope is None: scope = Scope()
        dec = bind_scope(scope, name, check_valid=False, implicit_drop=True)

        attrs = {k: dec(a) for k, a in attrs.items()}
        return super(ScopedMeta, cls).__new__(cls, clsname, bases, attrs)