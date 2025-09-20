from controller.reading_input_processor import ReadingInputProcessor
from model.Node import Node
from controller.NodeGenerator import TimeoutNode

#Sẽ được lớp TimeWindowGenerator kế thừa
class TsgFileEditor(ReadingInputProcessor):
    def __init__(self, dm):
        super().__init__(dm) 
        self._target_nodes = []
        self._ts_nodes = []
        self._ts_edges = []
    
    # Getter và Setter cho ts_nodes
    @property
    def ts_nodes(self):
        return self._ts_nodes

    @ts_nodes.setter
    def ts_nodes(self, value):
        if not isinstance(value, list):
            raise ValueError("ts_nodes must be a list")
        self._ts_nodes = value
    
    # Getter và Setter cho ts_edges
    @property
    def ts_edges(self):
        return self._ts_edges

    @ts_edges.setter
    def ts_edges(self, value):
        if not isinstance(value, list):
            raise ValueError("ts_edges must be a list")
        self._ts_edges = value
        
    @property
    def target_nodes(self):
        return self._target_nodes

    @target_nodes.setter
    def target_nodes(self, value):
        self._target_nodes = value
        
    def process_tsg_file(self, target_node, ID, earliness, tardiness):
        new_edges = set()

        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and len(parts) >= 6:
                        ID2 = int(parts[2])
                        self.process_line(ID, ID2, earliness, tardiness, new_edges, target_node)

        except FileNotFoundError:
            pass

        return new_edges

    def process_line(self, ID, ID2, earliness, tardiness, new_edges, target_node):
        for i in range(1, self.H + 1):
            j = i * self.M + ID
            if j == ID2:
                C = int(int(self.beta) * max(earliness - i, 0, i - tardiness) / int(self.alpha))
                new_edges.add((j, target_node.id, 0, 1, C))
                self.find_node(j).create_edge(target_node, self.M, self.d, [j, target_node.id, 0, 1, C])
                break

        t = ID2 // self.M - (1 if ID2 % self.M == 0 else 0)
        if t > self.H:
            C = self.H * self.H
            new_edges.add((j, target_node.id, 0, 1, C))
            self.find_node(j).create_edge(target_node, self.M, self.d, [j, target_node.id, 0, 1, C])
            
    def find_node(self, _id):
        _id = int(_id)
        # Tìm kiếm đối tượng Node có ID tương ứng
        if not hasattr(self, 'map_nodes'):
            # Nếu chưa tồn tại, chuyển self.ts_nodes thành self.map_nodes
            self.map_nodes = {node.id: node for node in self.ts_nodes}
        # Tìm kiếm trên self.map_nodes
        if _id in self.map_nodes:
            return self.map_nodes[_id]
        else:
            # Nếu không có trên map_nodes, thêm vào cả ts_nodes và map_nodes
            #if(id == 26272):
            #    pdb.set_trace()
            for node in self.target_nodes:
                if(node.id == _id):
                    self.map_nodes[_id] = node
                    return node
            time = _id // self.M - (1 if _id % self.M == 0 else 0)
            new_node = None
            if(time >= self.H):
                new_node = TimeoutNode(_id, "TimeOut")
            else:
                new_node = Node(_id)
            self.ts_nodes.append(new_node)
            self.map_nodes[_id] = new_node
            
            return new_node
        
    def append_edges_to_file(self, new_edges):
        """Thêm các cạnh mới vào file TSG.txt."""
        edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] 
                            for edge in self.space_edges if edge[3] == '0' and int(edge[4]) >= 1 }

        with open('TSG.txt', 'a') as file:
            for ID, j, c in new_edges:
                u, v = ID % self.M + (self.M if ID % self.M == 0 else 0), j % self.M + (self.M if j % self.M == 0 else 0)
                [upper, _] = edges_with_cost[(u, v)]
                file.write(f"a {ID} {j} 0 {upper} {c}\n")
        print("Da cap nhat file TSG.txt.")
        
    def update_file(self, id1=-1, id2=-1, c12=-1):
        """Cập nhật file TSG.txt với các cạnh mới dựa trên đầu vào."""
        ID1 = self.get_input_id(id1, "Nhap ID1: ")
        ID2 = self.get_input_id(id2, "Nhap ID2: ")
        C12 = self.get_input_weight(c12)

        ID2 = self.adjust_id2_if_needed(ID1, ID2, C12)

        existing_edges = self.load_existing_edges()
        if (ID1, ID2) not in existing_edges:
            new_edges = self.find_new_edges(ID1, ID2, C12)
            self.append_edges_to_file(new_edges)
