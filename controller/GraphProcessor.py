import os
import re
import json
from controller.NodeGenerator import TimeoutNode
from controller.NodeGenerator import ArtificialNode
from controller.NodeGenerator import RestrictionNode
from controller.NodeGenerator import TimeWindowNode
from controller.NodeGenerator import NodeGenerator
from controller.RestrictionController import RestrictionController
from controller.restriction_time_frame_controller import RestrictionForTimeFrameController
from controller.restriction_integrator_tqm import RestrictionIntegratorTQM
from controller.time_window_generator import TimeWindowGenerator
from controller.kick_off_generator import KickOffGenerator
from controller.time_determinator import TimeDeterminator
from model.Node import Node
from model.hallway_simulator_module.HallwaySimulator import BulkHallwaySimulator
from collections import deque
from scipy.sparse import lil_matrix
import config
import pdb

""" Mô tả yêu cầu của code:
https://docs.google.com/document/d/13S_Ycg-aB4GjEm8xe6tAoUHzhS-Z1iFnM4jX_bWFddo/edit?usp=sharing """

class GraphProcessor(KickOffGenerator):
    def __init__(self, dm):
        super().__init__(dm) 
        self._adj = []  # Adjacency matrix
        #self._tsedges = []
        self._restriction_controller = None
        #self._restriction_for_timeframe_controller = None
        self._start_ban = -1
        self._end_ban = -1
        self._time_determinator = TimeDeterminator(self)
        # Initialize an empty list to store the processed numbers

#===============================================================================

    # Getter và Setter cho restriction_for_timeframe_controller
    #@property
    #def restriction_for_timeframe_controller(self):
    #    return self._restriction_for_timeframe_controller
    
    #@restriction_for_timeframe_controller.setter
    #def restriction_for_timeframe_controller(self, value):
    #    self._restriction_for_timeframe_controller = value
        
    # Getter and Setter for adj
    @property
    def adj(self):
        return self._adj

    @adj.setter
    def adj(self, value):
        self._adj = value

    # Getter và Setter cho restriction_controller
    @property
    def restriction_controller(self):
        return self._restriction_controller

    @restriction_controller.setter
    def restriction_controller(self, value):
        self._restriction_controller = value

    # Getter và Setter cho start_ban
    @property
    def start_ban(self):
        return self._start_ban

    @start_ban.setter
    def start_ban(self, value):
        if not isinstance(value, int):
            raise ValueError("start_ban must be an integer")
        self._start_ban = value

    # Getter và Setter cho end_ban
    @property
    def end_ban(self):
        return self._end_ban

    @end_ban.setter
    def end_ban(self, value):
        if not isinstance(value, int):
            raise ValueError("end_ban must be an integer")
        self._end_ban = value
        

