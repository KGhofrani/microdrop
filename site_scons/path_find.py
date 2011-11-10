import os

from path import path


def path_find(filename):
    for p in [path(d) for d in os.environ['PATH'].split(';')]:
        if len(p.files(filename)):
            return p
    return None