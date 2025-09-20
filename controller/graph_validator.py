from controller.edge_modifier import EdgeModifier

#Sẽ được lớp KickOffGenerator kế thừa
class GraphValidator(EdgeModifier):
    def __init__(self, dm):
        super().__init__(dm)
    
    def version_check(self, current_time):
        """Kiểm tra nếu phiên bản cần được cập nhật."""
        time2 = self.graph.number_of_nodes_in_space_graph // self.M - (1 if self.graph.number_of_nodes_in_space_graph % self.M == 0 else 0)
        return time2 != current_time
    
    def is_valid_id(self, ID):
        """Kiểm tra xem ID có hợp lệ không."""
        return 0 <= ID < self.adj.shape[0]

    def is_target_node(self, next_id):
        all_ids_of_target_nodes = [node.id for node in self.target_nodes]
        return next_id in all_ids_of_target_nodes

    def should_add_edge(self, cost_info, ID, j, v):
        """Kiểm tra điều kiện để thêm cạnh."""
        upper, cost = cost_info
        return ((ID // self.M) + cost >= (j // self.M) - (v // self.M)) and (upper != -1)
    
    """def process_number(self, num):
        import math
        if num < 5:
            return 0
        else:
            return math.ceil(num)"""

    def validate_edges(self):
        pass
        """Kiểm tra tính nhất quán của các cạnh."""
        #assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.tsedges)} != {len(self.ts_edges)}" 
    
    def handle_collisions(self, result, next_id, agv, M):
        all_ids_of_target_nodes = [node.id for node in self.target_nodes]
        collision = True
        while collision:
            collision = False
            if next_id not in all_ids_of_target_nodes and next_id in self.graph.nodes:
                node = self.graph.nodes[next_id]
                if node.agv and node.agv != agv:
                    print(f'{node.agv.id} != {agv.id}')
                    collision = True
                    result += 1
                    next_id += M
        return result
        
    def check_file_conditions(self):
        try:
            seen_edges = set()
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] != 'a':
                        continue
                    ID1, ID2 = int(parts[1]), int(parts[2])

                    # Condition 1: ID1 should not equal ID2
                    if ID1 == ID2:
                        print("False")
                        return

                    # Condition 2: If ID1 before ID2, then ID2 should not come before ID1
                    if (ID1, ID2) in seen_edges or (ID2, ID1) in seen_edges:
                        print("False")
                        return
                    else:
                        seen_edges.add((ID1, ID2))

                    # Condition 3: ID2/self.M should be greater than ID1/self.M
                    if ID2 // self.M <= ID1 // self.M:
                        print("False")
                        return

            print("True")
        except FileNotFoundError:
            print("File TSG.txt khong ton tai!")
