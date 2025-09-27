from controller.NodeGenerator import ArtificialNode
from model.Edge import ArtificialEdge
from pathlib import Path
import random

class ExitEdge(ArtificialEdge):
    def __init__(self, vS, vT, lower, upper, weight, temporary=True):
        super().__init__(vS, vT, lower, upper, weight, temporary=temporary)

class ArtificialNodeInserter:
    DEFAULT_LOWER = 0
    DEFAULT_UPPER = 1
    DEFAULT_GAMMA = 1230919231

    def __init__(self, processor, vs_id=None, vt_id=None, start_artificial_id=None):
        self.processor = processor
        self.pipeline = processor.pipeline

        max_id = self._get_max_id()
        offset = self._get_offset()

        self.vs_id = vs_id if vs_id is not None else max_id + offset
        self.vt_id = vt_id if vt_id is not None else max_id + offset + 1
        self.artificial_node_id = (
            start_artificial_id
            if start_artificial_id is not None
            else random.randint(self.vt_id + 10, self.vt_id + 1000)
        )

        self.vS = ArtificialNode(id=self.vs_id, label="vS")
        self.vT = ArtificialNode(id=self.vt_id, label="vT")
        self.edges_added = []

    def _get_max_id(self): # Lấy ID lớn nhất từ bộ nhớ
        """all_ids = [node.id for node in self.processor.ts_nodes]
        if hasattr(self.processor, "graph") and hasattr(self.processor.graph, "nodes"):
            all_ids += list(self.processor.graph.nodes.keys())
        return max(all_ids) if all_ids else 1000"""
        max_id = max((node.id for node in self.processor.ts_nodes), default=0)

        if getattr(self.processor, "graph", None) and hasattr(self.processor.graph, "nodes"):
            graph_max = max(self.processor.graph.nodes.keys(), default=0)
            max_id = max(max_id, graph_max)
        
        return max_id if max_id > 0 else 1000

    def _get_offset(self):
        node_count = len(set(node.id for node in self.processor.ts_nodes))
        return max(1000, node_count * 10)

    # ==== Các hàm tiện ích, phụ trợ ==== #
    def create_artificial_edge(self, start, end, lower, upper, weight, temporary=True):
        return ArtificialEdge(start, end, lower, upper, weight, temporary=temporary)

    def find_original_edge(self, u, v):
        for e in self.processor.ts_edges:
            if getattr(e, 'start_node', None) and getattr(e, 'end_node', None):
                if e.start_node.id == u and e.end_node.id == v:
                    return e
        return None

    def create_artificial_nodes(self, idx):
        node1 = ArtificialNode(id=self.artificial_node_id, label=f"virt_{idx}_1")
        node2 = ArtificialNode(id=self.artificial_node_id + 1, label=f"virt_{idx}_2")
        self.artificial_node_id += 2
        self.processor.ts_nodes.extend([node1, node2])
        self.processor.graph.nodes[node1.id] = node1
        self.processor.graph.nodes[node2.id] = node2
        return node1, node2

    def add_artificial_edges(self, node1, node2, lower, upper, F, U):
        edges_artificial = [
            self.create_artificial_edge(self.vS, node1, lower, F - U, 0),
            self.create_artificial_edge(node1, node2, lower, upper, 0),
            self.create_artificial_edge(node2, self.vT, lower, F - U, 0)
        ]
        self.processor.ts_edges.extend(edges_artificial)
        self.edges_added.extend(edges_artificial)
    
    def remove_and_replace_edge(self, u, v, node1, node2, lower, upper, cost):
        removed = self.processor.remove_edge_by_id(u, v)
        if not removed:
            print(f"⚠️  Không tìm thấy cung gốc ({u} → {v}) để loại bỏ")
        edges_replacement = [
            self.create_artificial_edge(self.processor.graph.nodes[u], node1, lower, upper, cost),
            self.create_artificial_edge(node2, self.processor.graph.nodes[v], lower, upper, 0)
        ]
        self.processor.ts_edges.extend(edges_replacement)
        self.edges_added.extend(edges_replacement)
    
    
    # ==== Các hàm được gọi trong run() ====
    def add_artificial_source_sink_nodes(self):
        self.processor.ts_nodes.extend([self.vS, self.vT])
        self.processor.graph.nodes[self.vS.id] = self.vS
        self.processor.graph.nodes[self.vT.id] = self.vT

        # Thêm vS vào started_nodes nếu chưa có
        if hasattr(self.processor, "started_nodes"):
            if self.vS.id not in self.processor.started_nodes:
                self.processor.started_nodes.append(self.vS.id)
        # Thêm vT vào target_nodes nếu chưa có
        if hasattr(self.processor, "target_nodes"):
            if self.vT not in self.processor.target_nodes:
                self.processor.target_nodes.append(self.vT)

    def ask_gamma(self):
        gamma_input = input("Nhập gamma (cost vS→vT, mặc định = 1230919231): ")
        return int(gamma_input) if gamma_input.strip() else self.DEFAULT_GAMMA
    
    def add_exit_edge_vs_to_vt(self, U, gamma):
        F = self.pipeline.max_flow_value
        edge = ExitEdge(self.vS, self.vT, self.DEFAULT_LOWER, max(F - U, 0), gamma)
        self.processor.ts_edges.append(edge)
        self.edges_added.append(edge)

    def collect_omega_in_edges(self):
        """Lọc tất cả các cung có điểm đầu nằm trong tập omega_in."""
        omega_in = self.pipeline.omega_in
        omega_edges = self.pipeline.omega_edges
        V = [edge for edge in omega_edges if edge.start_node.id in {n.id for n in omega_in}]
        return V

    def insert_artificial_nodes_and_edges(self, V, U):
        F = self.pipeline.max_flow_value
        for idx, edge in enumerate(V):
            u, v = edge.start_node.id, edge.end_node.id
            cost = edge.weight

            orig_edge = self.find_original_edge(u, v)
            lower = getattr(orig_edge, 'lower', self.DEFAULT_LOWER) if orig_edge else self.DEFAULT_LOWER
            upper = getattr(orig_edge, 'upper', self.DEFAULT_UPPER) if orig_edge else self.DEFAULT_UPPER

            node1, node2 = self.create_artificial_nodes(idx)

            self.add_artificial_edges(node1, node2, lower, upper, F, U)
            self.remove_and_replace_edge(u, v, node1, node2, lower, upper, cost)

    def run(self, U, gamma):
        self.add_artificial_source_sink_nodes()
        self.add_exit_edge_vs_to_vt(U, gamma)
        V = self.collect_omega_in_edges()
        self.insert_artificial_nodes_and_edges(V, U)