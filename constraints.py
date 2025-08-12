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


from traced import Traced, Obj, NewInit, Call, Dispatch, UCall, UDispatch, Argument, \
        Op1, Op2, GetAttr, SetAttr, GetItem 
from evaluator import Evaluator


class Constraint:
    def __init__(self, from_node, to_node):
        self.from_traced = from_node
        self.to_traced = to_node

    def __repr__(self):
        return (f"{self.__class__.__name__}"
                f"({self.from_traced.__class__.__name__}"
                    f"({self.from_traced!r})->"
                    f"{self.to_traced.__class__.__name__}"
                    f"({self.from_traced!r}))")

    def __hash__(self):
        return hash((self.__class__, 
                     id(self.from_traced), 
                     id(self.to_traced)))

    def __eq__(self, other):
        return ((self.__class__ == other.__class__) and
                (id(self.from_traced) == id(other.from_traced)) and
                (id(self.to_traced) == id(other.to_traced)))

class HasAttr(Constraint):
    pass

class HasInit(Constraint):
    pass

class HasCallableMethod(Constraint):
    pass

class IsCallableFunction(Constraint):
    pass

class HasItem(Constraint):
    pass

class Arg2Content(Constraint):
    pass

class BuildUpstreamConstraints(Evaluator):
    # we use evaluator, but return previous tracing
    def __init__(self):
        self.from_id_to_constraints = dict()
        super().__init__()

    def add_constraint(self, constraint):
        from_traced, to_node = constraint.from_traced, constraint.to_traced
        constraints = self.from_id_to_constraints.get(id(from_traced), None)
        if not constraints:
            constraints = list();
            self.from_id_to_constraints[id(from_traced)] = constraints
        if constraint not in constraints:
            constraints.append(constraint)

    def new_init(self, call_env, traced):
        self.add_constraint(HasInit(traced._trace, traced))
        return traced

    def obj(self, traced):
        for set_attr in traced._attributes.values():
            assert(isinstance(set_attr, SetAttr))
            _ = self(set_attr)
            self.add_constraint(HasAttr(traced, set_attr))
        return traced


    def call(self, call_env, traced):
        self(traced._trace)
        # Getted object depends on mathod call signature
        self.add_constraint(IsCallableFunction(traced, traced._callable))
        return traced

    def dispatch(self, call_env, traced):
        self(traced._trace)
        # Getted object depends on mathod call signature
        self.add_constraint(HasCallableMethod(traced, traced._callable))
        return traced

    def argument(self, traced, tag, op1):
        self.add_constraint(Arg2Content(traced, op1))
        return traced

    def op1(self, traced, op1):
        match traced:
            case GetAttr(_tag=tag, _op1=op1, _value=prev_value):
                # GetAttred object depends on attribute field
                self.add_constraint(HasAttr(traced, op1))
            case _:
                pass
        return traced

    def op2(self, traced, op1, op2):
        match traced:
           case GetItem():
                # Getted object depends on accessed item
                if op1._trace is not None:
                    self.add_constraint(HasItem(traced, op1._trace))
           case _:
                pass
        return traced

    def deeptraced(self, traced):
        return traced

    def traced(self, traced):
        return traced



