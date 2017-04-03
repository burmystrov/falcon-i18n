from functools import total_ordering, wraps


class Promise:
    """The class is used to distinguish proxy object. Since proxy object
    is created in the closure."""
    pass


def lazy(func, *result_classes):
    """Turns callable object into a lazy evaluated object. The results aren't
    memoized. It returns Proxy object.
    """

    @total_ordering
    class __proxy__(Promise):
        __prepared = False

        def __init__(self, args, kw):
            self.__args = args
            self.__kw = kw

            if not self.__prepared:
                self.__prepare_class()
                self.__prepared = True

        @classmethod
        def __prepare_class(cls):
            # Reflect methods from result classes into the proxy object
            for resultclass in result_classes:
                for _type in resultclass.mro():
                    for name in _type.__dict__.keys():
                        if hasattr(cls, name):
                            continue

                        if not callable(getattr(_type, name)):
                            continue

                        setattr(cls, name, cls.__promise__(name))

        @classmethod
        def __promise__(cls, method_name):
            def __wrapper__(self, *args, **kwargs):
                f = func(*self.__args, **self.__kw)
                return getattr(f, method_name)(*args, **kwargs)

            return __wrapper__

        def __evaluate(self):
            return func(*self.__args, **self.__kw)

        def __str__(self):
            return str(self.__evaluate())

        def __bytes__(self):
            return bytes(self.__evaluate())

        def __repr__(self):
            return repr(self.__evaluate())

        def __hash__(self):
            return hash(self.__evaluate())

        def __eq__(self, other):
            if isinstance(other, Promise):
                other = other.__evaluate()
            return self.__evaluate() == other

        def __lt__(self, other):
            if isinstance(other, Promise):
                other = other.__evaluate()
            return self.__evaluate() < other

    @wraps(func)
    def wrapper(*args, **kwargs):
        return __proxy__(args, kwargs)

    return wrapper
