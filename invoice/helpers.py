import functools
import os
import subprocess
import sys
import tempfile

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


def get_from_file(init_string=''):
    f = tempfile.NamedTemporaryFile(delete = False)
    fname = f.name
    f.write(init_string.encode("utf-8"))
    f.close()
    editor_cmd = os.environ.get("EDITOR", "/usr/bin/vi").split()
    editor_cmd.append(f.name)
    p = subprocess.Popen(editor_cmd)
    p.wait()
    if p.returncode != 0:
        raise IOError("Error while spawning editor")
    with open(f.name) as f0:
        data = f0.read()
    os.unlink(f.name)
    return data
    


    
