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


import inspect
import functools
import types
import functools
from utility import build_expression_support, CALL_PRECEDENCE, LIMIT_PRECEDENCE, \
       GET_ITEM_PRECEDENCE

class Traced:
    """ Base generic tracing class  """
    def __init__(self, value):
        """ Takes raw Python data and stores it in _value """
        # not (yet) reentrant, make sure raw data is not traced
        assert(not isinstance(value, Traced))
        self._s('_value', value)

    def _s(self, name, x):
        """ Standard __setattr__ is intercepted, so we use our own one. """
        object.__setattr__(self, name, x)

    def _precedence_repr(self, precedence):
        """ A __repr__ that tracks operator precedence rules """
        if self._precedence() > precedence:
            return ''.join(('(', self.__repr__(), ')'))
        else:
            return self.__repr__()

    def _precedence(self):
        """ The default precedence when no operation context is known """
        return CALL_PRECEDENCE

    def __repr__(self): return self._value.__repr__()

    def __getattr__(self, name):
        """ Trace get attribute """
        return GetAttr(Attribute(name), self)

    def __setattr__(self, name, value):
        """ setting attributes only allowed on objects created by traced classes. """
        # TODO revisit this. 
        # While my style is typically immutable, maybe this is too strict.
        raise NotImplementedError(
                f"__setattr__ only for Obj, not impl. "
                f"for {type(self).__name__} {name}")


    def __call__(self, *args, **kwargs):
        """ Trace a call or an object instanciation """
        # check that we understand callable type, and that module is traced
        callable_ = self._value
        if isinstance(self, Class):
            # It is a class, we create a traced object, and __init__ it.
            obj = self._value.__new__(self._value)
            obj_t = Obj(obj)
            return obj_t._init(*args, **kwargs)
        elif hasattr(callable_, '__module__') and \
                callable_.__module__ in TRACED_MODULE_NAMES: 
            # we trace the call as we know it within a traced module.
            # all args need be trace, so for that we get some help.
            sighelper = signature_helper(callable_)
            call_args, call_kwargs, has_traced = \
                sighelper.bind_traced_function(args, kwargs)
            return_trace = sighelper.func(*call_args, **call_kwargs)
            return Call(self, call_args, call_kwargs, return_trace)
        else:
            # otherwise we call but having carefully removed all tracing from args
            return_no_traced =  self._value(*[from_traced(arg) 
                                              for arg in args], 
                                            **{attr:from_traced(value) 
                                               for attr, value in kwargs.items()}) 
            return UCall(self, args, kwargs, return_no_traced) 


    def __getitem__(self, other):
        # trace a get item
        return GetItem(self, to_traced(other))

    @classmethod
    def MK_OP1(cls, method1, op1):
        # define how standard unary operators are called
        op_name = method1.__reduce__()[1][1]
        return GetAttr(Attribute(op_name), op1)()

    @classmethod
    def MK_OP2(cls, method2, op1, op2):
        # define how standard binary operators are called
        op_name = method2.__reduce__()[1][1]
        return GetAttr(Attribute(op_name), op1)(op2)

    @classmethod
    def MK_CVT(cls, method1, op1):
        # for now conversions are immediately applied to allow direct integration
        # such as call math functions. TODO revisit this!
        return method1() 


    def __add__(self, other):
        return self.__class__.MK_OP2(self._value.__add__, self, other)
    def __radd__(self, other):
        return self.__class__.MK_OP2(self._value.__radd__, self, other)


    def __sub__(self, other):
        return self.__class__.MK_OP2(self._value.__sub__, self, other)
    def __rsub__(self, other):
        return self.__class__.MK_OP2(self._value.__rsub__, self, other)


    def __mul__(self, other):
        return self.__class__.MK_OP2(self._value.__mul__, self, other)
    def __rmul__(self, other):
        return self.__class__.MK_OP2(self._value.__rmul__, self, other)


    def __truediv__(self, other):
        return self.__class__.MK_OP2(self._value.__truediv__, self, other)
    def __rtruediv__(self, other):
        return self.__class__.MK_OP2(self._value.__rtruediv__, self, other)


    def __floordiv__(self, other):
        return self.__class__.MK_OP2(self._value.__floordiv__, self, other)
    def __rfloordiv__(self, other):
        return self.__class__.MK_OP2(self._value.__rfloordiv__, self, other)


    def __mod__(self, other):
        return self.__class__.MK_OP2(self._value.__mod__, self, other)
    def __rmod__(self, other):
        return self.__class__.MK_OP2(self._value.__rmod__, self, other)


    def __pow__(self, other):
        return self.__class__.MK_OP2(self._value.__pow__, self, other)
    def __rpow__(self, other):
        return self.__class__.MK_OP2(self._value.__rpow__, self, other)


    def __lshift__(self, other):
        return self.__class__.MK_OP2(self._value.__lshirt__, self, other)
    def __rlshift__(self, other):
        return self.__class__.MK_OP2(self._value.__rlshift__, self, other)


    def __rshift__(self, other):
        return self.__class__.MK_OP2(self._value.__rshift__, self, other)
    def __rrshift__(self, other):
        return self.__class__.MK_OP2(self._value.__rrshift__, self, other)


    def __and__(self, other):
        return self.__class__.MK_OP2(self._value.__and__, self, other)
    def __rand__(self, other):
        return self.__class__.MK_OP2(self._value.__rand__, self, other)


    def __xor__(self, other):
        return self.__class__.MK_OP2(self._value.__xor__, self, other)
    def __rxor__(self, other):
        return self.__class__.MK_OP2(self._value.__rxor__, self, other)


    def __or__(self, other):
        return self.__class__.MK_OP2(self._value.__or__, self, other)
    def __ror__(self, other):
        return self.__class__.MK_OP2(self._value.__ror__, self, other)


    def __matmul__(self, other):
        return self.__class__.MK_OP2(self._value.__matmul__, self, other)
    def __rmatmul__(self, other):
        return self.__class__.MK_OP2(self._value.__rmatmul__, self, other)

    def __divmod__(self, other):
        return self.__class__.MK_OP2(self._value.__divmod__, self, other)


    def __lt__(self, other):
        return self.__class__.MK_OP2(self._value.__lt__, self, other)


    def __le__(self, other):
        return self.__class__.MK_OP2(self._value.__le__, self, other)


    def __eq__(self, other):
        return self.__class__.MK_OP2(self._value.__eq__, self, other)


    def __ne__(self, other):
        return self.__class__.MK_OP2(self._value.__ne__, self, other)


    def __gt__(self, other):
        return self.__class__.MK_OP2(self._value.__qt__, self, other)


    def __ge__(self, other):
        return self.__class__.MK_OP2(self._value.__qe__, self, other)


    def __neg__(self):
        return self.__class__.MK_OP1(self._value.__neq__, self)


    def __pos__(self):
        return self.__class__.MK_OP1(self._value.__pos__, self)


    def __invert__(self):
        return self.__class__.MK_OP1(self._value.__invert__, self)


    def __abs__(self):
        return self.__class__.MK_OP1(self._value.__abs__, self)


    def __str__(self):
        return self.__class__.MK_CVT(self._value.__str__, self)


    def __bool__(self):
        return self.__class__.MK_CVT(self._value.__bool__, self)


    def __int__(self):
        return self.__class__.MK_CVT(self._value.__int__, self)


    def __float__(self):
        return self.__class__.MK_CVT(self._value.__float__, self)


    def __complex__(self):
        return self.__class__.MK_CVT(self._value.__complex__, self)


