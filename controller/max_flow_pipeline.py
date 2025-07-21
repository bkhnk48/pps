from controller.NodeGenerator import ArtificialNode, RestrictionNode
from controller.EdgeGenerator import RestrictionEdge
import networkx as nx
import os
import shutil

class MaxFlowPipeline:
    def __init__(self, graph_processor=None):
        self.graph_processor = graph_processor
        self.graph = nx.DiGraph()
        self.max_flow_value = 0
        self.M = 0
        self.omega_edges = []
        self.omega_nodes = set()
        self.omega_in = set()
        self.omega_out = set()
        self.in_caps = {}
        self.out_caps = {}
        self.result_dir = self._prepare_result_dir()

    def _prepare_result_dir(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        result_dir = os.path.join(this_dir, "Result")
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        os.makedirs(result_dir)
        return result_dir

    # --- Các hàm ghi file ---
    def write_omega_file(self):
        omega_path = os.path.join(self.result_dir, "Omega.txt")
        with open(omega_path, "w") as f:
            for edge in self.omega_edges:
                f.write(f"a {edge.start_node.id} {edge.end_node.id} {edge.lower} {edge.upper} {edge.weight}\n")
        # print(f"✅ Đã ghi tập Omega vào file: {omega_path}")

    def write_omega_in_file(self, nodes):
        omega_in_path = os.path.join(self.result_dir, "Omega(IN).txt")
        with open(omega_in_path, "w") as f_in:
            for node in sorted(nodes, key=lambda n: n.id):
                f_in.write(f"{node.id}\n")
        # print(f"✅ Đã ghi Omega(IN).txt vào: {omega_in_path}")

    def write_omega_out_file(self, nodes):
        omega_out_path = os.path.join(self.result_dir, "Omega(OUT).txt")
        with open(omega_out_path, "w") as f_out:
            for node in sorted(nodes, key=lambda n: n.id):
                f_out.write(f"{node.id}\n")
        # print(f"✅ Đã ghi Omega(OUT).txt vào: {omega_out_path}")

    def write_omega_in_caps_file(self, caps):
        omega_in_path = os.path.join(self.result_dir, "Omega(IN).txt")
        with open(omega_in_path, "w") as f:
            for node in sorted(caps, key=lambda n: n.id):
                f.write(f"{node.id} {caps[node]}\n")
        # print(f"✅ Đã ghi Omega(IN).txt (có capacity) vào: {omega_in_path}")

    def write_omega_out_caps_file(self, caps):
        omega_out_path = os.path.join(self.result_dir, "Omega(OUT).txt")
        with open(omega_out_path, "w") as f:
            for node in sorted(caps, key=lambda n: n.id):
                f.write(f"{node.id} {caps[node]}\n")
        # print(f"✅ Đã ghi Omega(OUT).txt (có capacity) vào: {omega_out_path}")

    # --- Các hàm phụ trợ ---
    def is_artificial_node(self, node):
        return isinstance(node, (ArtificialNode))

    def get_node_by_id(self, node_id):
        for node in self.graph_processor.ts_nodes:
            if node.id == node_id:
                return node
        return None

    def get_time_from_id(self, node_id):
        return node_id // self.M - (1 if node_id % self.M == 0 else 0)

    def make_restriction_edge(self, node1, node2, edge):
        if not isinstance(node1, RestrictionNode):
            node1 = RestrictionNode(node1.id, restrictions=None)
        if not isinstance(node2, RestrictionNode):
            node2 = RestrictionNode(node2.id, restrictions=None)
        lower = getattr(edge, 'lower', 0)
        upper = getattr(edge, 'upper', 1)
        weight = getattr(edge, 'weight', 1)
        edge_tuple = (node1.id, node2.id, lower, upper, weight)
        return RestrictionEdge(node1, node2, edge_tuple, "Restriction")

    def _valid_edge(self, edge):
        if hasattr(edge, 'start_node') and hasattr(edge, 'end_node'):
            id1 = edge.start_node.id
            id2 = edge.end_node.id
        else:
            id1, id2 = int(edge[0]), int(edge[1])
        node1 = self.get_node_by_id(id1)
        node2 = self.get_node_by_id(id2)
        if not node1 or not node2:
            return None, None
        if self.is_artificial_node(node1) or self.is_artificial_node(node2):
            return None, None
        return node1, node2

    def _edge_matches_conditions(self, id1, id2, t1, t2, conditions):
        for x, y, a, b in conditions:
            c1 = t1 * self.M + x
            c2 = t2 * self.M + y
            if c1 == id1 and c2 == id2 and ((t1 <= a and b <= t2) or (a <= t1 and t2 <= b)\
                or (t1 <= a and t2 <= b) or (a <= t1 and b <= t2)):
                return True
        return False

    def _id_space(self, node):
        return node.id % self.M if node.id % self.M != 0 else self.M

    def _filter_tsg_edges(self):
        return [
            (e.start_node, e.end_node, getattr(e, 'weight', 1))
            for e in self.graph_processor.ts_edges
            if hasattr(e, 'start_node') and hasattr(e, 'end_node')
            and e.start_node is not None
            and e.end_node is not None
            and not (
                (e.start_node in self.omega_nodes and e.end_node in self.omega_nodes)
                and self._id_space(e.start_node) == self._id_space(e.end_node)
            )
        ]

    def _compute_caps(self, nodes, is_in=True):
        omega_node_ids = {n.id for n in self.omega_nodes}
        tsg_all = [
            (e.start_node.id, e.end_node.id, getattr(e, 'weight', 1))
            for e in self.graph_processor.ts_edges
            if hasattr(e, 'start_node') and hasattr(e, 'end_node')
        ]
        result = {}
        for node in nodes:
            node_id = node.id
            if is_in:
                total = sum(ub for u, v, ub in tsg_all if v == node_id and u not in omega_node_ids)
            else:
                total = sum(ub for u, v, ub in tsg_all if u == node_id and v not in omega_node_ids)
            result[node] = total if total > 0 else 1
        return result

    # --- Các hàm chính ---
    def find_omega(self, conditions):
        self.M = self.graph_processor.M
        self.omega_edges = []
        for edge in self.graph_processor.ts_edges:
            node1, node2 = self._valid_edge(edge)
            if not node1 or not node2:
                continue
            id1, id2 = node1.id, node2.id
            t1, t2 = self.get_time_from_id(id1), self.get_time_from_id(id2)
            if self._edge_matches_conditions(id1, id2, t1, t2, conditions):
                self.omega_edges.append(self.make_restriction_edge(node1, node2, edge))
        self.omega_nodes = set(e.start_node for e in self.omega_edges) | set(e.end_node for e in self.omega_edges)
        self.write_omega_file()

    def create_in_out(self):
        tsg_all_edges = self._filter_tsg_edges()
        omega_node_ids = {n.id for n in self.omega_nodes}
        self.omega_in = {v for u, v, _ in tsg_all_edges if v.id in omega_node_ids and u.id not in omega_node_ids}
        self.omega_out = {u for u, v, _ in tsg_all_edges if u.id in omega_node_ids and v.id not in omega_node_ids}
        self.write_omega_in_file(self.omega_in)
        self.write_omega_out_file(self.omega_out)

    def add_capacities(self):
        self.in_caps = self._compute_caps(self.omega_in, is_in=True)
        self.out_caps = self._compute_caps(self.omega_out, is_in=False)
        self.write_omega_in_caps_file(self.in_caps)
        self.write_omega_out_caps_file(self.out_caps)

    def compute_max_flow(self):
        G = nx.DiGraph()
        for edge in self.omega_edges:
            G.add_edge(str(edge.start_node.id), str(edge.end_node.id), capacity=edge.upper)
        G.add_node("vS")
        G.add_node("vT")
        for node, cap in self.in_caps.items():
            if str(node.id) in G:
                G.add_edge("vS", str(node.id), capacity=cap)
        for node, cap in self.out_caps.items():
            if str(node.id) in G:
                G.add_edge(str(node.id), "vT", capacity=cap)
        flow_value, _ = nx.maximum_flow(G, "vS", "vT")
        self.max_flow_value = flow_value
        return flow_value

    def run_all(self, conditions):
        self.M = self.graph_processor.M
        self.find_omega(conditions)
        self.create_in_out()
        if not self.omega_in:  # Nếu omega_in rỗng
            self.max_flow_value = 0
            return 0
        self.add_capacities()
        return self.compute_max_flow()