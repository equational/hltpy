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

from traced import Traced, NewInit, Obj, Call, Dispatch, UCall, UDispatch, \
        Argument, Op1, Op2, GetAttr
from constraints import BuildUpstreamConstraints
import graphviz

class Render:
    def __init__(self):
        pass

    def to_graph(self, value):
        buc = BuildUpstreamConstraints()
        buc(value)
        id2constraints = buc.from_id_to_constraints


        self.dot = graphviz.Digraph('Graph')
        self.dot.attr(rankdir='TB', size='2,5', dpi='300')
        self.dot.attr('node', shape='box')

        self.nodes = dict()
        self.edges = dict()
        self.rendered_nodes = set()

        self.apply_node_and_edges(value)

    def mk_node_label(self, value):
        def val(x):
            if isinstance(x, (int, float)):
                return str(x)
            elif isinstance(x, str):
                return "'"+x+"'"
            elif hasattr(x, '__name__'):
                return getattr(x, '__name__')
            else:
                return x.__class__.__name__
 
        match value:
            case NewInit(_obj=obj):
                return  f"""<<TABLE>
                                <TR>
                                    <TD>{value.__class__.__name__}</TD>
                                    <TD>{obj._value.__class__.__name__}</TD>
                                </TR>
                            </TABLE>>"""
            case Obj():
                return  f"""<<TABLE>
                                <TR>
                                    <TD>{value.__class__.__name__}</TD>
                                    <TD>{value._value.__class__.__name__}</TD>
                                </TR>
                            </TABLE>>"""
            case Argument(_tag=tag):
                return  f"""<<TABLE>
                                <TR>
                                    <TD>{value.__class__.__name__}</TD>
                                    <TD>{str(tag)}</TD>
                                </TR>
                            </TABLE>>"""
            case GetAttr(_tag=tag):
                return  f"""<<TABLE>
                                <TR>
                                    <TD>{value.__class__.__name__}</TD>
                                    <TD>{tag.name}</TD>
                                </TR>
                            </TABLE>>"""
            case Traced(_value=x):
                if isinstance(value, (Call, Dispatch, UCall, UDispatch)):
                    return  f"""<<TABLE>
                                    <TR>
                                        <TD>{val(x)}</TD>
                                    </TR>
                                    <TR>
                                        <TD>{value.__class__.__name__}</TD>
                                    </TR>
                               </TABLE>>"""
                else:
                    return val(x)

            case _: 
                return value.__class__.__name__


    def mk_edge_label(self, e_name, n_0, n_1):
        return e_name

    def node_label(self, value):
        n_key = id(value)
        label = self.nodes.get(n_key, None)
        if not label:
            label = self.mk_node_label(value)
            self.nodes[n_key]= label
        return label

    def edge_label(self, e_name, n_0, n_1):
        e_key = (e_name, id(n_0), id(n_1))
        label = self.edges.get(e_key, None)
        if not label:
            label = self.mk_edge_label(e_name, n_0, n_1)
            self.edges[e_key] = label
        return e_key, label

    def apply_node(self, value):
        label = self.node_label(value)
        self.dot.node(str(id(value)), label)


    def apply_edge(self, e_name, n_0, n_1):
        e_key, label = self.edge_label(e_name, n_0, n_1)
        self.dot.edge(str(id(n_0)), str(id(n_1)), label=label)



    def apply_node_and_edges(self, value):
        assert(isinstance(value, Traced))
        value_id = id(value)
        if value_id not in self.rendered_nodes:
            self.rendered_nodes.add(value_id)
            self.apply_node(value)
            for e_name, n_1 in value.__dict__.items():
                if isinstance(n_1, Traced):
                    self.apply_edge(e_name, value, n_1)
                    self.apply_node_and_edges(n_1)
                elif isinstance(n_1, tuple):
                    for idx, n_1_e in enumerate(n_1):
                        self.apply_edge(e_name+':'+str(idx), value, n_1_e)
                        self.apply_node_and_edges(n_1_e)
                elif isinstance(n_1, dict):
                    for item, n_1_e in n_1.items():
                        self.apply_edge(e_name+':'+item, value, n_1_e)
                        self.apply_node_and_edges(n_1_e)






