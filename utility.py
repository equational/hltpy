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


import io
import csv


CALL_PRECEDENCE = 1
GET_ITEM_PRECEDENCE = 2
LIMIT_PRECEDENCE = 13

full_operator_data = """Symbol,Callable Name,Type,Arity,Associativity,Reflected Name,In-place Name,Precedence
+,__add__,Binary Arithmetic,2,Left-to-right,__radd__,__iadd__,7
-,__sub__,Binary Arithmetic,2,Left-to-right,__rsub__,__isub__,7
*,__mul__,Binary Arithmetic,2,Left-to-right,__rmul__,__imul__,6
@,__matmul__,Binary Arithmetic,2,Left-to-right,__rmatmul__,__imatmul__,6
/,__truediv__,Binary Arithmetic,2,Left-to-right,__rtruediv__,__itruediv__,6
//,__floordiv__,Binary Arithmetic,2,Left-to-right,__rfloordiv__,__ifloordiv__,6
%,__mod__,Binary Arithmetic,2,Left-to-right,__rmod__,__imod__,6
divmod,__divmod__,Binary Arithmetic,2,Left-to-right,__rdivmod__,,6
**,__pow__,Binary Arithmetic,2,Right-to-left,__rpow__,__ipow__,4
<<,__lshift__,Binary Bitwise,2,Left-to-right,__rlshift__,__ilshift__,8
>>,__rshift__,Binary Bitwise,2,Left-to-right,__rrshift__,__irshift__,8
&,__and__,Binary Bitwise,2,Left-to-right,__rand__,__iand__,9
^,__xor__,Binary Bitwise,2,Left-to-right,__rxor__,__ixor__,10
|,__or__,Binary Bitwise,2,Left-to-right,__ror__,__ior__,11
<,__lt__,Comparison,2,N/A,,,12
<=,__le__,Comparison,2,N/A,,,12
==,__eq__,Comparison,2,N/A,,,12
!=,__ne__,Comparison,2,N/A,,,12
>,__gt__,Comparison,2,N/A,,,12
>=,__ge__,Comparison,2,N/A,,,12
-,__neg__,Unary,1,N/A,,,5
+,__pos__,Unary,1,N/A,,,5
~,__invert__,Unary,1,N/A,,,5
abs,__abs__,Unary,1,N/A,,,1
(),__call__,Function Call,Variadic,Left-to-right,,,1
.,__getattr__,Attribute GetAttr,2,Left-to-right,,,2
[],__getitem__,Item GetAttr,2,Left-to-right,,,2
str,__str__,Conversion,1,N/A,,,1
bool,__bool__,Conversion,1,N/A,,,1
int,__int__,Conversion,1,N/A,,,1
float,__float__,Conversion,1,N/A,,,1
complex,__complex__,Conversion,1,N/A,,,1"""

right2left_ops = {'': '',
 '__add__': '__radd__',
 '__sub__': '__rsub__',
 '__mul__': '__rmul__',
 '__truediv__': '__rtruediv__',
 '__floordiv__': '__rfloordiv__',
 '__mod__': '__rmod__',
 '__pow__': '__rpow__',
 '__lshift__': '__rlshift__',
 '__rshift__': '__rrshift__',
 '__and__': '__rand__',
 '__xor__': '__rxor__',
 '__or__': '__ror__',
 '__matmul__': '__rmatmul__'}



def build_expression_support():
    callable_name2symbol_precedence_arity = {}

    f = io.StringIO(full_operator_data)
    reader = csv.reader(filter(lambda row: row.strip() and not row.startswith('#'), f))
    header = next(reader)
    processed_methods = set()
    for row in reader:
        symbol, callable_name, op_type, arity, _, \
                reflected_name, inplace_name, precedence = row
        callable_name2symbol_precedence_arity[callable_name] = (
                symbol, 
                int(precedence), 
                int(arity) if arity != 'Variadic' else None)
    return { 'callable_name2symbol_precedence_arity' : callable_name2symbol_precedence_arity }


def is_builtin(value):
    return type(value) in (bool, str, int, float, tuple, list, dict)    



