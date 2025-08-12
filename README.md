# hltpy: high-level tracing python  
Verifiable Python? JIT execution semantics of proprietary ML RAG rules? Tracing
based embedded Python DSLs?  This generic high-level tracing library for Python
dynamically wraps chosen data, objects, class and modules, to produce an
execution trace. The execution trace can then be processed, for example with
the purpose of enabling advanced JIT interpretation of an embedded DSL.

## Example expression graph visualization:
The Render class converts an execution trace to a graphviz graph.
[show_render.py](./show_render.py) traces the following code:
```
def simple03(a, x):
    d1 = trace({'a':a, 'b':2})
    d2 = trace({'x':x, 'y':12})
    d3 = trace({(k1,k2):(v1,v2) 
                for k1, v1 in d1.items() 
                for k2, v2 in d2.items()})
    v1, v2 =  d3[('a','x')]
    return list(grange(v1, v2))

def grange(l, h):
    for i in range(int(l), int(h)):
        yield(trace(i))
  
trace1 = simple03(1, 5)
``` 
Here the code traces calls, dispatches, iterators and generator to produce the following:

![output of show_render.py](./Graph.gv.png) 

## Status
Still in development! Draft 0.2 (early August 2025) adds tracing within basic
data structures (e.g.  tuple, lists, dicts), iterators, generators, and a draft
"compiler" that demonstrates how one can build an efficient (re) evaluation
from an execution trace (note compiler doesn't cover iterators and genertors
yet).

### Previous status
First draft 0.1 (July 2025): It does enough that I can use it for combine
inference of units and types, but still has a few big gaps, such as not
allowing traced operations to be processed during tracing. Also slices are not
yet traced.

## Introduction
hltpy is a high-level tracing Python library. It loosely is inspired by JAX,
PyTorch tracing, Sympy, existing automatic differentiation code, which share
the approach of dynamic capturing of Python objects dispatches for the purpose
of dynamically providing advanced features and without burdening the developer.
In effect, all, or a selected subset of, operations are intercepted. For
example, additions expressed with a '+' symbol result in the \_\_add\_\_
operation being intercepted.  Tracing is then the act of remembering these
operation interceptions.  Tracing at a low level is common, for example, Python's
trace library.  Tracing at high-level captures both the history and the
structure of execution.  High level tracing captures as much the source code
level of the language as possible.

The purpose of the hltpy library is support embedded DSL languages that 
facilitate Python development with strong formal properties. For
example for complex explainable RAG models, and to safely implement
distributed, trustful, and reversible interpretation semantics. 

## hltpy basic features
The Traced class dynamically wraps all traced Python data and captures all
operations on this data. The base class Traced has no knowledge of the data it
is tracing (and held in the \_value attribute). Traced objects that gain
properties incrementally are tracked with the \_trace attribute. So for example
if a function call returns a generator, a new trace object Generator is created
linked to the Call trace (produced by a traced function call) through the
\_trace attribute.  Derived from Traced are classes that implicitly capture the
context of the operation that produced the traced data. These derived classes
are: Obj, DeepTraced, Function, Class, Call, Dispatch, UCall, UDispatch,
NewInit, GetItem, GetAttr, Argument, SetAttr.  DeepTraced trace built-in
structural python types like tuple, list, dict, that contain traced data.  In
this version 0.2, the Traced and derived classes are typically not directly
used during the tracing processing by the developer.  From the developer's
perspective, the tracing is controlled through the functions: trace\_modules,
trace, and from\_traced. 

## How it works
- trace\_modules places hooks to trace all class definitions and top-level 
functions of the provided module names. 
- All operations of traced objects are intercepted, including traced classes. 
- Instantiation of new objects through traced classes automatically traces 
(wraps) the newly instantiated objects of that class.
- Operation interception creates new traces. 
   - For example, if x is traced, then 
x\.f(y) will produce Call(GetAttr(Attribute('x'), x), [Argument('...', y)], {}).
- Built-in Python types like tuple, list, ... need to be told about the tracing if they are not immediately given as argument to a traced function/method. The 'trace' function is used for that.
- Each 'tracing' object also carries the original python computation in their
\_value field.
- A trace that extends a previous trace refers to that previous trace through the \_trace attribute.

What to know:

- Still in development, with gaps that I fill when I need the fix!
- Nothing is optimized. The current usage target is depth of interpretation.
- Speed is achieved by "compiling" a traced execution into a Python form that
  is JIT compatible (e.g. with JAX's JIT). The compile module shows how such a
compilation process is done. 
- Type conversation operations such as \_\_float\_\_ are not traced. (Not clear
  yet if this is a good idea!)
- Arguments to calls on traced methods/functions are all traced, if 
the module traced!
- Built-in structural types (tuple, lists, dict, some others) can contain
  traced data. Such a structure is called "deep traced". Note that I initially
was trying to only trace immutable structures, which is why sets are only
frozensets at this point. That will be corrected at some point.
- No tracing happens to calls to methods/functions in untraced modules. More
importantly, any traced objects and method/function arguments are "untraced"
before calls are done!
- \_\_setattr\_\_ allowed in \_\_init\_\_, but not elsewhere as we follow an immutable style of programming.

## What comes next
Compiling iterators and generators, then generating complementary (reversed)
traces from (forward) execution traces, then enabling trace interpretation
during tracing.

## Example trace re-evaluation and constraint analysis
The Evaluator class is a draft example how the traced data can be (re-)
evaluated. Note: that additional application specific logic is needed to
evaluate with different inputs.

The compiler module is a nice example of how evaluation becomes a compiler.
Note that iterators and generators are cannot be evaluated or compiled yet.

The BuildUpstreamConstraints is a minimilistic example of how the traced data
can be used to extract the 'reverse' flow constraints needed for structure or 
type inference.   

## Some public prior work
[autograd](https://github.com/HIPS/autograd)
[JAX JIT](https://research.google/pubs/compiling-machine-learning-programs-via-high-level-tracing/)
[PyTorch tracing](https://docs.pytorch.org/docs/1.9.0/jit.html)
[Sympy](https://www.sympy.org/en/index.html)
[Python trace](https://docs.python.org/3/library/trace.html)

## Note on ML usage in coding
Before starting I asked Gemini to draft me a first concept 
([see here](https://equational.blogspot.com/2025/06/master-class-techniques-for-llm.html) 
for how to do high-level design with an LLM). Unfortunately there was so much
missing in that first version that I wrote it from scratch and that is what you
have here. (Note that the blog presents a much more rosy picture. Yet there is
a difference between prototype and code on which you build).

_All original content copyright James Litsios, 2025._
