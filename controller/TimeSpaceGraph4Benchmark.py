from model.BenchmarkNode import BenchmarkNode, TopBulbNode, BottomBulbNode, BottleneckNode
from model.BenchmarkEdge import BenchmarkEdge, InflowEdge, NeckEdge, OutflowEdge, WaitingEdge

class TimeSpaceGraph4Benchmark:
    def __init__(self, time_horizon, time_step=1):
        self.H = time_horizon
        self.d = time_step
        self.M = None
        self.V = {}  # node.id -> Node subclass
        self.E = {}  # edge_key -> Edge subclass

    # Cantor pairing (directed) for edge key
    def get_edge_key(self, a, b):
        s = a + b
        return int(s * (s + 1) / 2 + b)

    def add_node(self, node):
        if node.id not in self.V:
            self.V[node.id] = node

    def add_edge(self, edge):
        a = edge.start_node.id
        b = edge.end_node.id
        key = self.get_edge_key(a, b)
        if key not in self.E:
            self.E[key] = edge

    def get_space_id(self, ts_id):
        if ts_id % self.M == 0:
            return ts_id % self.M + self.M
        return ts_id % self.M

    def get_time(self, ts_id):
        if ts_id % self.M == 0:
            return ts_id // self.M - 1
        return ts_id // self.M

    def add_nodes_and_edges(self, list_ids, lower=0, upper=1, weight=1, d=1):
        if len(list_ids) != 6:
            raise ValueError("Invalid length of list")
        list_ids = sorted(list_ids)
        a1, a2, a3, a4 = list_ids[0], list_ids[1], list_ids[2], list_ids[3]
        t1, t2, t3, t4 = self.get_time(a1), self.get_time(a2), self.get_time(a3), self.get_time(a4)
        b1, b2, b3, b4 = self.get_space_id(a1), self.get_space_id(a2), self.get_space_id(a3), self.get_space_id(a4)
        v1, v2 = list_ids[4], list_ids[5]

        if (v1 <= self.M * self.H) or (v2 <= self.M * self.H) or (v2 - v1) != 1:
            raise ValueError("Invalid BottleneckNode ID.")
        if (t1 != t2) or (t3 != t4) or (t1 == t3) or (t2 == t4) or (t1 == t2 and t2 == t3 and t3 == t4):
            raise ValueError("Invalid Time of Node")
        if ((b1 != b3) and (b1 != b4)) or ((b1 == b3) and (b1 == b4)) or ((b2 != b3) and (b2 != b4)) or \
           ((b2 == b3) and (b2 == b4)) or (b3 == b4) or (b1 == b2):
            raise ValueError("Invalid Space ID")

        self.add_node(TopBulbNode(a1))
        self.add_node(TopBulbNode(a2))
        self.add_node(BottomBulbNode(a3))
        self.add_node(BottomBulbNode(a4))
        self.add_node(BottleneckNode(v1))
        self.add_node(BottleneckNode(v2))

        self.add_edge(InflowEdge(self.V[a1], self.V[v1], lower, upper, 0))
        self.add_edge(InflowEdge(self.V[a2], self.V[v1], lower, upper, 0))
        self.add_edge(NeckEdge(self.V[v1], self.V[v2], lower, upper, weight))
        self.add_edge(OutflowEdge(self.V[v2], self.V[a3], lower, upper, 0))
        self.add_edge(OutflowEdge(self.V[v2], self.V[a4], lower, upper, 0))
        if b2 == b4:
            self.add_edge(WaitingEdge(self.V[a2], self.V[a4], lower, upper, d))
            self.add_edge(WaitingEdge(self.V[a1], self.V[a3], lower, upper, d))
        else:
            self.add_edge(WaitingEdge(self.V[a2], self.V[a3], lower, upper, d))
            self.add_edge(WaitingEdge(self.V[a1], self.V[a4], lower, upper, d))

    def build_tsg_4_benchmark(self, benchmark_graph):
        benchmark_graph.generate_space_graph(benchmark_graph.file_map)
        benchmark_graph.export_space_graph_dimacs_file()
        self.M = benchmark_graph.width * benchmark_graph.height

        max_id = self.M * self.H
        for edge in benchmark_graph.E.values():
            s = edge.start_node
            t = edge.end_node
            lower = edge.lower
            upper = edge.upper
            weight = edge.weight
            for i in range(0, self.H - weight + 1, self.d):
                a1 = self.M * i + s.id
                a2 = self.M * (i + weight) + t.id
                a3 = self.M * i + t.id
                a4 = self.M * (i + weight) + s.id
                v1 = max_id + 1
                v2 = max_id + 2
                max_id += 2
                self.add_nodes_and_edges([a1, a2, a3, a4, v1, v2], lower, upper, weight, self.d)

    def export_tsg_dimacs_file(self, tsg_file_path="./TSG_4_Benchmark.txt"):
        edges_list = list(self.E.values())
        edges_list.sort(key=lambda e: (e.start_node.id, e.end_node.id))
        with open(tsg_file_path, "w", encoding="utf-8") as f:
            for edge in edges_list:
                u = edge.start_node.id
                v = edge.end_node.id
                lower = edge.lower
                upper = edge.upper
                weight = edge.weight
                if lower is None or upper is None or weight is None:
                    raise ValueError(f"Missing lower/upper/weight for edge {u}→{v}")
                if upper < lower:
                    raise ValueError(f"upper < lower for edge {u}→{v}")
                line = f"a {u} {v} {lower} {upper} {weight}\n"
                f.write(line)