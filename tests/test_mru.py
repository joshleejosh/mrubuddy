# -*- coding: utf-8 -*-

import sys, os, unittest, tempfile, shutil, codecs
import mrubuddy

class MRUTest(unittest.TestCase):
    def _u(self, i):
        if sys.version_info >= (3, 0):
            return str(i)
        return unicode(i)

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.tempdir)
        except OSError:
            pass

    def test_mru(self):
        m = mrubuddy.MRU()
        self.assertEqual(m.maxlen, mrubuddy.MRU_LEN)
        self.assertEqual(m.q.maxlen, m.maxlen)

        # should safely nop when no file is given
        m.load()

        self.assertEqual(str(m), '')
        m.add(3)
        m.add('Q')
        self.assertIn(3, m)
        self.assertIn('Q', m)
        self.assertNotIn('R', m)
        self.assertEqual(len(m), 2)
        self.assertEqual(m.serialize(), u'^_^MRULEN=48\n3\nQ\n')

        # add and save, but the save should safely nop
        m.save('Z')
        self.assertEqual(len(m), 3)
        self.assertEqual(m.serialize(), u'^_^MRULEN=48\n3\nQ\nZ\n')

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
        self.assertNotIn(0, m)
        self.assertNotIn(5, m)
        self.assertIn(6, m)
        self.assertIn(7, m)
        self.assertIn(8, m)
        self.assertIn(9, m)
        self.assertEqual(m.serialize(), u'^_^MRULEN=4\n6\n7\n8\n9\n')

        # resize up
        m.resize(6)
        self.assertEqual(m.serialize(), u'^_^MRULEN=6\n6\n7\n8\n9\n')

        # resizing down lops off the head
        m.resize(2)
        self.assertEqual(m.serialize(), u'^_^MRULEN=2\n8\n9\n')

        # can't resize to 0
        m.resize(0)
        self.assertEqual(m.serialize(), u'^_^MRULEN=2\n8\n9\n')

    def test_file(self):
        # create an empty file
        fn = os.path.join(self.tempdir, 't1')
        with open(fn, 'w') as fp:
            fp.write('')
        self.assertTrue(os.path.exists(fn))

        m = mrubuddy.MRU(fn)
        m.load()
        self.assertEqual(os.path.getsize(fn), 0)
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
        self.assertEqual(s, u'^_^MRULEN=4\n14\n89576\nwhatever\n62.73\n')

        n = mrubuddy.MRU(fn)
        n.load()
        self.assertEqual(n.serialize(), u'^_^MRULEN=4\n14\n89576\nwhatever\n62.73\n')

    def test_newfile(self):
        # If we try to load a file that doesn't exists, create it.
        fn = os.path.join(self.tempdir, 't2')
        self.assertFalse(os.path.exists(fn))
        m = mrubuddy.MRU()
        m.filename = fn
        m.load()
        self.assertTrue(os.path.exists(fn))
        self.assertEqual(os.path.getsize(fn), 0)

    """TODO
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
    """

    def test_load_save_unicode(self):
        fn = os.path.join(self.tempdir, 'tu')
        with codecs.open(fn, 'w', encoding='utf-8') as fp:
            us = u'%s7\nm🏀m\nñññ\nó�ó\nppp\nqqq'%mrubuddy.MRULENTAG
            fp.write(us)
        m = mrubuddy.MRU(fn)
        m.load()
        self.assertEqual(m.maxlen, 7)
        self.assertEqual(len(m), 5)

        self.assertEqual(self._u(m), u'm🏀m ñññ ó�ó ppp qqq')
        m.add('r')
        m.add(u'ß')
        m.add(u'𐂜')
        self.assertEqual(self._u(m), u'ñññ ó�ó ppp qqq r ß 𐂜')
        m.save()

        with codecs.open(fn, encoding='utf-8') as fp:
            ut = u'%s7\nñññ\nó�ó\nppp\nqqq\nr\nß\n𐂜\n'%mrubuddy.MRULENTAG
            self.assertEqual(fp.read(), ut)

