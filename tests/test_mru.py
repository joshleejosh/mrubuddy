# -*- coding: utf-8 -*-

import sys, os, unittest, tempfile, shutil, codecs, json
import mrubuddy

class MRUTest(unittest.TestCase):
    def _u(self, i):
        if sys.version_info >= (3, 0):
            return str(i)
        return unicode(i)

    def setUp(self):
        if sys.version_info < (3, 0):
            self.assertCountEqual = self.assertItemsEqual
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.tempdir)
        except OSError:
            pass

    def assertContents(self, m, ln, va):
        self.assertEqual(m.maxlen, ln)
        self.assertEqual(m.q.maxlen, ln)
        self.assertCountEqual(list(m.q), va)

    def assertJson(self, fn, ln, va):
        with codecs.open(fn, encoding='utf-8') as fp:
            jd = json.load(fp)
            self.assertCountEqual(sorted(list(jd.keys())), ['length', 'values'])
            self.assertEqual(jd['length'], ln)
            self.assertCountEqual(jd['values'], va)

    def test_mru(self):
        # new empty instance
        m = mrubuddy.MRU()
        self.assertEqual(m.maxlen, mrubuddy.MRU_LEN)
        self.assertEqual(m.q.maxlen, m.maxlen)
        self.assertCountEqual(m.q, [])

        # should safely nop when no file is given
        self.assertEqual(m.filename, '')
        m.load()

        self.assertEqual(str(m), '')
        m.add(3)
        m.add('Q')
        self.assertIn(3, m)
        self.assertIn('Q', m)
        self.assertNotIn('R', m)
        self.assertNotIn('3', m) # string, not int
        self.assertEqual(len(m), 2)
        self.assertContents(m, 48, [3, 'Q'])

        # add+save, but the save should safely nop
        m.save('Z')
        self.assertContents(m, 48, [3, 'Q', 'Z'])
        self.assertEqual(m.filename, '')

    def test_iter(self):
        m = mrubuddy.MRU()
        data = [ 'a', 'b', u'ç', 'd', ]
        for c in data:
            m.add(c)
        for i,c in enumerate(m):
            self.assertEqual(c, data[i])

    def test_maxlen(self):
        m = mrubuddy.MRU()
        self.assertEqual(m.maxlen, mrubuddy.MRU_LEN)
        m.resize(4)
        self.assertEqual(m.maxlen, 4)
        for i in range(10):
            m.add(i)
        # first 6 values should have been pushed out
        self.assertNotIn(0, m)
        self.assertNotIn(5, m)
        self.assertIn(6, m)
        self.assertIn(7, m)
        self.assertIn(8, m)
        self.assertIn(9, m)
        self.assertContents(m, 4, [6, 7, 8, 9])

        # resize up
        m.resize(6)
        self.assertContents(m, 6, [6, 7, 8, 9])

        # resizing down lops off the head
        m.resize(2)
        self.assertContents(m, 2, [8, 9])

        # can't resize to 0
        m.resize(0)
        self.assertContents(m, 2, [8, 9])

    def test_file(self):
        # create an empty file
        fn = os.path.join(self.tempdir, 't1')
        with open(fn, 'w') as fp:
            fp.write('{}')
        self.assertTrue(os.path.exists(fn))

        m = mrubuddy.MRU(fn)
        m.load()
        self.assertEqual(m.maxlen, mrubuddy.MRU_LEN)
        self.assertEqual(len(m), 0)

        m.resize(4)
        m.add('hi there')
        m.add(32.6)
        m.add(14)
        m.save()
        with open(fn) as fp:
            s = fp.read()
        self.assertEqual(s, m.serialize())

        m.add(89576)
        m.add('whatever')
        m.save(62.73)
        with open(fn) as fp:
            s = fp.read()
        self.assertEqual(s, m.serialize())
        a = [14, 89576, 'whatever', 62.73]
        self.assertContents(m, 4, a)

        self.assertJson(fn, 4, a)
        n = mrubuddy.MRU(fn)
        n.load()
        self.assertContents(n, 4, a)

    def test_newfile(self):
        # If we try to load a file that doesn't exists, create it.
        fn = os.path.join(self.tempdir, 't2')
        self.assertFalse(os.path.exists(fn))
        m = mrubuddy.MRU()
        m.filename = fn
        m.load()
        self.assertTrue(os.path.exists(fn))
        self.assertJson(fn, mrubuddy.MRU_LEN, [])

    def test_newline(self):
        fn = os.path.join(self.tempdir, 'nl')
        m = mrubuddy.MRU(fn)
        m.add('foo')
        m.add('bar\nbar')
        m.add('baz')
        self.assertEqual(len(m), 3)
        m.save()

        n = mrubuddy.MRU(fn)
        n.load()
        self.assertEqual(len(n), 3)

    def test_load_save_unicode(self):
        fn = os.path.join(self.tempdir, 'tu')
        with codecs.open(fn, 'w', encoding='utf-8') as fp:
            json.dump({
                'length':7,
                'values':[ u'm🏀m', u'ñññ', u'ó�ó', u'ppp', u'qqq', ]
                }, fp)
        m = mrubuddy.MRU(fn)
        m.load()
        self.assertEqual(m.maxlen, 7)
        self.assertEqual(len(m), 5)

        self.assertContents(m, 7, [ u'm🏀m', u'ñññ', u'ó�ó', u'ppp', u'qqq', ])
        m.add('r')
        m.add(u'ß')
        m.add(u'𐂜')
        va = [ u'ñññ', u'ó�ó', u'ppp', u'qqq', 'r', u'ß', u'𐂜', ]
        self.assertContents(m, 7, va)
        m.save()

        with codecs.open(fn, encoding='utf-8') as fp:
            jd = json.load(fp)
            self.assertEqual(jd['length'], 7)
            if sys.version_info >= (3, 0):
                self.assertCountEqual(jd['values'], va)
            else:
                self.assertItemsEqual(jd['values'], va)

