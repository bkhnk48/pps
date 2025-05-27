from controller.waiting_and_moving_generator import WaitingAndMovingEdgesGenerator
from controller.graph_validator import GraphValidator

#Sẽ được lớp GraphProcessor kế thừa
class KickOffGenerator(GraphValidator):
    def __init__(self, dm):
        super().__init__(dm) 
    
    def init_agvs_n_events(self, all_agvs, events, graph, graph_processor):
        from controller.EventGenerator import StartEvent
        StartEvent.static_index = 0
        from model.AGV import AGV
        for node_id in self.started_nodes:
            #pdb.set_trace()
            agv = AGV("AGV" + str(node_id), node_id, graph)  # Create an AGV at this node
            #print(Event.getValue("number_of_nodes_in_space_graph"))
            #if(self.M == 0):
            #    pdb.set_trace()
            start_time = node_id // self.M - (1 if node_id % self.M == 0 else 0)
            #if(node_id % self.M == 0):
            #    pdb.set_trace()
            end_time = start_time
            start_event = StartEvent(start_time, end_time, agv, graph, graph_processor)  # Start event at time 0
            events.append(start_event)
            all_agvs.add(agv)  # Thêm vào tập hợp AGV
        
    def init_tasks(self, tasks):
        for node_id in self.get_targets():
            tasks.add(node_id)
