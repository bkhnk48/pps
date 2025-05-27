from controller.NodeGenerator import TimeWindowNode
import random
import time
import math
import config
import pdb
from config import bcolors
    
class TimeDeterminator:
    def __init__(self, graph_processor):
        self._graph_processor = graph_processor
    
    def getReal(self, start_id, next_id, agv):
        M = self._graph_processor.graph.number_of_nodes_in_space_graph
        result = -1

        real_start_id, old_real_path = self._get_real_start_id_and_path(start_id, agv, M)
        start_time, end_time = self._calculate_times(start_id, next_id, M)
        space_start_node, space_end_node = self._get_space_nodes(start_id, next_id, M)

        min_moving_time = self._get_min_moving_time(space_start_node, space_end_node)
        end_time = max(end_time, start_time + min_moving_time)
        if self._graph_processor.is_target_node(next_id):
            result = 0
            self._update_agv_path(agv, next_id)

        result = self._handle_special_cases(start_id, next_id, start_time, end_time, result)

        if config.level_of_simulation == 2:
            result = self._calculate_sfm_runtime(space_start_node, space_end_node, agv, start_time, result)
        #elif config.level_of_simulation == 1 or config.level_of_simulation == 0:
        result = self._calculate_final_result(result, start_time, end_time)
        #else config.level_of_simulation == 0:
        #    pass
        return self._graph_processor.handle_collisions(result, next_id, agv, M)
    
    def _get_real_start_id_and_path(self, start_id, agv, M):
        if agv is None:
            return start_id % M + (M if start_id % M == 0 else 0), []
        old_real_path = [(node % M + (M if node % M == 0 else 0)) for node in agv.path]
        real_start_id = start_id % M + (M if start_id % M == 0 else 0)
        if real_start_id in old_real_path:
            return real_start_id, old_real_path
        agv.path.add(start_id)
        return real_start_id, old_real_path
    
    def _calculate_times(self, start_id, next_id, M):
        start_time = start_id // M - (1 if start_id % M == 0 else 0)
        end_time = next_id // M - (1 if next_id % M == 0 else 0)
        return start_time, end_time
    
    def _get_space_nodes(self, start_id, next_id, M):
        space_start_node = start_id % M + (M if start_id % M == 0 else 0)
        space_end_node = next_id % M + (M if next_id % M == 0 else 0)
        return space_start_node, space_end_node
    
    def _get_min_moving_time(self, space_start_node, space_end_node):
        edges_with_cost = {
            (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])]
            for edge in self._graph_processor.space_edges
            if edge[3] == '0' and int(edge[4]) >= 1
        }
        return edges_with_cost.get((space_start_node, space_end_node), [-1, -1])[1]
    
    def _update_agv_path(self, agv, node_id):
        if agv is not None:
            agv.path.add(node_id)
            
    def _handle_special_cases(self, start_id, next_id, start_time, end_time, result):
        try:
            if isinstance(self._graph_processor.graph.nodes[next_id], TimeWindowNode):
                return end_time - start_time if result == -1 else result
        except KeyError:
            #for e in self.ts_edges:
            #    if e[0] % self.graph.number_of_nodes_in_space_graph == start_id % self.graph.number_of_nodes_in_space_graph:
            for e in self._graph_processor.ts_edges:
                if e.start_node.id % self._graph_processor.graph.number_of_nodes_in_space_graph == start_id % self._graph_processor.graph.number_of_nodes_in_space_graph:
                    #result = e[4] if result == -1 else result
                    result = e.weight if result == -1 else result
            return abs(end_time - start_time) if result == -1 else result
        return result
    
    def _calculate_sfm_runtime(self, space_start_node, space_end_node, agv, start_time, result):
        runtime = self._graph_processor.getAGVRuntime(config.filepath, config.functions_file, space_start_node, space_end_node, agv, start_time)
        if runtime != -1:
            print(f"{bcolors.OKGREEN}{agv.id} from {space_start_node} to {space_end_node} at time {start_time} has runtime {runtime}.{bcolors.ENDC}")
            return runtime
        return result
    
    def _calculate_final_result(self, result, start_time, end_time):
        if result == -1:

            # Get the current time
            current_time = time.localtime()
            # Extract the components of the current time
            second = current_time.tm_sec
            minute = current_time.tm_min
            hour = current_time.tm_hour
            day = current_time.tm_mday
            month = current_time.tm_mon
            year = current_time.tm_year

            seed = second + minute * 60 + hour * 3600 + day * 86400 + month * 2592000 + year * 31104000
            # Seed the random number generator
            random.seed(seed)
            # Generate a random number with the given max value
            max_value = len(self._graph_processor.processed_numbers) if config.level_of_simulation == 1 else 300
            index = random.randint(0, max_value)
            if(config.level_of_simulation == 1):
                if index >= len(self._graph_processor.processed_numbers):
                    index = index % len(self._graph_processor.processed_numbers)
                    #pdb.set_trace()
            value = self._graph_processor.processed_numbers[index] if config.level_of_simulation == 1 else index
            return math.ceil((1 + value/100)*(end_time - start_time))
        return result