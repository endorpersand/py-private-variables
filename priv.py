from collections import ChainMap
import types
from typing import Any, Callable, MutableMapping, Optional, TypeVar, Union
import inspect

__all__ = ('Scope', 'register', 'static_of', 'bind_access', 'ScopedMeta', 'privatestatics', 'privatemethod')
PythonMethod = Union[types.FunctionType, classmethod, staticmethod, property]
C = TypeVar("C", bound=Callable)

class Scope:
    """
    This object acts as a key into the private scope.
    Scopes are open and the internals are freely accessible until `scope.close()` is called.
        - Alternatively, `with Scope() as s: ...` can be used to automatically close the scope 
        at the end of the block.
    
    - To register items statically into the scope, `declare`, `register`, `static_of` should be used.
    - To allow functions to reference items in the scope, `bind_access` should be used.
    - Classes
        - `ScopedMeta` to enable class private features
        - `privatemethod` (in `ScopedMeta` classes) to declare private methods
        - `privatestatics` (in `ScopedMeta` classes) to declare private class variables
        - All methods (in `ScopedMeta` classes) can reference items in the scope without `bind_access`.
    
    - Functions with scope access (either because they are a method in `ScopedMeta` or because they 
    have been `bind_access`'d can access scope variables through `priv(ctx)`. 
    See `bind_access` for more information.)
    - While a scope is open, variables can be accessed through `scope.priv(ctx)`.
    """

    def __init__(self, priv_name="priv"):
        self.priv_name = lambda: priv_name

        _open: bool = True
        self.is_open = lambda: _open
        
        def _close():
            nonlocal _open
            _open = False
        self.close = _close
        
        _access = _InternalAccess()
        # references instance of values that is always open
        self._access = lambda: self._require_open() and _access

        # bind = bind_scope(self, implicit_drop=True)
        # def _register_pmethod(fn: PythonMethod, name: str = None):
        #     self._require_open()
        #     p = PrivateMethod(bind(fn))
        #     static[name or p._name] = p
        # self._register_pmethod = _register_pmethod

    def priv(self, ref=None):
        return self._access()(ref)

    def _require_open(self):
        if not self.is_open():
            raise TypeError("Cannot access a closed scope")
        return True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()
    
    def __repr__(self) -> str:
        if self.is_open():
            return f"<open {self.__class__.__qualname__} at {hex(id(self))}>"
        return f"<closed {self.__class__.__qualname__} at {hex(id(self))}>"
    
    def __iter__(self):
        return iter((self, self.priv))

    def bind_access(self, *args, **kwargs):
        """
        Decorator. See `priv.bind_access(...)`.
        """
        return bind_access(self, *args, **kwargs)

    def declare(self, var: str, val):
        return setattr(self.priv(), var, val)
    
    @property
    def register(self):
        """
        Decorator. See `priv.register(...)`.
        """
        return register(self)
    
    @property
    def statics(self):
        """
        Decorator. See `priv.static_of(...)`.
        """
        return static_of(self)

class _InternalAccess:
    """
    Free access to variables within the scope. You do NOT want to expose this object.
    """
    def __init__(self):
        self._static: dict[str, Any] = {}
        self._class:  dict[int, dict[str, Any]] = {}
        self._inst:   dict[int, dict[str, Any]] = {}
    
    def __call__(self, ref: Any = None):
        use = [self._static]

        if ref is None:
            accessor = None
            ty = None
        elif inspect.isclass(ref):
            use.append(self._class.setdefault(object.__hash__(ref), {}))
            accessor = None
            ty = ref
        else: 
            use.append(self._class.setdefault(object.__hash__(type(ref)), {}))
            use.append(self._inst.setdefault(object.__hash__(ref), {}))

            accessor = ref
            ty = type(ref)
        
        return _ScopeVariables(ChainMap(*reversed(use)), accessor, ty)

class _ScopeVariables:
    """
    Object that provides all the scoped variables as attributes (This instance should NOT be revealed or exposed.)
    """
    def __init__(self, dct: MutableMapping, accessor, ty):
        def _get(it):
            o = dct[it]
            if isinstance(o, PrivateMethod):
                return o.__func__.__get__(accessor, ty)
            return o
        object.__setattr__(self, "_get", _get)

        def _set(it, v):
            o = dct.get(it, None)
            if isinstance(o, PrivateMethod) and (s := getattr(o.__func__, "__set__", None)) is not None:
                return s(accessor, v)
            dct[it] = v
        object.__setattr__(self, "_set", _set)

        def _del(it):
            o = dct.get(it, None)
            if isinstance(o, PrivateMethod) and (d := getattr(o.__func__, "__delete__", None)) is not None:
                return d(accessor)
            del dct[it]
        object.__setattr__(self, "_del", _del)
    
    def __getattribute__(self, i):
        try:
            return object.__getattribute__(self, "_get")(i)
        except KeyError as e:
            err = AttributeError(f"{str(e)}")
            raise err.with_traceback(None) from None
    
    def __setattr__(self, i, v):
        try:
            return object.__getattribute__(self, "_set")(i, v)
        except KeyError as e:
            err = AttributeError(f"{str(e)}")
            raise err.with_traceback(None) from None
    
    def __delattr__(self, i):
        try:
            return object.__getattribute__(self, "_del")(i)
        except KeyError as e:
            err = AttributeError(f"{str(e)}")
            raise err.with_traceback(None) from None

