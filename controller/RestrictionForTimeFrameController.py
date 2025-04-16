from controller.NodeGenerator import ArtificialNode
from model.Edge import  ArtificialEdge
from collections import defaultdict
from model.Graph import Graph

class RestrictionForTimeFrameController:
    def __init__(self, graph_processor):
        self.restrictions = []
        self.M = graph_processor.M
        self.H = graph_processor.H
        self.graph_processor = graph_processor
    
    # Class ArtificalNode ở đây kế thừa abstract artificialNode trong NodeGenerator
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id, label=None):
            super().__init__(id, label)
            # self.temporary = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"     

    
    def get_restrictions(self):
        restrictions = []
        print("Bắt đầu nhập input các restrictions")
        L = int(input("Nhập số restrictions: "))        
        if L:
            print(f"{L} dòng tiếp theo hãy nhập các restriction và timeframe")
            for i in range(L):
                timeframe = list(map(int,input(f"Nhập timeframe cho restriction thứ {i+1} (vd: 3 4): ").split()))
                restriction_nodes = list(map(int,input(f"    Nhập các edges cho timeframe {timeframe} (vd 3 4 5 6 là 2 edge [3,4] và [5,6]): ").split()))
                try:
                    U = int(input(f"    Nhập số lượng AGV tối đa (U) cho restriction {i+1}: "))
                    if U < 0:
                        print("U phải là số không âm!")
                        continue
                except ValueError:
                    print("Nhập sai định dạng U!")
                    continue
                if (len(restriction_nodes) % 2 == 0 and len(restriction_nodes) >= 2):
                    restriction_edges = list(map(lambda i:[restriction_nodes[i], restriction_nodes[i+1]] , range(0, len(restriction_nodes), 2)))
                else: 
                    print("     Nhập sai định dạng restriction edges!")
                    return None
                restrictions.append((restriction_edges, timeframe,U))
        else:
            return None
        self.restrictions = restrictions
        return 1
    
    def restriction_parser(self, restriction):
        # Parse the restriction and timeframe
        restriction_edges, [start_time_frame, end_time_frame], U = restriction
        return restriction_edges, start_time_frame, end_time_frame, U
    
    def _get_node_time(self, node_id):
        M = self.M
        return node_id // M - (1 if node_id % M == 0 else 0)
    
    def _get_node_coordinates(self, node_id):
        M = self.M
        s = node_id % M if node_id % M != 0 else M
        return s
    
    def calculate_total_capacity(self, S_TSG):
        total = sum(capacity for (_, _,_, capacity, _) in S_TSG)
        return total

    def calculate_virtual_flow(self, total_capacity, U):
        return total_capacity - U
    
    def identify_restricted_edges(self, restriction_edges, start_time_frame, end_time_frame):
        S_TSG = []
        restriction_set = {(u,v) for u,v in restriction_edges}
        for edge in list(self.graph_processor.ts_edges):
            source_id, dest_id, _, capacity, cost = edge
            t1 = self._get_node_time(source_id)
            s_source = self._get_node_coordinates(source_id)
            t2 = self._get_node_time(dest_id)
            s_dest = self._get_node_coordinates(dest_id)
            base_edge = (s_source, s_dest)
            if base_edge in restriction_set:
                if (t1 <= start_time_frame and start_time_frame <=t2 ) or (t1 <= end_time_frame and end_time_frame <= t2) or (start_time_frame <= t1 and t2 <= end_time_frame):
                    S_TSG.append((source_id, dest_id,0, capacity, cost))                
        return S_TSG
        

    def apply_restriction(self):
        # Main method processing the restrictions
        if not self.get_restrictions():
            return 
        for restriction in self.restrictions:
            restriction_edges, start_time_frame, end_time_frame, U = self.restriction_parser(restriction)
            S_TSG = self.identify_restricted_edges(restriction_edges, start_time_frame, end_time_frame)
            if not S_TSG:
                print(f"Không tìm thấy cung nào trong restriction {restriction}.")
                continue
            
            total_capacity = self.calculate_total_capacity(S_TSG)
            virtual_flow = self.calculate_virtual_flow(total_capacity, U)
            
            if virtual_flow < 0:
                print(f"Lỗi: U ({U}) U không thể lớn hơn capacity ({total_capacity})")
                continue
            elif virtual_flow == 0:
                print(f"Đã thoả mãn {restriction}.")
                continue
            
            """
            Duyệt từng cung a(s, d) trong tập S các cung cần giới hạn (S_TSG)
                Nối vS và s 
                Cung ảo (vS, s) có lower bound bằng 0, capacity bằng capacity của a, chi phí bằng 0 
                Nối d và vD 
                Cung ảo (d, vD) có lower bound bằng 0, capacity bằng capacity của a, chi phí bằng 0 
            Kết thúc duyệt 
            """
            # Node ảo vS và vD
            max_id = self.graph_processor.get_max_id() + 1
            vS_id, vD_id = max_id, max_id + 1
            vS = self.RestrictionArtificialNode(vS_id)
            vD = self.RestrictionArtificialNode(vD_id)
            
            self.graph_processor.check_and_add_nodes([vS_id, vD_id], is_artificial_node=True, label="Restriction")
            self.graph_processor.ts_nodes.append(vS)
            self.graph_processor.ts_nodes.append(vD)
            self.graph_processor.map_nodes[vS_id] = vS
            self.graph_processor.map_nodes[vD_id] = vD
            
            new_edges = set()
            print("===========")
            for source_id, dest_id,_, capacity, cost in S_TSG:
                # vS -> source
                new_edges.add((vS_id, source_id, 0, capacity, 0))
                # dest -> vD
                new_edges.add((dest_id, vD_id, 0, capacity, cost))
                print(f"Node ao {vS_id} noi voi {source_id} - {self._get_node_coordinates(source_id)}:{self._get_node_time(source_id)}")
                print(f"{dest_id} - {self._get_node_coordinates(dest_id)}:{self._get_node_time(dest_id)} noi voi node ao {vD_id}")
            # vS -> vD
            new_edges.add((vS_id, vD_id, 0, self.H, virtual_flow))
            
            print("cac node ao:", vS_id, vD_id)
            print("Cac cung ao:", new_edges)
            
            self.graph_processor.ts_edges.extend(e for e in new_edges if e not in self.graph_processor.ts_edges)
            self.graph_processor.create_set_of_edges(new_edges)
        
        self.graph_processor.insert_halting_edges()

        # Ghi lại đồ thị vào file
        self.graph_processor.write_to_file()
        print("Đã áp dụng tất cả restrictions!")
        print("Đang kiểm tra việc tìm đường cho robot có tuân thủ ràng buộc không ...")
            

    def check_paths_compliance(self, paths):
        if not self.restrictions:
            print("Không có restrictions để kiểm tra.")
            return True, {}

        # List các vi phạm trả về nếu compliance = False
        violations = defaultdict(list) 
        
        # True nếu không vi phạm, False nếu vi phạm
        compliance = True
        for restriction_idx, restriction in enumerate(self.restrictions):
            restriction_edges, [start_time_frame, end_time_frame], U = restriction
            
            restricted_set = {(u, v) for u, v in restriction_edges}
            agv_count = 0
            path_violations = []
            for path_idx, path in enumerate(paths):
                if not path or len(path) < 2:
                    continue 

                for i in range(len(path) - 1):
                    src_id, dest_id = path[i], path[i + 1]
                    
                    t1 = self._get_node_time(src_id)
                    s_source = self._get_node_coordinates(src_id)
                    s_dest = self._get_node_coordinates(dest_id)
                    base_edge = (s_source, s_dest)

                    # Kiểm tra nếu cung thuộc khu vực cấm và nằm trong khung thời gian
                    if base_edge in restricted_set and start_time_frame <= t1 <= end_time_frame:
                        agv_count += 1
                        path_violations.append({
                            "path_idx": path_idx,
                            "edge": (src_id, dest_id),
                            "time": t1,
                            "space_edge": base_edge
                        })
            if agv_count > U:
                violations[restriction_idx].append({
                    "type": "exceed_U",
                    "agv_count": agv_count,
                    "U": U,
                    "violated_paths": path_violations})
                compliance = False
            
            if violations:
                print("\nĐã có AGV không tuân thủ restriction, dưới đây là các vi phạm:")
                for restriction_idx, violation_list in violations.items():
                    restriction = self.restrictions[restriction_idx]
                    print(f"Restriction {restriction_idx + 1}: {restriction}")
                    for violation in violation_list:
                        if violation["type"] == "exceed_U":
                            print(f"    Vi phạm: Số AGV ({violation['agv_count']}) vượt quá U ({violation['U']}).")
                            for path_violation in violation["violated_paths"]:
                                print(f"        path {path_violation['path_idx']}: "
                                    f"         edge ({path_violation['edge'][0]}, {path_violation['edge'][1]}) "
                                    f"         tại t={path_violation['time']}, space_edge {path_violation['space_edge']}")
                        else:
                            print(f"  - Lỗi: {violation}")
            else:
                print("Tất cả AGV đã tuân thủ restrictions")
            
            return compliance, violations
    
                        
        