class NeedsTupleTracing:
    """ Stateful helper to track if tuple needs to be 'deep traced' """
    def __init__(self):
        self.trace_copy = False
        self.trace = False
 

def trace_tuple_if_needed(value, ntt):
    """ Traceds a tuple with propery deeper tracing if needed """
    if isinstance(value, tuple): # TODO: process slices as well
        ntt_ = NeedsTupleTracing()
        processed = [trace_tuple_if_needed(te, ntt_) for te in value]
        if ntt_.trace_copy:
            ntt.trace_copy= True
            return Tuple(tuple(processed), value)
        elif ntt_.trace:
            ntt.trace = True
            return Tuple(value, value)
        else:
            return value
    else:
        if isinstance(value, Traced):
            ntt.trace = True
        return value

def to_traced(value):
    """ 'wraps' given value for tracing if needed. Tuples are deep checked. """
    if isinstance(value, Traced):
        # Already traced
        return value
    elif isinstance(value, tuple):
        ntt = NeedsTupleTracing()
        processed = trace_tuple_if_needed(value, ntt)
        if ntt.trace_copy or ntt.trace:
            # A tuple with traced alement(s) has its own Tuple trace.
            return processed
        else:
            # A tuple without traced elements(s) is just a simple trace.
            return Traced(value)
    else:
        return Traced(value)

