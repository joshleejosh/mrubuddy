# -*- coding: utf-8 -*-
"""
Quick and dirty MRU lists to avoid repeating yourself.
"""

import sys, os, os.path, codecs, json
from collections import deque

MRU_LEN = 48
MRULENTAG = u'^_^MRULEN='

def _u(i):
    if sys.version_info >= (3, 0):
        return str(i)
    return unicode(i)

class MRU(object):
    def __init__(self, fn=''):
        self.q = deque([], MRU_LEN)
        self.filename = fn
        self.maxlen = MRU_LEN

    def _todict(self):
        return { 'length':self.maxlen, 'values':list(self.q) }

    def __str__(self):
        return ' '.join(str(i) for i in self.q)

    def __unicode__(self):
        return u' '.join((_u(i) for i in self.q))

    def __iter__(self):
        return iter(self.q)

    def __getitem__(self, i):
        return self.q[i]

    def __len__(self):
        return len(self.q)

    def resize(self, newlen):
        if newlen == self.maxlen:
            return
        if newlen < 1:
            return
        self.maxlen = newlen
        self.q = deque(self.q, self.maxlen)

    def add(self, v):
        """
        Add a value to the MRU list without saving. If the list is full, the
        oldest value is dropped.
        """
        if v:
            self.q.append(v)

    def serialize(self):
        return json.dumps(self._todict())

    def deserialize(self, s):
        d = json.loads(s)
        if 'length' in d:
            self.resize(d['length'])
        if 'values' in d:
            self.q = deque(d['values'], self.maxlen)

    def load(self):
        if not self.filename:
            return
        if os.path.exists(self.filename):
            with codecs.open(self.filename, encoding='utf-8') as fp:
                self.deserialize(fp.read())
        else:
            self.save()

    def save(self, newid=None):
        if newid:
            self.add(newid)
        if not self.filename:
            return
        s = self.serialize()
        with codecs.open(self.filename, 'w', encoding='utf-8') as fp:
            fp.write(s)

