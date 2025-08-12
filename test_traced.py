"""
MIT License

Copyright (c) 2025 James Litsios

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import unittest
from traced import trace_modules, from_traced, trace, \
        Traced, Hashable, DeepTraced, DeepHashable, Iteration, \
        TRACED_CLASSES, \
        MODULES_WITH_UNTRACED_PARENTS, \
        TRACED_MODULE_NAMES
import types
import numpy as np


def plus2(a):
    return a+2

class TestTracer01(unittest.TestCase):

    def test_module01(self):
        self.assertEqual(TRACED_CLASSES, 
                         {from_traced(TestTracer01.AddX), 
                          from_traced(TestTracer01.AddX2)})

    class AddX:
        def __init__(self, x):
            self.x = x

        def add_to(self, y, z=0):
            return self.x + y + z

    def test_simple01(self):
        add_10 = TestTracer01.AddX(10)
        final_trace = add_10.add_to(5, z=2)
        self.assertEqual(final_trace._value, 17)
        
    class AddX2:
        def __init__(self, x):
            self.add10 = TestTracer01.AddX(x)

        def add_to(self, y, z=0):
            return self.add10.add_to(y, z)

    def test_simple02(self):
        add_10_2 = TestTracer01.AddX2(10)

        final_trace2 = add_10_2.add_to(5, z=2)
        self.assertEqual(final_trace2._value, 17) 

    def test_simple03(self):
        add_10 = TestTracer01.AddX(10)

        final_value = add_10.add_to(5, z=2)
        self.assertEqual(final_value, 17)
 
    def test_simple04(self):
        add_10 = TestTracer01.AddX(plus2(10)._value)

        final_value = add_10.add_to(5, z=2)
        self.assertEqual(final_value, 19)

    def test_repr01(self):
        a = trace(2)
        b = a+3
        c = b.__repr__()
        self.assertEqual(c, '2+3')
        add_10 = TestTracer01.AddX(10)
        final_value = add_10.add_to(5, z=2)
        # print(final_value.__repr__())
        # print(final_value._return.__repr__())
 
    def test_tuple01(self):
        a = trace((2,3))
        b = trace((2,trace(3)))
        c = trace((2, (3, trace(4))))
        self.assertEqual(a, (2,3))
        self.assertEqual(b._traced_value[1].__class__, Hashable)
        self.assertEqual(c._traced_value[1]._traced_value[1].__class__, Hashable)

    def test_slice01(self):
        a = trace([1,2,3,4])
        b = a[trace(1):-1]
        self.assertEqual(b._op2.__class__, DeepHashable)

    def test_slice02(self):
        a = trace(np.array([[1,2,3,4], [5,6,7,8]]))
        b = a[1, trace(1):-1]
        self.assertEqual(b._op2.__class__, DeepHashable)

    def test_dict01(self):
        a = trace({'a':1, 'b':trace(2)})
        r = a['a']
        self.assertEqual(int(r), 1)
        self.assertEqual(r._op1.__class__, DeepTraced)

    def test_dict02(self):
        a = trace({'a':1, 'b':2})
        r = a[trace('a')]
        self.assertEqual(int(r), 1)
        self.assertEqual(r._op2.__class__, Hashable)

    def test_dict02(self):
        a = trace({trace('a'):1, 'b':2})
        r = a[trace('a')]
        self.assertEqual(int(r), 1)
        self.assertEqual(r._op1.__class__, DeepTraced)
        self.assertEqual(r._op2.__class__, Hashable)

    def test_dict03(self):
        a = trace({trace('a'):1, trace('b'):2})
        r = a['a']
        self.assertEqual(int(r), 1)
        self.assertEqual(r._op1.__class__, DeepTraced)
        self.assertEqual(r._op2.__class__, Hashable)

    def test_frozenset01(self):
        a = trace(frozenset({1,2,trace(3),4}))
        r = trace(5) in a
        self.assertEqual(bool(r), False)
        self.assertEqual(a.__class__, DeepHashable)


    def test_iter01(self):
        l1 = trace([1,2,3])
        l2 = trace([e for e in l1])
        self.assertEqual(int(l2[1]), 2)
        self.assertEqual(l2._traced_value[1]._iterator._iterable, l1)


    def test_iter02(self):
        d1 = trace({'a':1, 'b':2})
        d2 = trace({'x':10, 'y':12})
        d3 = trace({(k1,k2):(v1,v2) for k1, v1 in d1.items() for k2, v2 in d2.items()})
        self.assertEqual(d3[('a','x')]._trace._traced_value[0]._trace.__class__, Iteration)
        self.assertEqual(int(d3[('a','x')][1]), 10)        


if __name__ == '__main__':
    trace_modules([__name__])
    unittest.main()


