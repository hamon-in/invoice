import functools

def memoise(fn):
    fn.cache = {}
    functools.wraps(fn)
    def memoised_fn(*largs, **kargs):
        key = tuple(largs) + tuple(sorted(kargs.items()))
        if key in fn.cache:
            return fn.cache[key]
        else:
            val = fn(*largs, **kargs)
            fn.cache[key] = val
        return val
    return memoised_fn
