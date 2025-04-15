from controller.NodeGenerator import ArtificialNode
from controller.EdgeGenerator import ArtificialEdge
from controller.GraphProcessor import GraphProcessor
from collections import defaultdict

class RestrictionForTimeFrameController:
    def __init__(self, graph, U, restricted_edges, start_time_frame, end_time_frame):
        self.graph = graph  # Time-Space Graph (TSG)
        self.U = U  # Maximum number of AGVs allowed
        self.restricted_edges = restricted_edges  # Set of restricted edges to restrict
        self.start_time_frame = start_time_frame  # Start time of the timeframe
        self.end_time_frame = end_time_frame  # End time of the timeframe
        self.virtual_source = ArtificialNode(-1, 'vS', temporary=True)  # Virtual source node
        self.virtual_target = ArtificialNode(-2, 'vT', temporary=True)  # Virtual target node
        self.virtual_edges = []  # List of virtual edges

    def apply_restriction(self):
        # Step 1: Identify the set of edges in TSG corresponding to the restricted edges and timeframe [start_time_frame, end_time_frame]
        # Set S_TSG = None
        # For each edge a(s, d) in restricted_edges: 
        #     For each time-expanded edge (s_t1, d_t2) in TSG corresponding to e(s, d):
        #         If (t1 ≤ start_time_frame ≤ t2) OR (t1 ≤ end_time_frame ≤ t2) OR (start_time_frame ≤ t1 AND t2 ≤ end_time_frame):
        #             Add (s_t1, d_t2) to S_TSG
        
        # Step 2: Calculate the total capacity of the edges in S_TSG
        # max_capacity = sum(S_TSG)
        

        # Step 3: Calculate the virtual flow needed
        # F = Max - U

        # Step 4: If restriction is needed (F > 0), add virtual nodes and edges
        # If F < 0:
        #     Print "Error: U cannot be greater than total capacity C"
        #     Return null  // Trả về null nếu U không hợp lệ
        # Else If F > 0:
        #     Create virtuual source node and virtual target node
        #     vS = new ArtificialNode()
        #     vT = new ArtificialNode()
        #     Add vS to G
        #     Add vT to G

        # Return the updated TSG
        return self.graph


if __name__ == "__main__":
    # Example usage in a hypothetical scenario
    graph = Graph(...)  # Assume this is your graph object
    U = 5  # Maximum number of AGVs allowed
    restricted_edges = [...]  # List of restricted edges to restrict
    start_time_frame = 0  # Start time of restriction
    end_time_frame = 10  # End time of restriction

    restriction_controller = RestrictionForTimeFrameController(graph, U, restricted_edges, start_time_frame, end_time_frame)
    updated_graph = restriction_controller.apply_restriction()
    
from controller.NodeGenerator import ArtificialNode
from controller.EdgeGenerator import ArtificialEdge
from collections import defaultdict
from model.Graph import Graph

