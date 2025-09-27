from controller.waiting_and_moving_generator import WaitingAndMovingEdgesGenerator
from model.Node import Node
#Sẽ được lớp GraphValidator kế thừa
class EdgeModifier(WaitingAndMovingEdgesGenerator):
    def __init__(self, dm):
        super().__init__(dm)
        
    def insertEdgesAndNodes(self, start, end, edge):
        #pdb.set_trace()
        start_id = start if isinstance(start, int) else start.id
        end_id = end if isinstance(end, int) else end.id
        self.graph.adjacency_list[start_id].append((end_id, edge))
        start_node = start if isinstance(start, Node) else self.find_node(start)
        end_node = end if isinstance(end, Node) else self.find_node(end)
        if self.graph.nodes[start_id] is None:
            self.graph.nodes[start_id] = start_node
        if self.graph.nodes[end_id] is None:
            self.graph.nodes[end_id] = end_node
            
    def insert_from_queue(self, q, checking_list=None):
        """Chèn các cạnh từ hàng đợi vào đồ thị."""
        output_lines = []
        edges_with_cost = self.extract_edges_with_cost()
        ts_edges = self.get_ts_edges(checking_list)
        
        count = 0
        while q:
            if count % 1000 == 0:
                pass  # Có thể thêm log tại đây nếu cần
            count += 1
            ID = q.popleft()
            
            if not self.is_valid_id(ID):
                continue
            
            for j in self.adj.rows[ID]:
                if self.is_edge_present(ID, j, ts_edges):
                    continue
                
                self.add_edge_to_queue(q, ID, j, output_lines, edges_with_cost, checking_list)

        if checking_list is None:
            self.validate_edges()
        return output_lines
    
    def extract_edges_with_cost(self):
        """Trích xuất các cạnh có chi phí từ danh sách cạnh không gian."""
        return {(int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] 
                for edge in self.space_edges if edge[3] == '0' and int(edge[4]) >= 1}
        
    def add_edge_to_queue(self, q, ID, j, output_lines, edges_with_cost, checking_list):
        """Thêm cạnh vào hàng đợi và ghi lại vào output_lines nếu cần."""
        if j not in q:
            q.append(j)
        
        u, v = self.get_node_coordinates(ID, j)
        cost_info = edges_with_cost.get((u, v), (-1, -1))
        
        if self.should_add_edge(cost_info, ID, j, v):
            self.create_edge_output(output_lines, ID, j, cost_info, checking_list)
        elif ID + self.M * self.d == j and ID % self.M == j % self.M:
            self.create_holding_edge_output(output_lines, ID, j, checking_list)
            
    def find_new_edges(self, ID1, ID2, C12):
        """Tìm các cạnh mới cần thêm vào đồ thị."""
        q = deque([ID2])
        visited = {ID2}
        new_edges = [(ID1, ID2, C12)]

        while q:
            ID = q.popleft()
            for j in self.adj.rows[ID]:
                if j not in visited:
                    c = self.d if ID + self.M * self.d == j and ID % self.M == j % self.M else C12
                    if (ID // self.M) + c == j // self.M:
                        new_edges.append((ID, j, c))
                        q.append(j)
                        visited.add(j)
        
        return new_edges