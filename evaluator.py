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

from traced import Traced, NewInit, Obj, Call, Dispatch, UCall, UDispatch, Argument, Op1, Op2

class Evaluator:
    def __init__(self):
        self.env = list();
        self.env.append(dict())
        self.self2value = dict()

    def __call__(self, traced):
        match traced:
            case NewInit(_args=args, _kwargs=kwargs):
                if id(traced) not in self.self2value:
                    assert(id(traced._obj) == id(args[0]._op1))
                    self.enter_env(args, kwargs)
                    value = self.new_init(traced)
                    self.exit_env()
                    self.self2value[id(traced)] = value
                    return value
                else:
                    return self.self2value[id(traced)]
            case Obj():
                if id(traced) not in self.self2value:
                    value = self.obj(traced)
                    self.self2value[id(traced)] = value
                    return value
                else:
                    return self.self2value[id(traced)]
            case Call(_args=args, _kwargs=kwargs):
                self.enter_env(args, kwargs)
                value = self.call(traced)
                self.exit_env()
                return value
            case Dispatch(_args=args, _kwargs=kwargs):
                self.enter_env(args, kwargs)
                value = self.dispatch(traced)
                self.exit_env()
                return value
            case UCall(_callable=callable_, _args=args, _kwargs=kwargs):
                evaled_callable = self(callable_)
                evaled_args = [self(arg._op1) for arg in args]
                evaled_kwargs = {arg._tag: self(arg._op1) for kwarg in kwargs}
                value = self.ucall(traced, evaled_callable, evaled_args, evaled_kwargs)
                return value
            case UDispatch(_callable=callable_, _args=args, _kwargs=kwargs):
                evaled_callable = self(callable_)
                evaled_args = [self(arg._op1) for arg in args]
                evaled_kwargs = {arg._tag: self(arg._op1) for kwarg in kwargs}
                value = self.udispatch(traced, evaled_callable, evaled_args, evaled_kwargs)
                return value
            case Argument(_tag=tag, _op1=op1):
                return self.argument(traced, tag, op1) 
            case Op1(_op1=op1):
                return self.op1(traced, self(op1))
            case Op2(_op1=op1, _op2=op2):
                return self.op2(traced, self(op1), self(op2))
            case Traced():
                return self.traced(traced)
            case _:
                assert(False)

    def enter_env(self, args, kwargs):
        evaled_args = [(arg._tag, self(arg._op1)) for arg in args]
        evaled_kwargs = {arg._tag: self(arg._op1) for kwarg in kwargs}
        call_env = dict(self.env[-1])
        call_env.update({arg[0]: arg[1] for arg in evaled_args})
        call_env.update(evaled_kwargs)
        self.env.append(call_env)

    def exit_env(self):
        self.env.pop()

    def new_init(self, traced):
        value_attributes = dict({k:self(traced_attribute) 
                                 for k, traced_attribute 
                                 in traced._obj._attributes.items()})
        self_obj = self(traced._obj)
        self_obj.__dict__ = value_attributes
        return self_obj    

    def obj(self, traced):
        cls = traced._value.__class__
        obj = cls.__new__(cls)
        return obj

    def call(self, traced):
        return self(traced._return)

    def dispatch(self, traced):
        return self(traced._return)

    def ucall(self, traced, evaled_callable, evaled_args, evaled_kwargs):
        return evaled_callable(*evaled_args, **evaled_kwargs) 

    def udispatch(self, traced, evaled_callable, evaled_args, evaled_kwargs):
        return evaled_callable(*evaled_args, **evaled_kwargs) 

    def argument(self, traced, tag, op1):
        return self.env[-1][tag]

    def op1(self, traced, op1):
        return traced._op1o(op1)

    def op2(self, traced, op1, op2):
        return traced._op2o(op1, op2)

    def traced(self, traced):
        return traced._value 




