from model.Edge import Edge
from model.BenchmarkNode import BenchmarkNode

class BenchmarkEdge(Edge):
    def __init__(self, start_node, end_node, lower, upper, weight):
        if not (isinstance(start_node, BenchmarkNode) and isinstance(end_node, BenchmarkNode)):
            raise ValueError("edge endpoints must be BenchmarkNode")
        super().__init__(start_node, end_node, lower, upper, weight)

class InflowEdge(BenchmarkEdge):
    def __init__(self, u, v, lower, upper, weight=0):
        super().__init__(u, v, lower, upper, weight)

class NeckEdge(BenchmarkEdge):
    def __init__(self, u, v, lower, upper, weight):
        super().__init__(u, v, lower, upper, weight)

class OutflowEdge(BenchmarkEdge):
    def __init__(self, u, v, lower, upper, weight):
        super().__init__(u, v, lower, upper, weight)

class WaitingEdge(BenchmarkEdge):
    def __init__(self, u, v, lower, upper, weight):
        super().__init__(u, v, lower, upper, weight)