""" to_trace alias (TODO cleanup) """
trace = to_traced

def from_traced(value):
    """ 'unsrap' tracing and returns raw python value """
    if isinstance(value, Traced):
        return value._value
    elif isinstance(value, Tuple):
        return tuple([from_traced(te) for te in value])
    else:
        return value

class Tuple(Traced):
    """ Traced tuples they contain traced data """
    def __init__(self, traced_tuple, tuple_value):
        self._s('_traced_tuple', traced_tuple)
        super().__init__(tuple_value)

class Obj(Traced):
    """ Traced object, built by traced classes """
    def __init__(self, value):
        # value is fresh from __new__
        # __init__ of value happens after this init so that __setattr__ get tracked. 
        super().__init__(value)
        # Traced attributes are initially empty, 
        # and dynamically added by __setattr__ called by the value's __init__ later. 
        self._s('_attributes', dict())

    def __repr__(self): 
        """ Representation of object is currently the class name and object id """
        return f"{self._value.__class__.__name__}[{id(self._value)}]"

    def _init(self, *args, **kwargs):
        """ The 'late' ___init__is called by the traced class """
        # initialize the traced object
        self_value_init = self._value.__init__
        # traced dispatch with help as all args need to be traced have have proper self 
        sighelper = signature_helper(self_value_init)
        # A key, and controversial, concept is that the traced object __init__ self is traced!
        call_args, call_kwargs, has_traced = \
            sighelper.bind_traced_function((self,) + args, kwargs)
        _ = sighelper.func(*call_args, **call_kwargs)
        return NewInit(self, call_args, call_kwargs)
 
    def __setattr__(self, name, value):
        """ Attributes can be set on traced objects produced by traced classes """
        t_value = to_traced(value)
        self._attributes[name] = SetAttr(Attribute(name), t_value)
        object.__setattr__(self._value, name, t_value._value)

class Function(Traced):
    """ Traced top level functions of a traced module """
    def __repr__(self): return self._value.__name__

class Class(Traced):
    """ Traced class of a traced module """
    def __repr__(self): return self._value.__name__

class ArgumentsBase(Traced):
    """ The traced arguments of traced calls and dispatches """
    def __init__(self, args, kwargs, value):
        self._s('_args', args)
        self._s('_kwargs', kwargs)
        super().__init__(value)

    def _arguments_repr(self, first_arg_idx=0):
        return ('('+
                ', '.join([arg.__repr__() 
                           for arg in self._args[first_arg_idx:]] + 
                          ['='.join((name, arg.__repr__())) 
                           for name, arg in self._kwargs.items()])+
                ')')


class CallBase(ArgumentsBase):
    """ The traced callable of traced calls and dispatches """
    def __init__(self, callable_, args, kwargs, value):
        self._s('_callable', callable_)
        super().__init__(args, kwargs, value)

    def __repr__(self, first_arg_idx=0):
        return (self._callable._precedence_repr(CALL_PRECEDENCE) + 
                self._arguments_repr(first_arg_idx=first_arg_idx)) 

    def _dispatch_precedence_repr(self, precedence, first_arg_idx=0):
        # Represent nicely when dispatch is a 'standard' Python operator
        symbol, symbol_precedence = self.builtin_symbol_precedence()
        if symbol:
            if symbol_precedence > precedence:
                return ''.join(('(',self._builtin_repr(symbol, symbol_precedence),')'))
            else:
                return self._builtin_repr(symbol, symbol_precedence)
        else:
            # when not a 'standard' operator
            # TODO: remove boilerplate code for precedence.
            if CALL_PRECEDENCE > precedence:
                return ''.join(('(',CallBase.__repr__(self, first_arg_idx),')'))
            else:
                return CallBase.__repr__(self, first_arg_idx)

    def _builtin_repr(self, symbol, symbol_precedence):
        # the inner details of the 'Standard' Python operator expression
        # TODO: not really 'builtin', change name.
        if not self._args:
            # unary
            return symbol+self._callable._precedence_repr(symbol_precedence)
        else:
            # binary
            if symbol != '**':
                return ''.join((self._callable._op1._precedence_repr(symbol_precedence-1),
                                symbol, 
                                to_traced(self._args[0])._precedence_repr(symbol_precedence)))
            else:
                return ''.join((self._callable._op1._precedence_repr(symbol_precedence),
                                symbol, 
                                to_traced(self._args[0])._precedence_repr(symbol_precedence-1)))

    def builtin_symbol_precedence(self):
        # The core of checking that dispatch follows the 'standard' Python operator rules
        # Return None symbol when fail.
        match self._callable:
            case GetAttr(_tag=Attribute(name=name), _op1=op1):
                # precendence table is defined at end of file
                symbol_precedence_arity = callable_name2symbol_precedence.get(name, None)
                if symbol_precedence_arity:
                    # Name is standard operator
                    symbol, precedence, arity = symbol_precedence_arity 
                    if not self._kwargs and len(self._args) == (arity-1):
                        # Arity is good too.
                        return symbol, precedence
                    else:
                        return None, CALL_PRECEDENCE
                else:
                    return None, CALL_PRECEDENCE 
            case _:
                return None, CALL_PRECEDENCE 


