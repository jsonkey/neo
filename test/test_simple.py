from unittest import TestCase

import simple


class TestSimple(TestCase):
    if not hasattr(TestCase, 'assertIs'):
        def assertIs(self, a, b):
            self.assertTrue(a is b, '%r is %r' % (a, b))

    def test_float(self):
        self.assertEquals(simple.a(-10), 0)

    def test_1(self):
        self.assertEquals(simple.a(10), 1)
