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

# evaluation deep structure

from traced import Traced, NewInit, Obj, Call, Dispatch, UCall, UDispatch, Argument, Op1, Op2
from evaluator import Evaluator
from typing import List, Dict, Any

# for the moment the env of the evaluator is a stack (list) of dictionaries
# So... we need to "count" where the id are when we find them, the accessor then uses that count.

class Compiler(Evaluator):
    def build_access(self, id_):
        for i, env in enumerate(reversed(self.env)):
            if id_ in env:
                for j, k in enumerate(env.keys()):
                    if id_ == k:
                        def by_depth(i):
                            if i == 0:
                                return lambda var_stack: var_stack[0][j]
                            else:
                                next_level = by_depth(i-1)
                                return lambda var_stack: next_level(var_stack[1]) 
                        return by_depth(i) 
        assert id_stack, f"{id_} not defined)"


    def push_to_var_stack(self, call_env):
        f_args = list(call_env.values())
        def new_args(var_stack):
            return tuple(f_arg(var_stack) for f_arg in f_args)

        return lambda var_stack: (new_args(var_stack), var_stack)



    def new_init(self, call_env, traced):
        f_value_attributes = dict({k:self(traced_attribute) 
                                   for k, traced_attribute 
                                   in traced._obj._attributes.items()})
        f_self_obj = self(traced._obj)
        push = self.push_to_var_stack(call_env)
        def f_new_init(var_stack):
            var_stack2 = push(var_stack)
            self_obj = f_self_obj(var_stack2)
            self_obj.__dict__ = dict(map(evalt2_1(var_stack2), f_value_attributes.items())) 
            return self_obj
        return f_new_init

    def obj(self, traced):
        cls = traced._value.__class__
        return lambda var_stack: cls.__new__(cls) 

    def call(self, call_env, traced):
        push = self.push_to_var_stack(call_env)
        f_call = self(traced._return)
        return lambda var_stack: f_call(push(var_stack))

    def dispatch(self, call_env, traced):
        push = self.push_to_var_stack(call_env)
        f_call = self(traced._return)
        return lambda var_stack: f_call(push(var_stack))

    def ucall(self, traced, evaled_callable, evaled_args, evaled_kwargs):
        return lambda var_stack: (evaled_callable(var_stack)(
            *(evaled_arg(var_stack) for evaled_arg in evaled_args),
            **{var_id:evaled_kwarg(var_stack) for var_id, evaled_kwarg in evaled_kwargs.items()}))


    def udispatch(self, traced, evaled_callable, evaled_args, evaled_kwargs):
        return lambda var_stack: (evaled_callable(var_stack)(
            *(evaled_arg(var_stack) for evaled_arg in evaled_args),
            **{var_id:evaled_kwarg(var_stack) for var_id, evaled_kwarg in evaled_kwargs.items()}))

    def argument(self, traced, tag, op1):
        accessor = self.build_access(tag)
        return lambda var_stack: accessor(var_stack)

    def op1(self, traced, op1):
        op1o = traced._op1o
        return lambda var_stack: op1o(op1(var_stack))

    def op2(self, traced, op1, op2):
        op2o = traced._op2o
        return lambda var_stack: op2o(op1(var_stack), op2(var_stack))

    def traced(self, traced):
        cst = traced._value
        return lambda var_stack: cst 

    def deeptraced(self, traced):
        # here we decide all deeptraced are strongly structured
        cst_that_includes_traced = traced._value
        def either_cst_or_traced(value):
            if isinstance(value, Traced):
                return self(value)
            else:
                return just_const(value)
        match cst_that_includes_traced:
            case tuple():
                f_t = tuple(map(either_cst_or_traced, cst_that_includs_traced)) 
                return lambda var_stack: tuple(f_e(var_stack) for f_e in f_t)                
            case list():
                f_l = list(map(either_cst_or_traced, cst_that_includes_traced)) 
                return lambda var_stack: [f_e(var_stack) for f_e in f_l]                
            case slice():
                start = either_cst_or_traced(cst_that_includes_traced.start)
                stop = either_cst_or_traced(cst_that_includes_traced.stop)
                step = either_cst_or_traced(cst_that_includes_traced.step)
                return lambda var_stack: slice(start(var_stack), stop(var_stack), step(var_stack))
            case frozenset():
                l_traced = filter(is_traced, cst_that_includes_traced)
                untraced = frozenset(filter(is_untraced, cst_that_includes_traced))
                f_traced = tuple(self(fse) for fse in l_traced)
                return lambda var_stack: frozenset(f(var_stack) for f in f_traced) | untraced
            case dict():
                f2 = [(either_cst_or_traced(k), either_cst_or_traced(v)) for k,v in cst_that_includes_traced.items()]
                return lambda var_stack: dict((f_k(var_stack), f_v(var_stack)) for f_k, f_v in f2)

def is_traced(x):
    return isinstance(x, Traced)

def is_untraced(x):
    return not is_traced(x)

def just_const(x):
    return lambda var_stack: x


def evalt2_1(arg):
    def f(t2): 
        return (t2[0], t2[1](arg))
    return f