class RestrictionForTimeFrameController:
    def __init__(self, graph, U, restricted_edges, start_time_frame, end_time_frame):
        self.graph = graph
        self.U = U  # allowed capacity
        self.restricted_edges = restricted_edges
        self.start_time_frame = start_time_frame
        self.end_time_frame = end_time_frame

        self.virtual_source = ArtificialNode(-1, 'vS', temporary=True)
        self.virtual_target = ArtificialNode(-2, 'vT', temporary=True)

        self.virtual_edges = []
        
    def _get_node_time(self, node_id):
        M = self.graph.M
        return node_id // M - (1 if node_id % M == 0 else 0)
    
    def calculate_total_capacity(self, S_TSG):
        total = sum(capacity for (_, _, capacity) in S_TSG)
        return total

    def calculate_virtual_flow(self, total_capacity):
        return total_capacity - self.U
    
    def identify_restricted_edges(self):
        """
        Step 1: Identify the set of edges in TSG corresponding to the restricted edges and timeframe [start_time_frame, end_time_frame]        
        """
        S_TSG = []
        M = self.graph.M
        # Iterate over every edge in the time-space graph
        # Here we assume the graph stores time-expanded edges in an adjacency_list:
        for source_id, edges in self.graph.adjacency_list.items():
            t1 = self._get_node_time(source_id)
            for dest_entry in edges:
                dest_id, edge_obj = dest_entry
                t2 = self._get_node_time(dest_id)
                # Check if the base edge (s,d) matches one in the restricted_edges.
                # We assume edge_obj stores its original s and d in a list (e.g. as [s, d, ...])
                base_edge = (int(edge_obj.data[0]), int(edge_obj.data[1]))  # Adjust index as needed
                if base_edge in self.restricted_edges:
                    # If the time condition holds, add this edge.
                    if (t1 <= self.start_time_frame <= t2) or \
                       (t1 <= self.end_time_frame <= t2) or \
                       (self.start_time_frame <= t1 and t2 <= self.end_time_frame):
                        # Assume the capacity is stored as weight, otherwise adjust accordingly
                        capacity = getattr(edge_obj, "weight", 0)
                        S_TSG.append((source_id, dest_id, capacity))
        return S_TSG



    def add_virtual_nodes_and_edge(self, virtual_flow):
        """
        If virtual flow is needed (F > 0), add the virtual source and target nodes to the graph,
        and create a single virtual edge between them with capacity = virtual_flow.
        """
        # Add virtual source and target to the graph if not already present.
        if self.virtual_source.id not in self.graph.nodes:
            self.graph.nodes[self.virtual_source.id] = self.virtual_source
        if self.virtual_target.id not in self.graph.nodes:
            self.graph.nodes[self.virtual_target.id] = self.virtual_target
        # Create a virtual edge from vS to vT
        virtual_edge = ArtificialEdge(self.virtual_source, self.virtual_target, weight=virtual_flow, temporary=True)
        # Add the virtual edge to the graph's adjacency list.
        if self.virtual_source.id not in self.graph.adjacency_list:
            self.graph.adjacency_list[self.virtual_source.id] = []
        self.graph.adjacency_list[self.virtual_source.id].append((self.virtual_target.id, virtual_edge))
        self.virtual_edges.append(virtual_edge)

    def apply_restriction(self):
        """
        Apply the restriction algorithm using the following steps:
          1. Identify S_TSG: time-expanded edges corresponding to the restricted base edges
             that intersect the timeframe.
          2. Compute total capacity of these edges.
          3. Set F = total_capacity - U.
          4. If F < 0, print an error and return None.
             If F > 0, add virtual source and target nodes and a virtual edge representing
             the additional required flow.
          5. Return the updated Time-Space Graph.
        """
        S_TSG = self.identify_restricted_edges()
        total_capacity = self.calculate_total_capacity(S_TSG)
        virtual_flow = self.calculate_virtual_flow(total_capacity)
        
        if virtual_flow < 0:
            print("Error: U cannot be greater than total capacity C")
            return None
        elif virtual_flow > 0:
            self.add_virtual_nodes_and_edge(virtual_flow)
        
        # (Additional steps such as adjusting capacities or further updating the graph
        # may be implemented here as needed.)
        return self.graph


if __name__ == "__main__":
    graph = Graph(graph_processor=None)
    graph.M = 10  # for example
    graph.adjacency_list = {}  # should be populated properly
    graph.nodes = {}
    
    U = 5  # Allowed capacity
    restricted_edges = [(2, 3), (4, 5)]  # Example base edges to restrict
    start_time_frame = 0
    end_time_frame = 10
    
    restriction_controller = RestrictionForTimeFrameController(graph, U, restricted_edges, start_time_frame, end_time_frame)
    updated_graph = restriction_controller.apply_restriction()
    if updated_graph is not None:
        print("Restriction applied successfully.")
    else:
        print("Restriction could not be applied.")