class Returning(CallBase):
    """ A call or dispatch has a return value """
    def __init__(self, callable_, args, kwargs, return_):
        self._s('_return', return_)
        super().__init__(callable_, args, kwargs, return_._value)

class Call(Returning):
    """ Traced call """
    pass

class Dispatch(Returning):
    """ Traced dispatch """
    def __repr__(self):
        return self._dispatch_precedence_repr(LIMIT_PRECEDENCE, 1)

    def _precedence_repr(self, precedence):
        return self._dispatch_precedence_repr(precedence, 1)

class UCall(CallBase):
    """ Trace into an untraced call """
    pass

class UDispatch(CallBase):
    """ Trace into an untraced dispatch """
    def __repr__(self):
        return self._dispatch_precedence_repr(LIMIT_PRECEDENCE)

    def _precedence_repr(self, precedence):
        return self._dispatch_precedence_repr(precedence)

class NewInit(ArgumentsBase):
    """ Traced object creation/init """
    # The traced class creates this on instanciating a traced object
    def __init__(self, obj, args, kwargs):
        self._s('_obj', obj)
        super().__init__(args, kwargs, obj._value)

    def _precedence_repr(self, precedence):
        return Traced._precedence_repr(self, precedence)

    def __repr__(self):
        return (self._obj._precedence_repr(CALL_PRECEDENCE) + 
                self._arguments_repr(1)) 


class Op1(Traced):
    """ Base for context specific unary operator tracing """
    def __init__(self, op1):
        self._s('_op1', op1)
        super().__init__(self._op1o(op1._value))

    def __repr__(self): 
         raise NotImplementedError(
                f"__repr__ not impl. for {type(self).__name__}")

    def _op1o(self, v1):
        """ The raw operation is implemented here """
        raise NotImplementedError(
                f"_op1 not impl. for {type(self).__name__}")

    def _op1s(self):
        raise NotImplementedError(
                f"_op1s not impl. for {type(self).__name__}")

    def _precedence(self):
         raise NotImplementedError(
                f"_precedence not impl. for {type(self).__name__}")


class Op2(Traced):
    """ Base for context specific binary operator tracing """
    def __init__(self, op1, op2):
        self._s('_op1', op1)
        self._s('_op2', op2)
        super().__init__(self._op2o(op1._value, op2._value))

    def __repr__(self): 
         raise NotImplementedError(
                f"__repr__ not impl. for {type(self).__name__}")

    def _op2o(self, v1, v2):
        """ The raw operation is implemented here """
        raise NotImplementedError(
                f"_op2 not implemented for {type(self).__name__}")

    def _op2s(self):
        raise NotImplementedError(
                f"_op2s not implemented for {type(self).__name__}")

    def _precedence(self):
         raise NotImplementedError(
                f"_precedence not impl. for {type(self).__name__}")


class GetItem(Op2):
    def _op2o(self, v1, v2):
        """ The raw operation of the get item operator"""
        return v1[v2]

    def __repr__(self):
        return ''.join((self._op1._precedence_repr(CALL_PRECEDENCE), 
                        '[',
                        self._op2._precedence_repr(CALL_PRECEDENCE),
                        ']'))

    def _precedence(self):
        return GET_ITEM_PRECEDENCE


class Tag:
    pass

class Lexical(Tag):
    pass

