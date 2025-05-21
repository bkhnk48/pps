from controller.NodeGenerator import ArtificialNode
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx

class RestrictionForTimeFrameController:
    def __init__(self, graph_processor):
        self.restrictions: List[Tuple[List[List[int]], List[int], int, float, float, float]] = []
        self.M = graph_processor.M
        self.H = graph_processor.H
        self.graph_processor = graph_processor
        self.min_gamma = 200  # Ngưỡng tối thiểu cho gamma
        self.demands = {}  # Lưu demand cho các node ảo vS, vD
        
    
    # Class ArtificalNode ở đây kế thừa abstract artificialNode trong NodeGenerator
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id: int, label: Optional[str] = None):
            super().__init__(id, label)
            self.is_restriction_node = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"     

    def validate_restriction(self, restriction_edges: List[List[int]], timeframe: List[int], U: int) -> bool:
        # Check if restriction is valid
        if not restriction_edges or not timeframe or U < 0:
            print("Restriction không hợp lệ")
            return False
            
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("Time frame không hợp lệ")
            return False
            
        if not all(len(edge) == 2 for edge in restriction_edges):
            print("Restriction edges format không hợp lệ")
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

    def get_restrictions(self) -> bool:
        # Get restrictions from user input, support priority and gamma
        try:
            L = int(input("Nhập số restrictions: "))
            if L < 0:
                print("Số restrictions phải lớn hơn hoặc bằng 0")
                return False

            for i in range(L):
                timeframe = list(map(int, input(f"Nhập timeframe cho restriction thứ {i+1} (vd: 3 4): ").split()))
                restriction_nodes = list(map(int, input(f"    Nhập các edges cho timeframe {timeframe} (vd 3 4 5 6 là 2 edge [3,4] và [5,6]): ").split()))

                try:
                    U = int(input(f"    Nhập số lượng AGV tối đa (U) cho restriction {i+1}: "))
                except ValueError:
                    print("U không hợp lệ")
                    continue

                if len(restriction_nodes) % 2 != 0 or len(restriction_nodes) < 2:
                    print("Restriction edge không hợp lệ")
                    continue

                restriction_edges = [[restriction_nodes[j], restriction_nodes[j+1]] for j in range(0, len(restriction_nodes), 2)]

                # Nhập priority
                try:
                    priority = float(input(f"    Nhập priority (>=0, mặc định 1) cho restriction {i+1}: ") or 1.0)
                    if priority < 0:
                        print("Priority không hợp lệ, dùng mặc định 1.0")
                        priority = 1.0
                except ValueError:
                    print("Priority không hợp lệ, dùng mặc định 1.0")
                    priority = 1.0

                # Nhập gamma hoặc để tự động
                gamma_input = input(f"    Nhập gamma (phí phạt, để trống thì tự động tính): ")
                gamma = None
                if gamma_input.strip():
                    try:
                        gamma = float(gamma_input)
                        if gamma < 1:
                            print("Gamma quá nhỏ, dùng min_gamma = 1")
                            gamma = 1.0
                    except ValueError:
                        print("Gamma không hợp lệ, sẽ tự động tính.")
                        gamma = None

                # Nhập hệ số k nếu muốn
                try:
                    k = float(input(f"    Nhập hệ số k (mặc định 2, k càng lớn thì cost vi phạm càng cao) cho gamma: ") or 2)
                except ValueError:
                    k = 2

                if self.validate_restriction(restriction_edges, timeframe, U):
                    # Lưu cả priority, gamma, k vào restriction
                    self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k))

            return bool(self.restrictions)

        except ValueError as e:
            print(f"Input error: {str(e)}")
            return False

    def set_restrictions(self, restrictions_data: List[Tuple[List[List[int]], List[int], int, float, float, float]]) -> bool:
        # Set restrictions from data, support priority and gamma
        self.restrictions = []
        for restriction_edges, timeframe, U, priority, gamma, k in restrictions_data:
            if self.validate_restriction(restriction_edges, timeframe, U):
                self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k))
        return bool(self.restrictions)

    def restriction_parser(self, restriction: Tuple[List[List[int]], List[int], int, float, float, float]) -> Tuple[List[List[int]], int, int, int, float, float, float]:
        # Parse restriction tuple to components
        restriction_edges, [start_time_frame, end_time_frame], U, priority, gamma, k = restriction
        return restriction_edges, start_time_frame, end_time_frame, U, priority, gamma, k
    
    def _get_node_time(self, node_id: int) -> int:
        # Get time from node id
        return node_id // self.M - (1 if node_id % self.M == 0 else 0)
    
    def _get_node_coordinates(self, node_id: int) -> int:
        # Get spatial coordinate from node id
        return node_id % self.M if node_id % self.M != 0 else self.M
    
    def calculate_total_capacity(self, omega: List[Tuple[int, int, int, int, int]]) -> int:
        # Sum capacity of edges in omega
        return sum(capacity for (_, _, _, capacity, _) in omega)

    def calculate_virtual_flow(self, total_capacity: int, U: int) -> int:
        # Calculate needed virtual flow
        return max(0, total_capacity - U)

    def extract_weakly_connected_subgraph(self, graph: List[Tuple[int, int, int, int, int]]) -> List[List[Tuple[int, int, int, int, int]]]:
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
        for u, v, _, _, _ in graph:
            if u not in parent:
                parent[u] = u
            if v not in parent:
                parent[v] = v
            union(u, v)

        # Group nodes by connected components
        components = defaultdict(list)
        for edge in graph:
            root = find(edge[0])
            components[root].append(edge)

        return list(components.values())
    
    
    def identify_restricted_edges(self, restriction_edges: List[List[int]], start_time_frame: int, end_time_frame: int) -> List[Tuple[int, int, int, int, int]]:
        # Find edges in restriction time
        omega = []
        list_W = self.extract_weakly_connected_subgraph(self.graph_processor.ts_edges)
        restriction_set = {(u, v) for u, v in restriction_edges}
        
        for W_edges in list_W:
            for edge in W_edges:
                source_id, dest_id, _, capacity, cost = edge
                t1 = self._get_node_time(source_id)
                s_source = self._get_node_coordinates(source_id)
                t2 = self._get_node_time(dest_id)
                s_dest = self._get_node_coordinates(dest_id)
                base_edge = (s_source, s_dest)
                
                if base_edge in restriction_set:
                    if (t1 <= start_time_frame <= t2) or \
                       (t1 <= end_time_frame <= t2) or \
                       (start_time_frame <= t1 and t2 <= end_time_frame):
                        omega.append((source_id, dest_id, 0, capacity, cost))
                        
        return omega

    def apply_restriction(self) -> None:
        # Apply all restrictions to the graph
        if not self.get_restrictions():
            return

        for restriction in self.restrictions:
            restriction_edges, start_time_frame, end_time_frame, U, priority, gamma, k = self.restriction_parser(restriction)
            omega = self.identify_restricted_edges(restriction_edges, start_time_frame, end_time_frame)

            if not omega:
                print(f"Không tìm thấy cung nào trong restriction {restriction}")
                continue

            total_capacity = self.calculate_total_capacity(omega)
            virtual_flow = self.calculate_virtual_flow(total_capacity, U)

            if virtual_flow < 0:
                print(f"Lỗi: U ({U}) không thể lớn hơn capacity ({total_capacity})")
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
            vS = self.RestrictionArtificialNode(vS_id)
            vD = self.RestrictionArtificialNode(vD_id)

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
            self.graph_processor.ts_edges.extend(e for e in new_edges if e not in self.graph_processor.ts_edges)
            self.graph_processor.create_set_of_edges(new_edges)

        print("Đã áp dụng tất cả restrictions thành công")
        # print("Kiểm tra lại vi phạm restrictions")
        # self.check_restriction_violations_from_graph(self.graph_processor._graph)

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
    
    
    def indentify_restricted_nodes(self, omega: List[Tuple[int, int, int, int, int]]) -> set:
        # Identify restricted nodes in omega
        restricted_nodes = set()
        for source_id, dest_id, _, _, _ in omega:
            restricted_nodes.add(source_id)
            restricted_nodes.add(dest_id)
        return restricted_nodes
    
    
    def calculate_incoming_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]] , restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges come from nodes not in omega and their capacities
        restricted_nodes_incoming_capacity = defaultdict(int)
        for source_id, dest_id, _, capacity, _ in TSG:
            if dest_id in restricted_nodes  and source_id not in restricted_nodes:
                restricted_nodes_incoming_capacity[dest_id] += capacity
        return restricted_nodes_incoming_capacity
    
    def calculate_outgoing_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]], restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges go to nodes not in omega and their capacities
        restricted_nodes_outgoing_capacity = defaultdict(int)
        for source_id, dest_id, _, capacity, _ in TSG:
            if source_id in restricted_nodes and dest_id not in restricted_nodes:
                restricted_nodes_outgoing_capacity[source_id] += capacity
                
        return restricted_nodes_outgoing_capacity
    
    
    def calulate_max_flow(self , omega: List[Tuple[int, int, int, int, int]] , restricted_nodes_incoming_capacity , restricted_nodes_outgoing_capacity) -> int:
        # Calculate max flow F
        
        # Build graph
        G = nx.DiGraph()
        for source_id, dest_id, _, capacity, _ in omega:
            G.add_edge(source_id, dest_id, capacity=capacity)
            
        # Add incoming edges for restricted nodes
        for node_id, capacity in restricted_nodes_incoming_capacity.items():
            G.add_edge("vS", node_id , capacity=capacity)
        
        # Add outgoing edges for restricted nodes
        for node_id, capacity in restricted_nodes_outgoing_capacity.items():
            G.add_edge(node_id, "vT", capacity=capacity)
                        
        return nx.maximum_flow_value(G, "vS", "vT")