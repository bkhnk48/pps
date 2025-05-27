from controller.NodeGenerator import TimeWindowNode
#from controller.reading_input_processor import ReadingInputProcessor
from controller.tsg_file_editor import TsgFileEditor

#Sẽ được lớp WaitingAndMovingEdgesGenerator kế thừa
class TimeWindowGenerator(TsgFileEditor):
    def __init__(self, dm):
        super().__init__(dm) 
        self._time_window_controller = None
        self._alpha = 1
        self._beta = 1
        self._gamma = 1
    
    # Getter và Setter cho time_window_controller
    @property
    def time_window_controller(self):
        return self._time_window_controller

    @time_window_controller.setter
    def time_window_controller(self, value):
        self._time_window_controller = value
        
    # Getter and Setter for alpha
    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value

    # Getter and Setter for beta
    @property
    def beta(self):
        return self._beta

    @beta.setter
    def beta(self, value):
        self._beta = value

    # Getter and Setter for gamma
    @property
    def gamma(self):
        return self._gamma

    @gamma.setter
    def gamma(self, value):
        self._gamma = value
        
    def append_target(self, target_node):
        if isinstance(target_node, TimeWindowNode):
            #pdb.set_trace()
            pass
        self._target_nodes.append(target_node)
        
    def get_targets(self, index = -1):
        if (index != -1):
            return self._target_nodes[index]
        return self._target_nodes
    
    def get_target_by_id(self, id):
        for node in self._target_nodes:
            if(node.id == id):
                return node
        return None
    
    def create_time_window_node(self, max_val):
        target_node = TimeWindowNode(max_val, "TimeWindow")
        self.ts_nodes.append(target_node)
        self.append_target(target_node)
        return target_node
    
    def get_max_id(self):
        max_val = 0
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a':
                        max_val = max(max_val, int(parts[2]))
        except FileNotFoundError:
            pass
        return max_val
    
    def get_initial_conditions(self, target_node):
        if isinstance(self.ID, list):
            if(len(self.ID) == 0):
                pdb.set_trace()
            ID = self.ID[0]
            earliness = self.earliness[0]
            tardiness = self.tardiness[0]
            self.ID = self.ID[1:]
            self.earliness = self.earliness[1:]
            self.tardiness = self.tardiness[1:]
        else:
            ID = self.ID
            earliness = self.earliness
            tardiness = self.tardiness

        self.time_window_controller.add_source_and_TWNode(ID, target_node, earliness, tardiness)
        return ID, earliness, tardiness
    
    def create_set_of_edges(self, edges):
        for e in edges:
            #self.tsedges.append(ArtificialEdge(self.find_node(e[0]), self.find_node(e[1]), e[4]))
            temp = self.find_node(e[0]).create_edge(self.find_node(e[1]), self.M, self.d, e)
            self.ts_edges.append(temp)
    
    def update_edges(self, new_edges):
        #self.ts_edges.extend(e for e in new_edges if e not in self.ts_edges)
        self.create_set_of_edges(new_edges)

        with open('TSG.txt', 'a') as file:
            for edge in new_edges:
                file.write(f"a {edge[0]} {edge[1]} {edge[2]} {edge[3]} {edge[4]}\n")
        
    def add_time_windows_constraints(self):
        from controller.TimeWindowController import TimeWindowController

        max_val = self.get_max_id() + 1
        target_node = self.create_time_window_node(max_val)

        if self.time_window_controller is None:
            self.time_window_controller = TimeWindowController(self.alpha, self.beta, self.gamma, self.d, self.H)

        ID, earliness, tardiness = self.get_initial_conditions(target_node)
        new_edges = self.process_tsg_file(target_node, ID, earliness, tardiness)

        self.update_edges(new_edges)

        if self.print_out:
            print(f"Đã cập nhật {len(new_edges)} cung mới vào file TSG.txt.")
    
    def add_time_window_first_time(self, num_of_agvs):
        count = 0

        while(count <= num_of_agvs - 1):
            #pdb.set_trace()
            if(isinstance(self.ID, int)):
                self.ID = 3
                self.earliness = 4 if count == 0 else 7
                self.tardiness = 6 if count == 0 else 9
                self.alpha = 1
                self.beta = 1

            self.add_time_windows_constraints()
            #assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.tsedges)}"
            count += 1