#======================================================================================

    def getReal(self, start_id, next_id, agv):
        result = self._time_determinator.getReal(start_id, next_id, agv)
        return result
    
    def getReal_preprocess(self, Map_file, function_file):
        # read files
        map_data = None
        function_data = None
        with open(Map_file, 'r', encoding='utf-8') as file:
            map_data = file.readlines()
        with open(function_file, 'r', encoding='utf-8') as file:
            function_data = file.readlines()
        hallways_list = []
        functions_list = []
        for line in map_data:
            line = line.strip()
            parts = line.split(" ")
            if len(parts) == 8:
                hallway = {
                    "hallway_id": parts[6],
                    "length": int(int(parts[5]) * 0.6),
                    "width": 4,
                    "agents_distribution": int(parts[7]),
                    "src": int(parts[1]),
                    "dest": int(parts[2])
                }
                hallways_list.append(hallway)
        for line in function_data:
            line = line.strip()
            functions_list.append(line)
        return hallways_list, functions_list

    def getAGVRuntime(self, Map_file, function_file, start_id, next_id, agv, current_time):
        hallways_list, functions_list = self.getReal_preprocess(Map_file, function_file)
        agv_id = self._extract_agv_id(agv)
        direction, hallway_id = self._get_hallway_direction(hallways_list, start_id, next_id)
        
        if hallway_id is None:
            print(f"{bcolors.WARNING}Hallway not found!{bcolors.ENDC}")
            return -1

        events_list = self._create_event_list(agv_id, direction, current_time, hallway_id)
        hallways_list = self._filter_hallways_list(hallways_list, hallway_id, direction)
        
        return self._simulate_bulk_runtime(agv_id, hallway_id, hallways_list, functions_list, events_list)

    def _extract_agv_id(self, agv):
        return int(agv.id[3:])

    def _get_hallway_direction(self, hallways_list, start_id, next_id):
        for hallway in hallways_list:
            if hallway["src"] == start_id and hallway["dest"] == next_id:
                return 1, hallway["hallway_id"]
            elif hallway["src"] == next_id and hallway["dest"] == start_id:
                return 0, hallway["hallway_id"]
        return 0, None

    def _create_event_list(self, agv_id, direction, time_stamp, hallway_id):
        event = {
            "AgvIDs": [agv_id],
            "AgvDirections": [direction],
            "time_stamp": int(time_stamp),
            "hallway_id": hallway_id
        }
        return [event]

    def _filter_hallways_list(self, hallways_list, hallway_id, direction):
        return [
            hallway for hallway in hallways_list
            if hallway["hallway_id"] == hallway_id and (hallway["src"] - hallway["dest"]) * direction > 0
        ]

    def _simulate_bulk_runtime(self, agv_id, hallway_id, hallways_list, functions_list, events_list):
        bulk_sim = BulkHallwaySimulator("test", 3600, hallways_list, functions_list, events_list)
        result = bulk_sim.run_simulation()
        completion_time = result[agv_id][hallway_id]["completion_time"]
        print(f"{bcolors.OKGREEN}AGV {agv_id} has runtime {completion_time} in hallway {hallway_id}.{bcolors.ENDC}")
        return completion_time
    
    def update(self,currentpos,nextpos,realtime):
        list = utility()
        del self.matrix[currentpos,nextpos]
        q = deque()
        q.append(nextpos)
        while q:
            pos = q[0]
            q.pop()
            for i in list.findid(pos):
                if (pos,i) in self.matrix:
                    del self.matrix[pos,i]
                    q.append(i)
        nextpos = list.M*(int(currentpos/list.M)+ realtime) + list.getid(nextpos)
        self.matrix[currentpos,nextpos] = realtime
        q.append(nextpos)
        while q:
            pos = q[0]
            q.pop()
            for i in list.findid(pos):
                if (pos,i) not in self.matrix:
                    self.matrix[pos,i] = int((pos-i)/list.M)
                    q.append(i)
    
    def update_graph(self, id1=-1, id2=-1, end_id=-1, agv_id=None):
        """Cập nhật đồ thị với thông tin cạnh mới."""
        ID1, ID2, endid = self.get_ids(id1, id2, end_id)
        M = self.graph.number_of_nodes_in_space_graph
        current_time, new_node_id = self.calculate_times(ID1, ID2, endid, M)

        self.process_adjacency_list(current_time, new_node_id, M)
        
        q = self.update_new_started_nodes(new_node_id)
        new_edges = self.insert_from_queue(q, self.graph.adjacency_list)
        self.process_new_edges(new_edges)

        if self.version_check(current_time):
            self.graph.version += 1

        new_halting_edges = self.collect_new_halting_edges()
        self.write_to_file([agv_id, new_node_id], new_halting_edges)
        #pdb.set_trace()                
    
    def process_adjacency_list(self, current_time, new_node_id, M):
        """Duyệt qua từng phần tử của adjacency_list và cập nhật thông tin."""
        for source_id, edges in list(self.graph.adjacency_list.items()):
            isContinued = any(node.id == source_id for node in self.target_nodes)
            if isContinued:
                continue

            if source_id in self.graph.nodes:
                node = self.graph.nodes[source_id]
                time = source_id // M - (1 if source_id % M == 0 else 0)
                if time < current_time and not isinstance(node, (TimeWindowNode, RestrictionNode)):
                    self.update_nodes(source_id, current_time, M)
    
    def update_nodes(self, source_id, current_time, M):
        """Cập nhật thông tin nút và xóa khỏi danh sách."""
        del self.graph.adjacency_list[source_id]
        if self.graph.nodes[source_id].agv is not None:
            space_id = M if (source_id % M == 0) else source_id % M
            new_source_id = current_time * M + space_id
            self.transfer_agv(source_id, new_source_id)
        del self.graph.nodes[source_id]
    
    def transfer_agv(self, source_id, new_source_id):
        """Chuyển AGV từ nút cũ sang nút mới."""
        try:
            if new_source_id in self.graph.nodes:
                self.graph.nodes[new_source_id].agv = self.graph.nodes[source_id].agv
            index = self.started_nodes.index(source_id)
            self.started_nodes[index] = new_source_id
        except ValueError:
            pass
        
    def get_ids(self, id1, id2, end_id):
        """Nhận ID từ người dùng hoặc sử dụng giá trị mặc định."""
        ID1 = int(input("Nhap ID1: ")) if id1 == -1 else id1
        ID2 = int(input("Nhap ID2: ")) if id2 == -1 else id2
        endid = int(input("Nhap ID thực sự khi AGV kết thúc hành trình: ")) if end_id == -1 else end_id
        return ID1, ID2, endid

    def calculate_times(self, ID1, ID2, endid, M):
        """Tính thời gian và ID nút mới."""
        time2 = ID1 // M - (1 if ID1 % M == 0 else 0)
        current_time = endid // M - (1 if endid % M == 0 else 0)
        new_node_id = current_time * M + (M if ID2 % M == 0 else ID2 % M)
        return current_time, new_node_id

    def update_new_started_nodes(self, new_node_id):
        """Cập nhật danh sách các nút mới bắt đầu và trả về hàng đợi."""
        q = deque([new_node_id])
        new_started_nodes = self.graph.getAllNewStartedNodes()
        for start in new_started_nodes:
            if start != new_node_id:
                q.append(start)
        return q

    def process_new_edges(self, new_edges):
        """Xử lý và cập nhật các cạnh mới vào đồ thị."""
        for edge in new_edges:
            #if edge == "a 599 1239 0 1 10": #or edge == "a 792 1432 0 1 10":#liệu đây có làm arr bị None???
            #    pdb.set_trace()
            arr = self.graph.parse_string(edge)
            if arr is not None:
                if arr[0] is None:
                    pdb.set_trace()
            else:
                pdb.set_trace()            
            source_id, dest_id = arr[0], arr[1]
            self.add_edge_to_graph(source_id, dest_id, arr)

    def add_edge_to_graph(self, source_id, dest_id, arr):
        """Thêm một cạnh mới vào đồ thị."""
        if source_id not in self.graph.nodes:
            self.graph.nodes[source_id] = self.find_node(source_id)
        if dest_id not in self.graph.nodes:
            self.graph.nodes[dest_id] = self.find_node(dest_id)

        if source_id not in self.graph.adjacency_list:
            self.graph.adjacency_list[source_id] = []
        
        found = any(end_id == dest_id for end_id, _ in self.graph.adjacency_list[source_id])
        if not found:
            anEdge = self.graph.nodes[source_id].create_edge(self.graph.nodes[dest_id], self.M, self.d, [source_id, dest_id, arr[2], arr[3], arr[4]])
            self.graph.adjacency_list[source_id].append([dest_id, anEdge])
        
        # Add TimeWindowEdge and RestrictionEdge
        self.time_window_controller.generate_time_window_edges(self.graph.nodes[source_id], self.graph.adjacency_list, self.graph.number_of_nodes_in_space_graph)
        self.restriction_controller.generate_restriction_edges(self.graph.nodes[source_id], self.graph.nodes[dest_id], self.graph.nodes, self.graph.adjacency_list)


    def collect_new_halting_edges(self):
        """Thu thập các cạnh dừng mới cần được thêm vào."""
        sorted_edges = sorted(self.graph.adjacency_list.items(), key=lambda x: x[0])
        new_nodes = set()
        new_halting_edges = []

        for source_id, edges in sorted_edges:
            for edge in edges:
                t = edge[0] // self.M - (1 if edge[0] % self.M == 0 else 0)
                if t >= self.H and edge[0] not in new_nodes and isinstance(self.graph.nodes[edge[0]], TimeoutNode):
                    new_nodes.add(edge[0])
                    for target in self.get_targets():
                        dest_id = target.id
                        new_halting_edges.append([edge[0], dest_id, 0, 1, self.H * self.H])

        return new_halting_edges
    
    def reset_agv(self, real_node_id, agv):
        for node_id in self.graph.nodes.keys():
            if(node_id != real_node_id):
                if self.graph.nodes[node_id].agv == agv:
                    self.graph.nodes[node_id].agv = None
        self.graph.nodes[real_node_id].agv = agv
    
    def remove_node_and_origins(self, node_id):
        node = None
        if isinstance(node_id, Node):
            node = node_id
        elif node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
        else:
            return
        node = node_id if isinstance(node_id, Node) else self.graph.nodes[node_id]
        R = [node]  # Khởi tạo danh sách R với nút cần xóa
        while R:  # Tiếp tục cho đến khi R rỗng
            current_node = R.pop()  # Lấy ra nút cuối cùng từ R
            if current_node.id in self.graph.nodes:  # Kiểm tra xem nút có tồn tại trong đồ thị hay không
                del self.graph.nodes[current_node.id]  # Nếu có, xóa nút khỏi danh sách các nút
            for id in self.graph.adjacency_list:
                edges = []
                found = False
                for end_id, edge in self.graph.adjacency_list[id]:
                    if(end_id == node.id):
                        #del self.adjacency_list
                        found = True
                    else:
                        edges.append([end_id, edge])
                if(found):
                    self.graph.adjacency_list[id] = edges
            
    def remove_edge(self, start_node, end_node, agv_id):
        if (start_node, end_node) in self.graph.edges:
            del self.graph.edges[(start_node, end_node)]
            self.graph.lastChangedByAGV = agv_id  # Update the last modified by AGV

    def handle_edge_modifications(self, start_node, end_node, agv):
        # Example logic to adjust the weights of adjacent edges
        print(f"Handling modifications for edges connected to {start_node} and {end_node}.")
        #pdb.set_trace()
        adjacent_nodes_with_weights = self.graph.adjacency_list.get(end_node, [])
        # Check adjacent nodes and update as necessary
        for adj_node, weight in adjacent_nodes_with_weights:
            if (end_node, adj_node) not in self.graph.lastChangedByAGV or self.graph.lastChangedByAGV[(end_node, adj_node)] != agv.id:
                # For example, increase weight by 10% as a traffic delay simulation
                new_weight = int(weight * 1.1)
                self.graph.adjacency_list[end_node][adj_node] = new_weight
                print(f"Updated weight of edge {end_node} to {adj_node} to {new_weight} due to changes at {start_node}.")
	
    def generate_hm_matrix(self):
        self.matrix = [[j + 1 + self.M * i for j in range(self.M)] for i in range(self.H)]
        if(self.print_out):
            print("Hoan tat khoi tao matrix HM!")
        #     print(' '.join(map(str, row)))

    def generate_adj_matrix(self):
        size = (self.H + 1) * self.M + 1
        self.adj = lil_matrix((2*size, 2*size), dtype=int)

        for edge in self.space_edges:
            if len(edge) >= 6 and edge[3] == '0' and int(edge[4]) >= 1:
                u, v, c = int(edge[1]), int(edge[2]), int(edge[5])
                for i in range(self.H + 1):
                    source_idx = i * self.M + u
                    target_idx = (i + c) * self.M + v
                    if(self.print_out):
                        print(f"i = {i} {source_idx} {target_idx} = 1")

                    if source_idx < size and (target_idx < size or (size <= target_idx < 2*size)):
                        self.adj[source_idx, target_idx] = 1
                        
        for i in range(size):
            j = i + self.M * self.d
            if j < size and (i % self.M == j % self.M):
                self.adj[i, j] = 1

        if(self.print_out):
            print("Hoan tat khoi tao Adjacency matrix!")

        rows, cols = self.adj.nonzero()
        with open('adj_matrix.txt', 'w') as file:
            for i, j in zip(rows, cols):
                file.write(f"({i}, {j})\n")
        if(self.print_out):
            print("Cac cap chi so (i,j) khac 0 cua Adjacency matrix duoc luu tai adj_matrix.txt.")

    def check_and_add_nodes(self, args, is_artificial_node = False, label = ""):
        if not hasattr(self, 'map_nodes'):
            # Nếu chưa tồn tại, chuyển self.ts_nodes thành self.map_nodes
            self.map_nodes = {node.id: node for node in self.ts_nodes}
        for id in args:
            # Ensure that Node objects for id exist in ts_nodes
            if not any(node.id == id for node in self.ts_nodes) and isinstance(id, int):
                NodeGenerator.generate_node(is_artificial_node, id, label, self)
        #    self.ts_nodes.append(Node(ID2))

    def get_node_coordinates(self, ID, j):
        """Lấy tọa độ nút từ ID."""
        u = ID % self.M if ID % self.M != 0 or ID == 0 else self.M
        v = j % self.M if j % self.M != 0 or j == 0 else self.M
        return u, v

    def create_tsg_file(self):          
        #pdb.set_trace()
        q = deque()
        q.extend(self.started_nodes)

        #pdb.set_trace()
        output_lines = self.insert_from_queue(q)
        with open('TSG.txt', 'w') as file:
            for line in output_lines:
                file.write(line + "\n")
        if(self.print_out):
            print("TSG.txt file created.")
    
    def query_edges_by_source_id(self):
        source_id = int(input("Nhap vao ID nguon: "))

        edges = []
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and int(parts[1]) == source_id:
                        edges.append(line.strip())
        except FileNotFoundError:
            if(self.print_out):
                print("File TSG.txt khong ton tai!")
            return

        if edges:
            if(self.print_out):
                print(f"Cac canh co ID nguon la {source_id}:")
            for edge in edges:
                print(edge)
        else:
            if(self.print_out):
                print(f"Khong tim thay canh nao co ID nguon la {source_id}.")

    def get_input_id(self, default_id, prompt):
        """Lấy ID từ người dùng hoặc sử dụng giá trị mặc định."""
        return int(input(prompt)) if default_id == -1 else default_id

    def get_input_weight(self, default_weight):
        """Lấy trọng số từ người dùng hoặc sử dụng giá trị mặc định."""
        return int(input("Nhap trong so C12: ")) if default_weight == -1 else default_weight

    def adjust_id2_if_needed(self, ID1, ID2, C12):
        """Điều chỉnh ID2 nếu i2 - i1 không bằng C12."""
        i1, i2 = ID1 // self.M, ID2 // self.M
        if i2 - i1 != C12:
            print('Status: i2 - i1 != C12')
            ID2 = ID1 + self.M * C12
        return ID2

    def load_existing_edges(self):
        """Tải các cạnh đã tồn tại từ file TSG.txt."""
        existing_edges = set()
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                        existing_edges.add((int(parts[1]), int(parts[2])))
        except FileNotFoundError:
            print("File TSG.txt khong ton tai!")
            return existing_edges
        return existing_edges


    def process_restrictions(self, use_config_data = False):
        """Xử lý các hạn chế trong đồ thị."""
        #pdb.set_trace()
        #if self.restriction_for_timeframe_controller is None:
        #    self.restriction_for_timeframe_controller = RestrictionForTimeFrameController(self)
            #self.restriction_for_timeframe_controller.apply_restriction(use_config_data)
        if self.restriction_controller is None:
            self.restriction_controller = RestrictionIntegratorTQM(self)
    
        self.insert_halting_edges()
        F = self.restriction_controller.compute_max_flow(use_config_data)
        self.restriction_controller.insert_artificial_objects(F, use_config_data=use_config_data)
        
        # Ghi file TSG.txt
        U = config.artificial_upper_bound
        if  F > U:
            vs_id = next((n.id for n in self.graph.nodes.values() if getattr(n, "label", "") == "vS"), None)
            vt_id = next((n.id for n in self.graph.nodes.values() if getattr(n, "label", "") == "vT"), None)
            self.write_to_file(supply=U, vs_id=vs_id, vt_id=vt_id)
        else:
            self.write_to_file()

    def get_edges_with_cost(self):
        """Trả về một từ điển các cạnh với chi phí."""
        return {(int(edge[1]), int(edge[2])): int(edge[5])
                for edge in self.space_edges if edge[3] == '0' and int(edge[4]) >= 1}
    
    def remove_edge_by_id(self, u, v):
        """Xóa cạnh từ ts_edges dựa trên id hai đầu mút."""
        self.ts_edges = [e for e in self.ts_edges
            if not (getattr(e, 'start_node', None) and getattr(e, 'end_node', None) and e.start_node.id == u and e.end_node.id == v)
        ]   
        return True

    def create_restricted_edges(self, restriction, edges_with_cost, maxid):
        """Tạo các cạnh bị cấm dựa trên hạn chế và chi phí."""
        R = []
        for time in range(self.start_ban, self.end_ban + 1):
            time_space_point_0 = time * self.M + restriction[0]
            cost = edges_with_cost.get((restriction[0], restriction[1]), -1)
            time_space_point_1 = (time + cost) * self.M + restriction[1]
            
            R.append([time_space_point_0, time_space_point_1, cost])
            self.adj[time_space_point_0, time_space_point_1] = 0

        self.update_edges_after_restrictions(R)
        return R
    
    def remove_artificial_nodes_and_edges(self):
        """Xóa toàn bộ node/cung ảo và reset trạng thái pipeline, restriction_controller."""
        artificial_types = {"ArtificialNode", "RestrictionNode"}
        artificial_edge_types = {"ArtificialEdge", "RestrictionEdge"}

        def not_artificial(obj, types):
            return getattr(obj, "__class__", type("")).__name__ not in types

        self.ts_nodes = [n for n in self.ts_nodes if not_artificial(n, artificial_types)]
        self.ts_edges = [e for e in self.ts_edges if not_artificial(e, artificial_edge_types)]

        if getattr(self, 'graph', None):
            self.graph.nodes = {k: v for k, v in self.graph.nodes.items() if not_artificial(v, artificial_types)}
            for k in self.graph.adjacency_list:
                self.graph.adjacency_list[k] = [(end_id, edge) for end_id, edge in self.graph.adjacency_list[k] if not_artificial(edge, artificial_edge_types)
                ]
        # Reset pipeline state
        pipeline = getattr(self, "pipeline", None)
        if pipeline:
            for attr in ("omega_edges", "omega_nodes", "omega_in", "omega_out", "in_caps", "out_caps"):
                val = type(getattr(pipeline, attr, []))()
                setattr(pipeline, attr, val)
            pipeline.max_flow_value = 0

        # Reset restriction_controller state
        rc = getattr(self, "restriction_controller", None)
        if rc and hasattr(rc, "restriction_edges"):
            rc.restriction_edges.clear()

    def use_in_main(self, use_config_data = False):
        self.ask_for_print_out(use_config_data)
        self.ask_spatial_map(use_config_data)
        self.started_nodes = [] #[1, 10]

        self.process_input_file(config.filepath)
        self.ask_horizontal_time(use_config_data)
        self.ask_for_draw(use_config_data)

        self.generate_hm_matrix()
        
        self.ask_for_d(use_config_data)
        
        self.generate_adj_matrix()
        
        num_of_agvs = self.reuse_for_tasks(use_config_data)

        self.create_tsg_file()
        self.add_time_window_first_time(num_of_agvs)
        #self.add_restrictions()
        self.gamma = 1
        self.restriction_count = 1
        self.restrictions = []
        self.ur = 3
        #pdb.set_trace()
        self.process_restrictions()
