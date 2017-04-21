import functools
import os
import pkg_resources
import subprocess
import tempfile
import textwrap


def get_package_file(fname):
    return  pkg_resources.resource_filename("invoice", fname)

def wrap(ip, extra_indent):
    return textwrap.fill(ip, subsequent_indent = " "*extra_indent)
    
    

def memoise(fn):
    fn.cache = {}

    @functools.wraps(fn)
    def memoised_fn(*largs, **kargs):
        key = tuple(largs) + tuple(sorted(kargs.items()))
        if key in fn.cache:
            return fn.cache[key]
        else:
            val = fn(*largs, **kargs)
            fn.cache[key] = val
        return val
    return memoised_fn


def get_from_file(init_string='', delete = False):
    f = tempfile.NamedTemporaryFile(mode = "w", delete = False)
    fname = f.name
    f.write(init_string)
    f.close()
    editor_cmd = os.environ.get("EDITOR", "/usr/bin/vi").split()
    editor_cmd.append(f.name)
    p = subprocess.Popen(editor_cmd)
    p.wait()
    if p.returncode != 0:
        raise IOError("Error while spawning editor")
    with open(f.name, "r") as f0:
        data = f0.read()
    if delete:
        os.unlink(f.name)
    return (f.name, data)
    


    
