import itertools
import os

class Formatter:
    stdout_output = False
    def __init__(self, dir="generated"):
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.base = dir

    def gen_unique_filename(self, name):
        full_name = os.path.join(self.base, name)
        basename, extension = os.path.splitext(os.path.basename(name))
        if not os.path.exists(full_name):
            return full_name
        else:
            for i in itertools.count(1):
                nname = os.path.join(self.base, "{}_({}){}".format(basename, i, extension))
                if not os.path.exists(nname):
                    return nname

    pass