def _kw_in_signature(f, name):
    """
    Check if keyword is valid in the signature
    """
    try:
        inspect.signature(f).bind_partial(**{name: 0})
    except TypeError:
        return False
    return True

def register(scope: Scope):
    """
    Decorator. Used to register a private STATIC function into the scope. For methods within a class, use `@privatemethod`.
    
    This decorator cannot be used on a class, because it would not enable truly private classes.
    """
    def deco(o):
        if inspect.isclass(o): raise TypeError("Cannot use @register decorator on class")
        scope.declare(o.__name__, o)
        # destroy the reference.
    return deco

def static_of(scope: Scope):
    """
    Class decorator. Consumes the class and inherits all of the variables and functions into the scope's static.
    For private class fields, use `@privatestatics`.

    This class should not be written as a regular class (i.e., don't include `self` in functions).
    Any declarations in the form of `r"__.+"` are ignored.
    `class _(static_of(scope)): ...`
    """
    bind = scope.bind_access(check_valid=False, implicit_drop=True)

    def deco(cls):
        for k, v in privatestatics(cls).refs.items():
            scope.declare(k, bind(v))
    return deco

def bind_access(scope: Scope, *, check_valid = True, implicit_drop = False):
    """
    Decorator. Allow a function to access scope internals through a `priv` parameter. This should be above `classmethod`, `property`, and the like.

    The `priv` parameter has 3 versions:
    - `priv()`: access variables/methods defined within the scope but not within any class
    - `priv(cls)`: access class variables/methods of `cls`
    - `priv(self)`: access instance variables/methods of `self`

    Decorator parameters:
    - `check_valid` (default `true`): Raise error if this decorator was called on an invalid object
    - `implicit_drop` (default `False`): If false, error when the parameter is missing.

    """
    name = scope.priv_name()
    oa = scope._access()

    def add_kw(f: C) -> C:
        if not _kw_in_signature(f, name):
            if implicit_drop: return f
            else: raise TypeError(f"Function does not provide {name} parameter to override")
        
        def func(*args, **kwargs):
            nkwargs = {**kwargs, name: oa}
            return f(*args, **nkwargs)
        func.__name__ = f.__name__
            
        return func

    def decorator(o: PythonMethod):
        if callable(o):
            return add_kw(o)

        elif isinstance(o, (classmethod, staticmethod)):
            f = o.__func__
            cls = type(o)

            return cls(add_kw(f))
        
        elif isinstance(o, PrivateMethod):
            return o

        elif isinstance(o, property):
            def mapper(f: Optional[Callable]):
                return f and add_kw(f)
            
            return property(
                *(mapper(getattr(o, a)) for a in ("fget", "fset", "fdel")),
                doc = o.__doc__
            )

        elif check_valid:
            raise TypeError("Cannot bind scope here")

        else:
            return o
    
    return decorator

### Scoping a class

class ScopedMeta(type):
    """
    Metaclass that allows a scope to keep track of class and instance private variables
    """
    def __new__(cls, clsname, bases, attrs, *, scope = None):
        if scope is None: scope = Scope()

        # automatically bind access to all attrs
        bind = bind_access(scope, check_valid=False, implicit_drop=True)

        nattrs = {}
        pm: dict[str, PrivateMethod] = {}
        pf: dict[str, Any] = {}

        for k, a in attrs.items():
            if isinstance(a, PrivateMethod):
                pm[k] = a
            elif isinstance(a, privatestatics):
                pf.update(a.refs)
            else: 
                nattrs[k] = bind(a)
        
        c = super(ScopedMeta, cls).__new__(cls, clsname, bases, nattrs)

        # register all the private methods
        priv = scope.priv(c)
        for k, p in pm.items():
            setattr(priv, k, p._bs(bind))
        for k, p in pf.items():
            setattr(priv, k, bind(p))
        return c

# @privatestatics
class privatestatics:
    """
    Class decorator. When used on an inner class of a scoped class (one that is metaclassed by `ScopedMeta`), the fields are registered into the scope.
    If NOT used in a scoped class, these fields will be exposed.
    """
    def __init__(self, cls):
        self.refs = {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("__") and not k.startswith(f"_{cls.__name__}__")
        }

# @privatemethod
def privatemethod(f: "PythonMethod"):
    """
    Decorator. When used in a scoped class (one that is metaclassed by `ScopedMeta`), the private method is registered into the scope.
    If NOT used in a scoped class, the function is exposed.
    """
    if isinstance(f, property):
        return PrivateProperty(f)

    return PrivateMethod(f)

class PrivateMethod:
    def __init__(self, fn: PythonMethod):
        self.__func__ = fn

    def _bs(self, bsf):
        self.__func__ = bsf(self.__func__)
        return self
    
    @property
    def _name(self):
        """
        Exposes function's name for non-ScopedMeta classes
        """
        fn = self.__func__
        if hasattr(fn, "__func__"): return fn.__func__.__name__
        if hasattr(fn, "fget"): return fn.fget.__name__
        if hasattr(fn, "__name__"): return fn.__name__

class PrivateProperty(PrivateMethod):
    def getter(self, fget):
        p = self.__func__
        return PrivateProperty(property(fget, p.fset, p.fdel, p.__doc__))
    def setter(self, fset):
        p = self.__func__
        return PrivateProperty(property(p.fget, fset, p.fdel, p.__doc__))
    def deleter(self, fdel):
        p = self.__func__
        return PrivateProperty(property(p.fget, p.fset, fdel, p.__doc__))
