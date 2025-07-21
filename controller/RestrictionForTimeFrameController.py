from controller.NodeGenerator import ArtificialNode
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx
import config
import pdb

# Class ArtificalNode ở đây kế thừa abstract artificialNode trong NodeGenerator
class RestrictionArtificialNode(ArtificialNode):
    def __init__(self, id: int, label: Optional[str] = None):
        super().__init__(id, label)
        self.is_restriction_node = True
    def __repr__(self):
        return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"     
    
class RestrictionForTimeFrameController:
    def __init__(self, graph_processor):
        self.restriction_arcs: List[Tuple[List[List[int]], List[int], int, float, float, float]] = []
        self.M = graph_processor.M
        self.H = graph_processor.H
        self.graph_processor = graph_processor
        self.min_gamma = 200  # Ngưỡng tối thiểu cho gamma
        self.demands = {}  # Lưu demand cho các node ảo vS, vD
        self._omegas = []  # Lưu các edges trong các omega
        
    def get_omegas(self) -> List[Tuple[int, int, int, int, int]]:
        # Getter for omegas
        return self._omegas
    
    def set_omegas(self, omega: List[Tuple[int, int, int, int, int]]) -> None:
        # Setter for omega
        self._omegas = omegas

    def validate_restriction(self, restriction_arcs: List[List[int]], timeframe: List[int], U: int) -> bool:
        # Check if restriction is valid
        if not restriction_arcs or not timeframe or U < 0:
            print("Restriction không hợp lệ")
            return False
            
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("Time frame không hợp lệ")
            return False
            
        if not all(len(edge) == 2 for edge in restriction_arcs):
            print("Restriction Arcs format không hợp lệ")
            return False
            
        return True

    def calculate_default_gamma(self, TSG, priority=1.0, k=1, min_gamma=1):
        # Calculate default penalty gamma
        if not TSG:
            return self.min_gamma
        costs = [cost for (_, _, _, _, cost) in TSG if cost is not None]
        avg_cost = np.mean(costs) if costs else 10
        gamma = k * avg_cost * max(1.0, priority)
        return max(gamma, self.min_gamma)

    def _validate_restriction_input(self, timeframe: List[int], restriction_nodes: List[int], U: int) -> bool:
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("Time frame không hợp lệ")
            return False

        if len(restriction_nodes) % 2 != 0 or len(restriction_nodes) < 2:
            print("Restriction edge không hợp lệ")
            return False

        if U < 0:
            print("U không hợp lệ")
            return False

        return True
    
    def _process_restriction_arcs(self, restriction_nodes: List[int]) -> List[List[int]]:
        return [[restriction_nodes[j], restriction_nodes[j+1]] for j in range(0, len(restriction_nodes), 2)]

    def _store_restriction(self, restriction_arcs: List[List[int]], timeframe: List[int], U: int, priority: float, gamma: Optional[float], k: float) -> None:
        self.restriction_arcs.append((restriction_arcs, timeframe, U, priority, gamma, k))
    
    def _get_user_input_for_restriction(self, index: int) -> Optional[Tuple[List[int], List[int], int, float, Optional[float], float]]:
        try:
            timeframe = list(map(int, input(f"Nhập timeframe cho restriction thứ {index+1} (vd: 3 4): ").split()))
            restriction_nodes = list(map(int, input(f"    Nhập các đoạn đường áp dụng giới hạn trong time frame: {timeframe} (vd 3 4 5 6 là 2 đoạn nối [3,4] và [5,6]): ").split()))

            U = int(input(f"    Nhập số lượng AGV tối đa (U) cho restriction {index+1}: ") or config.numOfAGVs)
            if U < 0:
                print("U không hợp lệ, dùng mặc định U = config.numOfAGVs")
                U = config.numOfAGVs

            priority = float(input(f"    Nhập priority (>=0, mặc định 1) cho restriction {index+1}: ") or 1.0)
            if priority < 0:
                print("Priority không hợp lệ, dùng mặc định 1.0")
                priority = 1.0

            gamma_input = input(f"    Nhập gamma (phí phạt, để trống thì tự động tính): ")
            gamma = float(gamma_input) if gamma_input.strip() else None
            if gamma is not None and gamma < 1:
                print("Gamma quá nhỏ, dùng min_gamma = 1")
                gamma = 1.0

            k = float(input(f"    Nhập hệ số k (mặc định 2, k càng lớn thì cost vi phạm càng cao) cho gamma: ") or 2)
            if k < 0:
                k = 1

            return timeframe, restriction_nodes, U, priority, gamma, k
        except ValueError as e:
            print(f"Lỗi nhập liệu: {e}")
            return None
    
    def get_restrictions(self, use_config_data=False) -> bool:
        if not use_config_data:
            try:
                L = int(input("Nhập số restrictions (default 0): "))
                if L < 0:
                    L = 0
                for i in range(L):
                    user_input = self._get_user_input_for_restriction(i)
                    if not user_input:
                        continue
                    
                    timeframe, restriction_nodes, U, priority, gamma, k = user_input
                    self.graph_processor.gamma = gamma

                    if not self._validate_restriction_input(timeframe, restriction_nodes, U):
                        continue
                    
                    restriction_arcs = self._process_restriction_arcs(restriction_nodes)
                    self._store_restriction(restriction_arcs, timeframe, U, priority, gamma, k)

                return bool(self.restriction_arcs)

            except ValueError as e:
                L = 0
        else:
            # Handle config data case
            pass
        return True
    def set_restrictions(self, restrictions_data: List[Tuple[List[List[int]], List[int], int, float, float, float]]) -> bool:
        # Set restrictions from data, support priority and gamma
        self.restrictions = []
        for restriction_arcs, timeframe, U, priority, gamma, k in restrictions_data:
            if self.validate_restriction(restriction_arcs, timeframe, U):
                self.restriction_arcs.append((restriction_arcs, timeframe, U, priority, gamma, k))
        return bool(self.restriction_arcs)

    def restriction_parser(self, restriction: Tuple[List[List[int]], List[int], int, float, float, float]) -> Tuple[List[List[int]], int, int, int, float, float, float]:
        # Parse restriction tuple to components
        restriction_arcs, [start_time_frame, end_time_frame], U, priority, gamma, k = restriction
        return restriction_arcs, start_time_frame, end_time_frame, U, priority, gamma, k
    
    def _get_node_time(self, node_id: int) -> int:
        # Get time from node id
        return node_id // self.M - (1 if node_id % self.M == 0 else 0)
    
    def _get_node_coordinates(self, node_id: int) -> int:
        # Get spatial coordinate from node id
        return node_id % self.M if node_id % self.M != 0 else self.M
    
    def calculate_total_capacity(self, omega: List[Tuple[int, int, int, int, int]]) -> int:
        # Sum capacity of edges in omega
        return sum(capacity for (_, _, _, capacity, _) in omega)

    def calculate_virtual_flow(self, max_flow: int, U: int) -> int:
        # Calculate needed virtual flow
        return max(0, max_flow - U)

    #def extract_weakly_connected_subgraph(self, graph: List[Tuple[int, int, int, int, int]]) -> List[List[Tuple[int, int, int, int, int]]]:
    def extract_weakly_connected_subgraph(self, ts_edges):
        """Hàm này sẽ lấy các thành phần liên thông yếu trong đồ thị thời gian không gian."""
        # Get weakly connected subgraphs
        parent = {}
        
        def find(u: int) -> int:
            if parent[u] != u:
                parent[u] = find(parent[u])
            return parent[u]

        def union(u: int, v: int) -> None:
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv

        # Initialize parent for each node
        for e in ts_edges:
            u = e.start_node.id
            v = e.end_node.id
            # Ensure both nodes are in the parent map
            # If the node is not in parent, initialize it to itself
            if u not in parent:
                parent[u] = u
            if v not in parent:
                parent[v] = v
            union(u, v)

        # Group nodes by connected components
        components = defaultdict(list)
        for edge in ts_edges:
            root = find(edge.start_node.id)
            components[root].append(edge)

        return list(components.values())
    
    
    def identify_restricted_edges(self, restriction_arcs: List[List[int]], start_time_frame: int, end_time_frame: int) -> List[Tuple[int, int, int, int, int]]:
        # Find edges in restriction time
        omega = []
        pdb.set_trace()
        list_W = self.extract_weakly_connected_subgraph(self.graph_processor.ts_edges)
        restriction_set = {(u, v) for u, v in restriction_arcs}
        
        for W_edges in list_W:
            for edge in W_edges:
                source_id, dest_id, _, capacity, cost = edge.start_node.id, edge.end_node.id, edge.lower, edge.upper, edge.weight
                t1 = self._get_node_time(source_id)
                s_source = self._get_node_coordinates(source_id)
                t2 = self._get_node_time(dest_id)
                s_dest = self._get_node_coordinates(dest_id)
                base_edge = (s_source, s_dest)
                
                if base_edge in restriction_set:
                    if (t1 <= start_time_frame <= t2) or \
                       (t1 <= end_time_frame <= t2) or \
                       (start_time_frame <= t1 and t2 <= end_time_frame and t1 < t2):
                        omega.append(edge)
        pdb.set_trace()
        return omega

    def apply_restriction(self, use_config_data = False) -> None:
        # Apply all restrictions to the graph
        if not self.get_restrictions(use_config_data):
            pdb.set_trace()
            return
        
        pdb.set_trace()

        for restriction in self.restriction_arcs:
            restriction_arcs, start_time_frame, end_time_frame, U, priority, gamma, k = self.restriction_parser(restriction)
            omega = self.identify_restricted_edges(restriction_arcs, start_time_frame, end_time_frame)

            if not omega:
                print(f"Không tìm thấy cung nào trong restriction {restriction}")
                """#region Alert"""
                #dimacs_input, node_labels = self.make_dimacs_input(self.graph_processor.ts_edges, self.demands)
                """#endregion"""
                print("DIMACS input:")
                print(dimacs_input)
                print("Node labels:")
                print(node_labels)
                continue
            self._omegas.append(omega)
            
            pdb.set_trace()
            """#region Alert"""
            incoming_capacity = self.calculate_capacity_for_restricted_nodes(self.graph_processor.ts_edges, omega, direction = "incoming")
            outgoing_capacity = self.calculate_capacity_for_restricted_nodes(self.graph_processor.ts_edges, omega, direction = "outgoing")
            """#endregion"""
            
            max_flow = self.calculate_max_flow(omega, outgoing_capacity, incoming_capacity)
            virtual_flow = self.calculate_virtual_flow(max_flow, U)

            if virtual_flow < 0:
                print(f"Lỗi: U ({U}) không thể lớn hơn max flow ({max_flow})")
                continue
            elif virtual_flow == 0:
                print(f"Đã thoả mãn restriction {restriction}")
                continue

            # Calculate gamma if not set
            if gamma is None:
                gamma = self.calculate_default_gamma(self.graph_processor.ts_edges, priority=priority, k=k)
            gamma = int(round(gamma))

            # Create virtual nodes
            max_id = self.graph_processor.get_max_id() + 1
            vS_id, vD_id = max_id, max_id + 1
            vS = RestrictionArtificialNode(vS_id)
            vD = RestrictionArtificialNode(vD_id)

            # Add virtual nodes to graph
            self.graph_processor.check_and_add_nodes([vS_id, vD_id], is_artificial_node=True, label="Restriction")
            self.graph_processor.ts_nodes.append(vS)
            self.graph_processor.ts_nodes.append(vD)
            self.graph_processor.map_nodes.update({vS_id: vS, vD_id: vD})

            # Set demand for vS, vD
            self.demands[vS_id] = -virtual_flow
            self.demands[vD_id] = virtual_flow
            if hasattr(self.graph_processor, 'set_node_demand'):
                self.graph_processor.set_node_demand(vS_id, -virtual_flow)
                self.graph_processor.set_node_demand(vD_id, virtual_flow)
            else:
                print("Cảnh báo: graph_processor chưa hỗ trợ set_node_demand.")

            # Create virtual edges
            new_edges = set()
            for source_id, dest_id, _, capacity, _ in omega:
                new_edges.add((vS_id, source_id, 0, capacity, 0))
                new_edges.add((dest_id, vD_id, 0, capacity, 0))

            # Escape edge (vS, vD) has cost = gamma
            new_edges.add((vS_id, vD_id, 0, self.H, int(round(gamma))))

            # Update graph with new edges
            #self.graph_processor.ts_edges.extend(e for e in new_edges if e not in self.graph_processor.ts_edges)
            self.graph_processor.create_set_of_edges(new_edges)

        print("Đã áp dụng tất cả restrictions thành công")
        # print("Kiểm tra lại vi phạm restrictions")
        # self.check_restriction_violations_from_graph(self.graph_processor._graph)

    def make_dimacs_input(self, TSG: List[Tuple[int, int, int, int, int]], demands: Dict[int, int] = {}) -> Tuple[str, Dict[int, str]]:
        """
        Generates a DIMACS format string representing the Time-Space Graph (TSG).

        Args:
            TSG: A list of tuples, where each tuple represents an edge in the TSG
                 in the format (source_id, dest_id, lower_capacity, upper_capacity, cost).
            demands: A dictionary where keys are node IDs and values are their demands.
                     Positive demand indicates a sink, negative indicates a source,
                     and zero indicates a transshipment node.

        Returns:
            A tuple containing:
                - A string in DIMACS format representing the TSG.
                - A dictionary mapping node IDs to their labels (if available).
        """
        num_nodes = 0
        edges_data = []
        node_labels = {}

        # Find all unique nodes and their labels
        all_nodes = set()
        for u, v, _, _, _ in TSG:
            all_nodes.add(u)
            all_nodes.add(v)
            if u in self.graph_processor.map_nodes:
                node_labels[u] = str(self.graph_processor.map_nodes[u].label)
            else:
                node_labels[u] = str(u)
            if v in self.graph_processor.map_nodes:
                node_labels[v] = str(self.graph_processor.map_nodes[v].label)
            else:
                node_labels[v] = str(v)

        num_nodes = len(all_nodes)
        indexed_nodes = {node: i + 1 for i, node in enumerate(sorted(list(all_nodes)))}
        reverse_indexed_nodes = {i + 1: node for node, i in indexed_nodes.items()}

        # Prepare edges in DIMACS format
        for u, v, lower, upper, cost in TSG:
            u_index = indexed_nodes[u]
            v_index = indexed_nodes[v]
            edges_data.append(f"a {u_index} {v_index} {lower} {upper} {cost}")

        # Prepare demand in DIMACS format
        demand_data = []
        for node, demand in demands.items():
            if node in indexed_nodes:
                node_index = indexed_nodes[node]
                demand_data.append(f"n {node_index} {demand}")

        # Construct the DIMACS string
        dimacs_str = f"p min {num_nodes} {len(edges_data)}\n"
        dimacs_str += "\n".join(demand_data) + "\n" if demand_data else ""
        dimacs_str += "\n".join(edges_data) + "\n"

        # Create a mapping from DIMACS internal node IDs to original node labels
        dimacs_node_labels = {i: node_labels.get(reverse_indexed_nodes[i], str(reverse_indexed_nodes[i])) for i in range(1, num_nodes + 1)}

        return dimacs_str, dimacs_node_labels

    def check_restriction_violations_from_graph(self, G, file_path='TSG.txt'):
        violations = []
        restriction_edges = []
        for u, v, data in G.edges(data=True):
            if data.get('is_restriction', False):
                U = data.get('capacity', 0)
                restriction_edges.append((u, v, U))
        # Chạy network simplex
        flowCost, flowDict = nx.network_simplex(G)
        # Kiểm tra vi phạm
        for source, dest, U in restriction_edges:
            flow = 0
            if str(source) in flowDict and str(dest) in flowDict[str(source)]:
                flow = flowDict[str(source)][str(dest)]
            if flow > U:
                n = flow - U
                print(f"Edge {source} {dest} violates {n} times (flow={flow}, U={U})")
                violations.append((source, dest, n))
        # Ghi ra file
        with open(file_path, 'w') as f:
            for source, dest, n in violations:
                f.write(f"c Edge {source} {dest} violates {n} times\n")
    
    
    def identify_restricted_nodes(self, omega: List[Tuple[int, int, int, int, int]]) -> set:
        # Identify restricted nodes in omega
        restricted_nodes = set()
        for source_id, dest_id, _, _, _ in omega:
            restricted_nodes.add(source_id)
            restricted_nodes.add(dest_id)
        return restricted_nodes
    
    
    def calculate_capacity_for_restricted_nodes(self, ts_edges, omega, direction: str) -> defaultdict:
        """
        Calculate the capacity for restricted nodes based on the direction (incoming or outgoing).
        Args:
            TSG: List of edges in the format (source_id, dest_id, lower_capacity, upper_capacity, cost).
            restricted_nodes: Set of restricted nodes.
            direction: "incoming" or "outgoing" to specify the direction of capacity calculation.
        Returns:
            A defaultdict containing the capacity for each restricted node.
        """
        capacity = defaultdict(int)
        #pdb.set_trace()
        # Trích ID các node bị hạn chế
        restricted_node_ids = set()
        for edge in omega:
            restricted_node_ids.add(edge.start_node.id)
            restricted_node_ids.add(edge.end_node.id)
        for e in ts_edges:
            source_id, dest_id, cap = e.start_node.id, e.end_node.id, e.upper
            if direction == "incoming" and dest_id in restricted_node_ids and source_id not in restricted_node_ids:
                capacity[dest_id] += cap
            elif direction == "outgoing" and source_id in restricted_node_ids and dest_id not in restricted_node_ids:
                capacity[source_id] += cap
        return capacity    
    
    def calculate_max_flow(self , omega , restricted_nodes_incoming_capacity , restricted_nodes_outgoing_capacity) -> int:
        # Calculate max flow F
        
        # Build graph
        G = nx.DiGraph()
        G.add_node("vS")
        G.add_node("vT")
        for e in omega:
            source_id, dest_id, capacity = e.start_node.id, e.end_node.id, e.upper
            G.add_edge(source_id, dest_id, capacity=capacity)
            
        # Add incoming edges for restricted nodes
        for node_id, capacity in restricted_nodes_incoming_capacity.items():
            G.add_edge("vS", node_id , capacity=capacity)
        
        # Add outgoing edges for restricted nodes
        for node_id, capacity in restricted_nodes_outgoing_capacity.items():
            G.add_edge(node_id, "vT", capacity=capacity)
                        
        return nx.maximum_flow_value(G, "vS", "vT")
