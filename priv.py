from collections import ChainMap
import types
from typing import Any, Callable
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

        # references instance of values that is always open
        self.access = lambda: self._require_open() and OpenAccess(_access, values, static)
        def _register_default(k: str, v):
            self._require_open()
            values[k] = v
        self._register_default = _register_default

    def _require_open(self):
        if not self.is_open():
            raise TypeError("Cannot access a closed scope")
        return True

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
        
        def make_vars(accessor):
            if accessor is None: return _base
            cm = _base.new_child(values)
            return _access.setdefault(id(accessor), _ScopeVariables(accessor, cm))
        self._vars = make_vars
    
    def __call__(self, accessor):
        return self._vars(accessor)

class _ScopeVariables:
    """
    Converts __getattribute__ and __setattribute__ calls to __getitem__ and __setitem__
    """
    def __init__(self, accessor, dct: dict):
        def _get(it):
            o = dct[it]
            if isinstance(o, PrivateMethod):
                return _override_kw(o.__func__.__get__(accessor, type(accessor)), pself=self)
            return o
        object.__setattr__(self, "_get", _get)

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

def _override_kw(fn, **kwargs):
    """
    Creates a function (that isn't a partial) that has overridden some kwargs
    """
    if all(kw_in_signature(fn, k) for k in kwargs):
        def func(*args, **kw):
            nkwargs = {**kw, **kwargs}
            return fn(*args, **nkwargs)
        return func
    return fn

class _PrivateSentinel:
    def __repr__(self): return "PRIVATE"

    def __set_name__(self, o, name):
        self.attr = name
    def __get__(self, obj, objtype=None): raise AttributeError(f"'{objtype.__name__}' object has no attribute '{self.attr}'")

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
            if not kw_in_signature(f, name):
                if implicit_drop: return o
                else: raise TypeError(f"Function does not provide {name} parameter to override")
            def func(self, *args, **kwargs):
                values = oa(self)
                nkwargs = {**kwargs, name: values}
                return f(self, *args, **nkwargs)
            return func

        elif isinstance(o, (classmethod, staticmethod)):
            f = o.__func__
            if not kw_in_signature(f, name):
                if implicit_drop: return o
                else: raise TypeError(f"Function does not provide {name} parameter to override")
            def func(*args, **kwargs):
                values = oa(None)
                nkwargs = {**kwargs, name: values}
                return f(*args, **nkwargs)
            return type(o)(func)

        elif isinstance(o, PrivateMethod):
            if o._name is None: raise ValueError("Could not resolve privatemethod's name")
            scope._register_default(o._name, o)
            return _PrivateSentinel()

        elif isinstance(o, property):
            np = [o.fget, o.fset, o.fdel, o.__doc__]
            def a(i):
                f = np[i]
                if f is None: return
                if hasattr(f, "scoped"): return
                if not kw_in_signature(f, name):
                    if implicit_drop: return
                    else: raise TypeError(f"Function does not provide {name} parameter to override")
                
                def func(self, *args, **kwargs):
                    values = oa(self)
                    nkwargs = {**kwargs, name: values}
                    return f(self, *args, **nkwargs)
                np[i] = func
            for i in range(3): a(i)
            return property(*np)

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
        nattrs = {}
        for k, a in attrs.items():
            if isinstance(a, PrivateMethod):
                scope._register_default(k, a)
                continue

            d = dec(a)
            if not isinstance(d, _PrivateSentinel): nattrs[k] = d
        return super(ScopedMeta, cls).__new__(cls, clsname, bases, nattrs)

class PrivateMethod:
    def __init__(self, fn: "Callable | classmethod | staticmethod | property"):
        self.__func__ = fn

    @property
    def _name(self):
        fn = self.__func__
        if hasattr(fn, "__func__"): return fn.__func__.__name__
        if hasattr(fn, "fget"): return fn.fget.__name__
        return fn.__name__

    def __get__(self, obj, objtype=None):
        raise TypeError("Cannot use privatemethod outside of scoped classes")

# @privatemethod
# @privatemethod(scope)
def privatemethod(scope_or_function: "Scope | Callable" = None):
    if isinstance(scope_or_function, Scope):
        def decorator(fn: "Callable | classmethod | staticmethod | property"):
            pm = PrivateMethod(fn)
            scope_or_function._register_default(pm._name, pm)
            return # it's been registered, destroy the attribute
        return decorator
    
    return PrivateMethod(scope_or_function)