from controller.NodeGenerator import ArtificialNode
from model.Edge import  ArtificialEdge
from collections import defaultdict
from model.Graph import Graph

class RestrictionForTimeFrameController:
    def __init__(self, graph_processor):
        self.restrictions = []
        self.gp = graph_processor
        self.M = graph_processor.M
        self.graph_processor = graph_processor
    
    # Class ArtificalNode ở đây kế thừa abstract artificialNode trong NodeGenerator
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id, label=None):
            super().__init__(id, label)
            # self.temporary = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"     
        

    class RestrictionArtificialEdge(ArtificialEdge):
        def __init__(self, source, target, capacity):
            super().__init__(source, target,upper=capacity, lower=0)
            self.weight = 0
            # self.temporary = True            
        def __repr__(self):
            return f"RestrictionArtificialEdge({self.start_node}, {self.end_node}, capacity={self.upper})"

    
    def get_restrictions(self):
        restrictions = []
        print("Nhập input các restrictions: ")
        L = int(input("Nhập số restrictions: "))        
        if L:
            print(f"{L} dòng tiếp theo hãy nhập các restriction và timeframe (vd: 3 4 5 6 restrction_edges là [(3,4),(5,6)] và timeframe là [3,4])")
            for i in range(L):
                restriction = input(f"Nhập restriction thứ {i+1}: ")
                restriction_edge, timeframe = restriction.split(" ")
                restrictions.append(restriction_edge, timeframe)
        else:
            return None
        self.restrictions = restrictions
    
    def restriction_parser(self, restriction):
        # Parse the restriction and timeframe
        restriction_edge, timeframe = restriction
        restriction_edges = eval(restriction_edge)
        start_time_frame, end_time_frame = eval(timeframe)
        return restriction_edges, start_time_frame, end_time_frame
    
    def _get_node_time(self, node_id):
        M = self.M
        return node_id // M - (1 if node_id % M == 0 else 0)
    
    def _get_node_coordinates(self, node_id):
        M = self.M
        s = node_id % M if node_id % M != 0 else M
        return s
    
    def calculate_total_capacity(self, S_TSG):
        total = sum(capacity for (_, _, capacity) in S_TSG)
        return total

    def calculate_virtual_flow(self, total_capacity):
        return total_capacity - self.U
    
    def identify_restricted_edges(self, restriction_edges, start_time_frame, end_time_frame):
        S_TSG = []
        for source_id, edges in list(self.graph_processor.graph.adjacency_list.items()):
            t1 = self._get_node_time(source_id)
            s_source = self._get_node_coordinates(source_id)
            for dest_entry in edges:
                dest_id, edge_obj = dest_entry
                t2 = self._get_node_time(dest_id)
                # Check if the edge is in the restricted edges set
                s_dest = self._get_node_coordinates(dest_id)
                base_edge = (s_source, s_dest)
                if base_edge in restriction_edges:
                    if (t1 <= start_time_frame <=t2 ) or (t1 <= end_time_frame <= t2) or (start_time_frame <= t1 and t2 <= end_time_frame):
                        capacity = edge_obj.capacity
                        S_TSG.append((source_id, dest_id, capacity))                
        return S_TSG
        

    def apply_restriction(self):
        # Main method processing the restrictions
        self.get_restrictions()
        
        for restriction in self.restrictions:
            restriction_edges, start_time_frame, end_time_frame = self.restriction_parser(restriction)
            S_TSG = self.identify_restricted_edges(restriction_edges, start_time_frame, end_time_frame)
            total_capacity = self.calculate_total_capacity(S_TSG)
            virtual_flow = self.calculate_virtual_flow(total_capacity)
            
            if virtual_flow < 0:
                print("Error: U cannot be greater than total capacity C")
                return None
            elif virtual_flow > 0:
                """
                Duyệt từng cung a(s, d) trong tập S các cung cần giới hạn (S_TSG)
                    Nối vS và s 
                    Cung ảo (vS, s) có lower bound bằng 0, capacity bằng capacity của a, chi phí bằng 0 
                    Nối d và vD 
                    Cung ảo (d, vD) có lower bound bằng 0, capacity bằng capacity của a, chi phí bằng 0 
                Kết thúc duyệt 
                """
                for source_id, dest_id, capacity in S_TSG:
                    # Create virtual nodes
                    vS = self.RestrictionArtificialNode(source_id)
                    vD = self.RestrictionArtificialNode(dest_id)

                    # Tạo mảng tham số cho cạnh ảo:
                    # lower bound = 0, upper (capacity) = capacity, weight = 0.
                    virtual_edge1 = [vS.id, source_id, 0, capacity, 0]
                    virtual_edge2 = [dest_id, vD.id, 0, capacity, 0]

                    # Thêm cạnh ảo vào đồ thị
                    self.graph_processor.add_edge_to_graph(vS.id, source_id, virtual_edge1)
                    self.graph_processor.add_edge_to_graph(dest_id, vD.id, virtual_edge2)
            

