# -*- coding: utf-8 -*-
"""
Stub main for testing the file format.
"""

from . import MRU

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
            type=str,
            help='File to store the MRU in')
    parser.add_argument('value',
            nargs='*',
            type=str,
            help='Values to load into the MRU')
    args = parser.parse_args()

    m = MRU(args.filename)
    m.load()
    for v in args.value:
        m.add(v)
    m.save()

