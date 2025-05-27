from model.Node import Node

class NodeGenerator:
    @staticmethod
    def generate_node(is_artificial_node, id, label, graph_processor):
        if(is_artificial_node):
            if(label == "TimeWindow"):
                temp = TimeWindowNode(id, label)
                graph_processor.ts_nodes.append(temp)
                graph_processor.map_nodes[id] = temp
            elif(label == "Restriction"):
                temp = RestrictionNode(id, label)
                graph_processor.ts_nodes.append(temp)
                graph_processor.map_nodes[id] = temp
            elif (label == "Timeout"):
                temp = TimeoutNode(id, label)
                graph_processor.ts_node.append(temp)
                graph_processor.map_nodes[id] = temp
            else:
                temp = ArtificialNode(id, label)
                graph_processor.ts_nodes.append(temp)
                graph_processor.map_nodes[id] = temp
        else:
            time = id // graph_processor.M - (1 if id % graph_processor.M == 0 else 0)
            temp = None
            if(time >= graph_processor.H):
                temp = TimeoutNode(id, "Timeout")
            else:
                temp = Node(id)
            graph_processor.ts_nodes.append(temp)
            graph_processor.map_nodes[id] = temp
class ArtificialNode(Node):
    def __init__(self, id, label=None, temporary=False):
        super().__init__(id, label)
        self.temporary = temporary  # Indicates whether the node is temporary

    def __repr__(self):
        return f"ArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"
    
from controller.EdgeGenerator import RestrictionEdge
import pdb

class RestrictionNode(Node):
    def __init__(self, ID, restrictions):
        super().__init__(ID)
        self.restrictions = restrictions  # Restrictions associated with the node
        
    def create_edge(self, node, M, d, e):
        #pdb.set_trace()
        # Always returns a RestrictionEdge regardless of other node types or conditions.
        return RestrictionEdge(self, node, e, "Restriction")

    def __repr__(self):
        return f"RestrictionNode(ID={self.id}, restrictions={self.restrictions})"

class TimeoutNode(Node):
    def __init__(self, id, label=None, temporary=False):
        super().__init__(id, label)
        self.temporary = temporary  # Indicates whether the node is temporary

    def __repr__(self):
        return f"TimeoutNode(id={self.id}, label='{self.label}', temporary={self.temporary})"

class TimeWindowNode(Node):
    def __init__(self, ID, time_window):
        super().__init__(ID)
        self.time_window = time_window  # Time window in which the node can be accessed
        self.earliness = float('-inf')
        self.tardiness = float('inf')

    def set_time_window(self, earliness, tardiness):
        self.earliness = earliness
        self.tardiness = tardiness
        
    def calculate(self, reaching_time):
        if reaching_time >= self.earliness and reaching_time <= self.tardiness:
            return 0
        if reaching_time < self.earliness:
            return (-1)*(self.earliness - reaching_time)
        #if reaching_time > self.tardiness:
        return (reaching_time - self.tardiness)
        
    def create_edge(self, node, M, d, e):
        # Does nothing and returns None, effectively preventing the creation of any edge.
        return None
    
    def getEventForReaching(self, event):
        from controller.EventGenerator import ReachingTargetEvent
        if self.id == event.agv.target_node.id:
            #pdb.set_trace()
            print(f"Target {event.agv.target_node.id}")
            return ReachingTargetEvent(
                event.end_time, event.end_time, event.agv, event.graph, self.id
            )
        return None
    
    def __repr__(self):
        return f"TimeWindowNode(ID={self.id}, time_window={self.time_window})"
