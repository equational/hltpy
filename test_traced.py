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
from traced import trace_modules, from_traced, trace, Traced, TRACED_CLASSES, \
        MODULES_WITH_UNTRACED_PARENTS, \
        TRACED_MODULE_NAMES

def plus2(a):
    return a+2

class TestTracer01(unittest.TestCase):

    def test_module01(self):
        self.assertEqual(TRACED_CLASSES, {from_traced(TestTracer01.AddX), from_traced(TestTracer01.AddX2)})

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
        self.assertEqual(b._traced_tuple[1].__class__, Traced)
        self.assertEqual(c._traced_tuple[1][1].__class__, Traced)

if __name__ == '__main__':
    trace_modules([__name__])
    unittest.main()