class Dynamic(Tag):
    pass

class Arg(Lexical):
    def __init__(self, param_kind, name):
        self.param_kind = param_kind
        self.name = name
        # self.idx = idx

    def __repr__(self):
        return f"{self.name}"

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (self.name == other.name and 
                    self.param_kind == other.param_kind)
        else:
            return False

    def __hash__(self):
        return hash((self.name, self.param_kind))


class Attribute(Dynamic):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}"

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (self.name == other.name)
        else:
            return False

    def __hash__(self):
        return hash(self.name)


class BaseHasAttr(Op1):
    def __init__(self, tag, op1):
        self._s('_tag', tag)
        super().__init__(op1)

    def __repr__(self):
        return self._op1._precedence_repr(CALL_PRECEDENCE)+'.'+self._tag.name


    def _precedence(self):
        return CALL_PRECEDENCE

class GetAttr(BaseHasAttr):
    def _op1o(self, v1):
        """ The raw operation of the get attribute operator"""
        return object.__getattribute__(v1, self._tag.name) 

    def __call__(self, *args, **kwargs):
        # check that we understand the method type, and that module is traced
        dispatch_self = self._op1
        self_value = dispatch_self._value
        if  ((isinstance(self_value, type) and 
              self_value.__module__ in TRACED_MODULE_NAMES) or 
             self_value.__class__.__module__ in TRACED_MODULE_NAMES):
            # traced dispatch with help as all args need to be traced have have proper self 
            sighelper = signature_helper(self._value)
            call_args, call_kwargs, has_traced = \
                sighelper.bind_traced_function((self._op1,) + args, kwargs)
            return_trace = sighelper.func(*call_args, **call_kwargs)
            return Dispatch(self, call_args, call_kwargs, return_trace)
        else:
            # non-traced dispatch, remove all tracing from args
            return_no_traced =  self._value(*[from_traced(arg) 
                                              for arg in args], 
                                            **{attr:from_traced(value) 
                                               for attr, value in kwargs.items()}) 

            return UDispatch(self, args, kwargs, return_no_traced) 


class Argument(Op1):
    """ Used to 'tag' and track the arguments to traced calls and dispatches """
    def __init__(self, tag, op1):
        self._s('_tag', tag)
        super().__init__(op1)

    def __setattr__(self, name, value):
        # Setting goes through to set on argument object.
        self._op1.__setattr__(name, value)

    def __repr__(self): 
        return self._tag.name+'='+self._op1._precedence_repr(LIMIT_PRECEDENCE)

    def _op1o(self, v1):
        # TODO: Probably best raise exception, because not expected to be called.
        return v1

    def _precedence(self):
        return CALL_PRECEDENCE



class SetAttr(BaseHasAttr):
    def _op1o(self, v1):
        # TODO: Probably best raise exception, because not expected to be called.
        return v1


def signature_helper(func_or_method):
    """ Return the signature helper object associated to the callable argument """
    if isinstance(func_or_method, types.FunctionType):
        func = func_or_method
        is_object_method = False
    else:
        assert(isinstance(func_or_method, types.MethodType))
        method = func_or_method
        func = method.__func__
        cls = method.__self__.__class__
        is_object_method = True

    if not hasattr(func, '_signature_tracing_helper'):
        # Creates helper if not already done.
        sighelper = SignatureHelper(func, is_object_method)
        func._signature_tracing_helper = sighelper
    else:
        # Get previously created helper
        sighelper = func._signature_tracing_helper
    return sighelper

