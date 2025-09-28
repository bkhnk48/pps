import pdb
from inspect import currentframe, getframeinfo
import inspect

class Node:
    def __init__(self, id,label=None):
        frame = inspect.currentframe().f_back
        self.info = inspect.getframeinfo(frame)
        if not isinstance(id, int):
            raise ValueError(f"Tham số {id} truyền vào phải là số nguyên")
        self._id = id
        self.label=label
        self.edges = []
        self._agv = None
        
    @property
    def agv(self):
        return self._agv

    @agv.setter
    def agv(self, value):
        if(isinstance(value, str)):
            pdb.set_trace()
        self._agv = value

    @property
    def id(self):
        return self._id
    
    def get_raw_id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        self._id = value
    def create_edge(self, node, M, d, e, debug = False):
        if(debug):
            pdb.set_trace()
        from controller.NodeGenerator import RestrictionNode
        from controller.NodeGenerator import TimeWindowNode
        from model.Edge import HoldingEdge
        from controller.EdgeGenerator import RestrictionEdge
        from controller.EdgeGenerator import TimeWindowEdge 
        from model.Edge import MovingEdge
        if(isinstance(node, int)):
            pdb.set_trace()
        if node.id % M == self.id % M and \
        ((node.id - self.id) // M == d) and \
        isinstance(node, Node) and \
        not isinstance(node, RestrictionNode) and \
        not isinstance(node, TimeWindowNode):
            return HoldingEdge(self, node, e[2], e[3], d, d)
        elif isinstance(node, RestrictionNode):
            return RestrictionEdge(self, node, e, "Restriction")
        elif isinstance(node, TimeWindowNode):
            return TimeWindowEdge(self, node, e[4], "TimeWindows")
        elif isinstance(node, Node):
            if node.id % M != self.id % M:
                return MovingEdge(self, node, e[2], e[3], e[4])
        else:
            return None
        
    def connect(self, other_node, weight, graph):
        graph.add_edge(self.id, other_node.id, weight)
        
    def getEventForReaching(self, event):
        from controller.EventGenerator import HoldingEvent
        from controller.EventGenerator import ReachingTargetEvent
        
        current_node = event.agv.current_node.id if isinstance(event.agv.current_node, Node) else event.agv.current_node

        # Xác định kiểu sự kiện tiếp theo
        delta_t = (self.id // event.graph.number_of_nodes_in_space_graph \
                                #- (event.graph.graph_processor.d if self.id % event.graph.number_of_nodes_in_space_graph == 0 else 0)) - (
                                - (1 if self.id % event.graph.number_of_nodes_in_space_graph == 0 else 0)) - (
            current_node // event.graph.number_of_nodes_in_space_graph \
                                #- (event.graph.graph_processor.d if current_node % event.graph.number_of_nodes_in_space_graph == 0 else 0)
                                - (1 if current_node % event.graph.number_of_nodes_in_space_graph == 0 else 0)
        )
                                
        try:

            if (self.id % event.graph.number_of_nodes_in_space_graph) == (
                current_node % event.graph.number_of_nodes_in_space_graph
            ):
                from controller.EventGenerator import StartEvent
                if(not isinstance(event, StartEvent)):
                    event.agv.move_to(event)
                if event.end_time + delta_t >= event.graph.graph_processor.H:
                    return self._create_halting_event(event, self.id, delta_t)
                return HoldingEvent(
                    event.end_time, event.end_time + delta_t,
                    event.agv, event.graph,
                    delta_t, event.graph_processor
                )
            elif self.id == event.agv.target_node.id:
                print(f"Target {event.agv.target_node.id}")
                return ReachingTargetEvent(
                    event.end_time, event.end_time, event.agv, event.graph, self.id
                )
            else:
                #if event.agv.id == 'AGV23':
                #    pdb.set_trace()
                #return self.goToNextNode(event)
                M = event.graph.number_of_nodes_in_space_graph
                all_ids_of_target_nodes = [node.id for node in event.graph.graph_processor.target_nodes]
                if self.id in all_ids_of_target_nodes:
                    return self._create_reaching_target_event(event, self.id)

                if event.end_time + delta_t < event.graph.graph_processor.H:
                    if self.id % M == event.agv.current_node % M:
                        return self._create_holding_event(event, delta_t)
                    return self._create_moving_event(event, self.id, delta_t)

                return self._create_halting_event(event, self.id, delta_t)
        except Exception as e:
            pdb.set_trace()
            print(f"Error in getEventForReaching: {e}")
    def goToNextNode(self, event):
        M = event.graph.graph_processor.M
        if not self._is_start_event(event):
            current_node = event.agv.current_node.id \
                if isinstance(event.agv.current_node, Node) else event.agv.current_node
            if self.id % M == current_node % M and self.id != current_node:
                event.agv.move_to(event)
        L = len(event.agv.get_traces())
        i = 0
        while (i < L) or (i == 0 and L == 0):
            next_vertex = self._get_next_vertex(event, M)
            i = i+1
            if next_vertex != event.agv.current_node:
                #pdb.set_trace()
                break
            else:
                event.agv.move_to(event)
        
        delta_t = event.graph_processor.getReal(event.agv.current_node, next_vertex, event.agv)
        all_ids_of_target_nodes = [node.id for node in event.graph.graph_processor.target_nodes]
        
        if next_vertex in all_ids_of_target_nodes:
            return self._create_reaching_target_event(event, next_vertex)
        
        if delta_t == 0:
            pass
        
        if event.end_time + delta_t < event.graph.graph_processor.H:
            if next_vertex % M == event.agv.current_node % M:
                return self._create_holding_event(event, delta_t)
            return self._create_moving_event(event, next_vertex, delta_t)
        
        if event.graph.graph_processor.print_out:
            print(f"H = {event.graph.graph_processor.H} and {event.end_time} + {delta_t}")
        
        return self._create_halting_event(event, next_vertex, delta_t)

    def _is_start_event(self, event):
        from controller.EventGenerator import StartEvent
        return isinstance(event, StartEvent)

    def _get_next_vertex(self, event, M):
        if event.agv.get_traces():
            return event.agv.get_traces()[0].id
        return self._find_next_vertex_from_edges(event, M)

    def _find_next_vertex_from_edges(self, event, M):
        reaching_time = self.id // M - (1 if self.id % M == 0 else 0)
        for source_id in event.graph.graph_processor.time_window_controller.TWEdges:
            if source_id % M == self.id % M:
                edges = event.graph.graph_processor.time_window_controller.TWEdges.get(source_id)
                if edges:
                    return self._get_max_cost_vertex(edges, reaching_time)
        return -1
    #end of the method: def _find_next_vertex_from_edges(self, event, M):

    def _get_max_cost_vertex(self, edges, reaching_time):
        max_cost, index = edges[0][0].calculate(reaching_time), 0
        for i, edge in enumerate(edges[1:], 1):
            temp_cost = edge[0].calculate(reaching_time)
            if temp_cost > max_cost:
                max_cost, index = temp_cost, i
        return edges[index][0].id

    def _create_reaching_target_event(self, event, next_vertex):
        from controller.EventGenerator import ReachingTargetEvent
        return ReachingTargetEvent(event.end_time, event.end_time, event.agv, event.graph, next_vertex, event.graph_processor)

    def _create_moving_event(self, event, next_vertex, delta_t):
        from controller.EventGenerator import MovingEvent
        return MovingEvent(
            event.end_time,
            event.end_time + delta_t,
            event.agv,
            event.graph,
            event.agv.current_node,
            next_vertex,
            event.graph_processor,
        )

    def _create_halting_event(self, event, next_vertex, delta_t):
        from controller.EventGenerator import HaltingEvent
        return HaltingEvent(
            event.end_time,
            event.graph.graph_processor.H,
            event.agv,
            event.graph,
            event.agv.current_node,
            next_vertex,
            delta_t,
            event.graph_processor
        )
    def _create_holding_event(self, event, delta_t):
        from controller.EventGenerator import HoldingEvent
        from controller.EventGenerator import HaltingEvent
        if event.end_time + delta_t >= event.graph.graph_processor.H:
            return self._create_halting_event(event, self.id, delta_t)
        return HoldingEvent(
            event.end_time,
            event.end_time + delta_t,
            event.agv,
            event.graph,
            delta_t,
            event.graph_processor
        )
