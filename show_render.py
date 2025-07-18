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

from traced import trace_modules
from render import Render

class AddX:
    def __init__(self, x):
        self.x = x

    def add_to(self, y, z=0):
        return self.x + y + z

def simple01():
    add_10 = AddX(10)
    r = add_10.add_to(5, z=2)
    return r 
    
def show_render():
    r = Render()
    trace1 = simple01()
    r.to_graph(trace1)
    r.dot.view()
    r.dot.render(format='png')
    
if  __name__ == '__main__':
    trace_modules([__name__])
    show_render()
