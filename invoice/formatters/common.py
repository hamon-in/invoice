import itertools
import os

class Formatter:
    stdout_output = False
    def __init__(self, dir="generated"):
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.base = dir

    def gen_unique_filename(self, name, overwrite):
        full_name = os.path.join(self.base, name)
        if overwrite:
            return full_name
        if not os.path.exists(full_name):
            return full_name
        else:
            basename, extension = os.path.splitext(os.path.basename(name))
            for i in itertools.count(1):
                nname = os.path.join(self.base, "{}_({}){}".format(basename, i, extension))
                if not os.path.exists(nname):
                    return nname