class SignatureHelper:
    """ Holds a callable's inspect details to accelerate calls and dispatchs """
    def __init__(self, func, is_object_method):
        assert(not hasattr(func, '_signature_tracing_helper'))
        self.func = func
        self.is_object_method = is_object_method
        self.signature = inspect.signature(func)
        self.argument_tags = list()

        count_positionals = 0
        has_var_positional = False
        count_keywords = 0
        has_var_keyword = False

        for param in self.signature.parameters.values():
            tag = Arg(param.kind, param.name)
            self.argument_tags.append(tag)
            match tag.param_kind:
                case inspect.Parameter.POSITIONAL_ONLY:
                    count_positionals += 1

                case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    count_positionals += 1

                case inspect.Parameter.VAR_POSITIONAL:
                    has_var_positional = True

                case inspect.Parameter.KEYWORD_ONLY:
                    count_keywords += 1

                case inspect.Parameter.VAR_KEYWORD:
                    has_var_keyword = True

        self.count_positionals = count_positionals
        self.has_var_positional = has_var_positional
        self.count_keywords = count_keywords
        self.has_var_keyword = has_var_keyword



    def bind_traced_function(self, args, kwargs):
        """ Binds and traces the arugments to call or a dispatch """
        bound_args = self.signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments

        arg_iter = zip(self.argument_tags, arguments.values())
        def unroll_arg(has_traced):
            tag, value = next(arg_iter)
            if isinstance(value, Traced):
                has_traced = True 
            else:
                value = Traced(value)
            # As arguments are 'process' (unrolled) we tag them as arguments.
            return Argument(tag, value), has_traced

        has_traced = False

        call_args = list()
        for idx in range(self.count_positionals):
            argument, has_traced = unroll_arg(has_traced)
            if idx == 0 and isinstance(argument._op1, Obj):
                has_traced = False
            assert(argument._tag.param_kind 
                   == inspect.Parameter.POSITIONAL_ONLY or
                   argument._tag.param_kind 
                   == inspect.Parameter.POSITIONAL_OR_KEYWORD)
            call_args.append(argument)

        if self.has_var_positional:
            argument, has_traced = unrol_arg(has_traced)
            assert(argument._tag.param_kind 
                   == inspect.Parameter.VAR_POSITIONAL) 
            call_args.append(argument) 

        call_kwargs = dict()
        for _ in range(self.count_keywords):
            argument, has_traced = unrol_arg(has_traced)
            assert(argument._tag.param_kind 
                   == inspect.Parameter.KEYWORD_ONLY) 
            call_kwargs[argument.name] = argument

        if self.has_var_keyword:
            argument, has_traced = unroll_arg(has_traced)
            assert(argument._tag.param_kind 
                   == inspect.Parameter.VAR_KEYWORD) 
            call_kwargs[argument.name] = argument

        return call_args, call_kwargs, has_traced


TRACED_MODULE_NAMES = set()
TRACED_CLASSES = set()
MODULES_WITH_UNTRACED_PARENTS = list()


def trace_modules(module_names):
    """ Trace all classes and top-level functions of given module names """

    def trace_class(cls, has_members):
        assert(isinstance(type(cls), type))
        sighelper = signature_helper(cls.__init__)
        TRACED_CLASSES.add(cls)
        setattr(has_members, cls.__name__, Class(cls))



    def all_parents(cls):
        parents = set()
        def get_parents(cls):
            for parent in cls.__bases__:
                if parent != object:
                    parents.add(parent)
                    get_parents(parent)
        get_parents(cls)
        return parents

    def trace_module(module_name):
        module = __import__(module_name)
        to_process_classes = list()
        def trace_classes(has_members):
            for name, obj in inspect.getmembers(has_members):
                if inspect.isclass(obj):
                    if obj.__module__ == module_name:
                        parents = all_parents(obj)
                        untraced_parents = parents - TRACED_CLASSES
                        trace_classes(obj)
                        if not untraced_parents:
                            to_process_classes.append((has_members, obj))
                        else:
                            MODULES_WITH_UNTRACED_PARENTS.append((has_members,
                                                                  obj, 
                                                                  untraced_parents))
        trace_classes(module)
        for has_members, cls in to_process_classes:
            trace_class(cls, has_members)
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and obj.__module__ == module_name:
                setattr(module, name, Function(obj))


    def recheck_tracing_of_parents():
        to_recheck = MODULES_WITH_UNTRACED_PARENTS.copy()
        MODULES_WITH_UNTRACED_PARENTS.clear()
        for has_members, obj, parents_to_recheck in to_recheck:
            untraced_parents = parents_to_recheck - TRACED_CLASSES
            if not untraced_parents:
                trace_class(cls, has_members)
            else:
                MODULES_WITH_UNTRACED_PARENTS.append((has_members,
                                                      obj, 
                                                      untraced_parents))
    for module_name in module_names:
        if (module_name not in TRACED_MODULE_NAMES and
            module_name not in ['traced']):
            TRACED_MODULE_NAMES.add(module_name)
            trace_module(module_name)
    recheck_tracing_of_parents()

# table to lookup symbol, precedence and arity of standard expression operators
callable_name2symbol_precedence = \
        build_expression_support()['callable_name2symbol_precedence_arity']



