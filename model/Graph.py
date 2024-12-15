import os
import pdb
from collections import deque, defaultdict
from model.utility import utility
import inspect
from controller.NodeGenerator import RestrictionNode
from controller.NodeGenerator import TimeWindowNode
from controller.NodeGenerator import TimeoutNode
from model.Node import Node
import config
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
class Graph:
    def __init__(self, graph_processor):
        self._graph_processor = graph_processor
        self._adjacency_list = defaultdict(list)
        self._nodes = {node.id: node for node in graph_processor.ts_nodes} if graph_processor else {}
        self._adjacency_list = {node.id: [] for node in graph_processor.ts_nodes} if graph_processor else {}
        self._list1 = []
        self._neighbour_list = {}
        self._visited = set()
        self._version = -1
        self._file_path = None
        self._cur = []
        self._map = {}
        self._number_of_nodes_in_space_graph = -1 if graph_processor is None else graph_processor.M
        self._calling = 0
        self._continue_debugging = True
        self._history = []
        if graph_processor is not None:
            graph_processor.graph = self
            
#==========================================================================================

    # Getter và setter cho graph_processor
    @property
    def graph_processor(self):
        return self._graph_processor

    @graph_processor.setter
    def graph_processor(self, value):
        self._graph_processor = value

    # Getter và setter cho adjacency_list
    @property
    def adjacency_list(self):
        return self._adjacency_list

    @adjacency_list.setter
    def adjacency_list(self, value):
        self._adjacency_list = value

    # Getter và setter cho nodes
    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = value

    # Getter và setter cho list1
    @property
    def list1(self):
        return self._list1

    @list1.setter
    def list1(self, value):
        self._list1 = value

    # Getter và setter cho neighbour_list
    @property
    def neighbour_list(self):
        return self._neighbour_list

    @neighbour_list.setter
    def neighbour_list(self, value):
        self._neighbour_list = value

    # Getter và setter cho visited
    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, value):
        self._visited = value

    # Getter và setter cho version
    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    # Getter và setter cho file_path
    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        self._file_path = value

    # Getter và setter cho cur
    @property
    def cur(self):
        return self._cur

    @cur.setter
    def cur(self, value):
        self._cur = value

    # Getter và setter cho map
    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, value):
        self._map = value

    # Getter và setter cho number_of_nodes_in_space_graph
    @property
    def number_of_nodes_in_space_graph(self):
        return self._number_of_nodes_in_space_graph

    @number_of_nodes_in_space_graph.setter
    def number_of_nodes_in_space_graph(self, value):
        self._number_of_nodes_in_space_graph = value

    # Getter và setter cho calling
    @property
    def calling(self):
        return self._calling

    @calling.setter
    def calling(self, value):
        self._calling = value

    # Getter và setter cho continue_debugging
    @property
    def continue_debugging(self):
        return self._continue_debugging

    @continue_debugging.setter
    def continue_debugging(self, value):
        self._continue_debugging = value

    # Getter và setter cho history
    @property
    def history(self):
        return self._history

    @history.setter
    def history(self, value):
        self._history = value

#==========================================================================================
    def count_edges(self):
        count = 0
        for node in self.adjacency_list:
            count = count + len(self.adjacency_list[node])
        return count
    
    def find_unpredicted_node(self, id, forceFinding = False, isTargetNode = False):
        node = None
        idIsAvailable = id in self.nodes
        if idIsAvailable and not forceFinding:
            node = self.nodes[id]
        else:
            #if start == -1:
            found = False
            M = self.number_of_nodes_in_space_graph
            for x in self.nodes:
                if(x % M == id % M and (self.nodes[x].agv is not None or isTargetNode)):
                    if(idIsAvailable):
                        if(type(self.nodes[x]) == type(self.nodes[id])):
                            found = True
                    elif(isinstance(self.nodes[x], Node)\
                                and not isinstance(self.nodes[x], TimeWindowNode)\
                                    and not isinstance(self.nodes[x], RestrictionNode)):
                        found = True
                    if(found):
                        node = self.nodes[x]
                        break
        return node
        
    def build_path_tree(self, file_path = 'traces.txt'):
        """ Build a tree from edges listed in a file for path finding. """
        #pdb.set_trace()
        id1_id3_tree = defaultdict(list)
        M = self.number_of_nodes_in_space_graph
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('a'):
                    numbers = line.split()
                    id1 = int(numbers[1])
                    id3 = int(numbers[2])
                    id2 = id1 % M
                    id4 = id3 % M
                    node1 = self.find_unpredicted_node(id1) 
                    if (node1 is not None):
                        #pdb.set_trace()
                        isTargetNode = True
                        node3 = self.find_unpredicted_node(id3, node1.id != id1, isTargetNode)
                        if(node3 is None):
                            print(f"{node1.id}/{id1} {id3}")
                        id3 = node3.id
                        self.neighbour_list[id1] = id2
                        self.neighbour_list[id3] = id4
                        if(node1.id in self.graph_processor.started_nodes or\
                            node1.agv is not None):
                            #pdb.set_trace()
                            self.list1.append(node1.id)
                        id1_id3_tree[node1.id].append(node3)
                        id1_id3_tree[id3].append(node1)
        return id1_id3_tree

    def dfs(self, tree, start_node):
        self.visited.add(start_node)
        for node in tree[start_node]:
            node_id = node if isinstance(node, int) else node.id
            if node_id not in self.visited:
                #print(node, end=' ')
                self.cur.append(node)
                #self.id2_id4_list.append(self.neighbour_list[node_id])
                self.dfs(tree, node_id)

    def setTrace(self, file_path = 'traces.txt'):
        #pdb.set_trace()
        self.file_path = file_path #'traces.txt'
        self.list1 = []
        self.neighbour_list = {}
        self.visited = set()
        self.map = {}
        edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] for edge in self.graph_processor.space_edges \
            if edge[3] == '0' and int(edge[4]) >= 1 }
        M = self.graph_processor.M
        id1_id3_tree = self.build_path_tree()#self.list1 sẽ được thay đổi ở đâyđây
        for number in self.list1:
            if number not in self.visited:
                self.cur = []
                self.dfs(id1_id3_tree, number)
                self.visited = set()
                if len(self.cur) >= 1:
                    start = number % M + (M if number % M == 0 else 0)
                    end = self.cur[0].id % M + (M if self.cur[0].id % M == 0 else 0)
                    start_time = number // M - (1 if number % M == 0 else 0)
                    end_time = self.cur[0].id // M - (1 if self.cur[0].id % M == 0 else 0)
                    min_cost = edges_with_cost.get((start, end), [-1, -1])[1]
                    if(min_cost == -1):
                        need_to_remove_first_cur = True
                        if(start == end and number != self.cur[0].id and end_time - start_time == self.graph_processor.d):
                            need_to_remove_first_cur = False
                        if need_to_remove_first_cur:
                            found = False
                            for source_id, edges in self.graph_processor.time_window_controller.TWEdges.items():
                                if edges is not None and source_id % M == start:
                                    for index, e in enumerate(edges):
                                        if e[0].id ==end:
                                            found = True
                                            break
                            if(not found):                                    
                                self.cur = self.cur[1:]
                self.map[number] = self.cur #[1: ] if len(self.cur) > 1 else self.cur
    
    def getTrace(self, agv):
        #pdb.set_trace()
        idOfAGV = int(agv.id[3:])

        if idOfAGV in self.map:
            return self.map[idOfAGV]  
        else:
            found = False
            temp = []
            for id in self.nodes:
                if self.nodes[id].agv == agv:
                    #    pdb.set_trace()
                    if(id not in self.map):
                        for old_id in self.map.keys():
                            if(self.nodes[id].agv == self.nodes[old_id].agv):
                                temp = self.map[old_id]
                                found = True
                                break
                            else:
                                if isinstance(self.map[old_id], list):
                                    for node in self.map[old_id]:
                                        if node.agv == agv:
                                            temp = self.map[old_id]
                                            found = True
                                            break
                            if found:
                                break
                    else:
                        temp = self.map[id]#13899
                        found = True
                    node = self.nodes[id]
                    #    pdb.set_trace()
                    return [node, *temp]
                    #return s self.map[id]
        return None
    
    def has_initial_movement(self, node):
        # Check if there are any outgoing edges from 'node'
        return node in self.edges and len(self.edges[node]) > 0  
              
    def update_node(self, node, properties):
        return
 
    def add_edge(self, from_node, to_node, weight):
        self.adjacency_list[from_node].append((to_node, weight))
        print(f"Edge added from {from_node} to {to_node} with weight {weight}.")

    def display_graph(self):
        print("Displaying graph structure:")
        for start_node in self.adjacency_list:
            for end, weight in self.adjacency_list[start_node]:
                print(f"{start_node} -> {end} (Weight: {weight})")
            
    def get_edge(self, start_node, end_node):
        for neighbor, weight in self.adjacency_list[start_node]:
            if neighbor == end_node:
                print(f"Edge found from {start_node} to {end_node} with weight {weight}.")
                return weight
        print(f"No edge found from {start_node} to {end_node}.")
        return None
    
    def find_edge_by_weight(self, start_node, weight):
        # Find all edges from a node with a specific weight
        return [edge for edge in self.edges if edge.start_node == start_node and edge.weight == weight]
    
    def find_path(self, start_node, end_node):
        # Placeholder for a pathfinding algorithm like Dijkstra's
        queue = deque([start_node])
        visited = set()
        path = []
        
        while queue:
            node = queue.popleft()
            if node == end_node:
                break
            visited.add(node)
            for neighbor, weight in self.adjacency_list[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
                    path.append((node, neighbor, weight))
        return path
    
    def parse_string(self, input_string):
        parts = input_string.split()
        if len(parts) < 6 or parts[0] != "a":
            return None  # Chuỗi không đúng định dạng
        try:
            ID1, ID2, L, U, C = map(int, parts[1:6])
            return [ID1, ID2, L, U, C]
        except ValueError:
            return None  # Không thể chuyển thành số nguyên
    
    def get_current_node(self, agv_id_and_new_start, start):
        if(agv_id_and_new_start is None):
            return start
        if agv_id_and_new_start[0] == f'AGV{str(start)}':
            #print(agv_id_and_new_start[1])
            return agv_id_and_new_start[1]
        return start
    
    def getAllNewStartedNodes(self, excludedAgv = None):
        from model.AGV import AGV
        allAGVs = AGV.all_instances()
        started_nodes = set()
        from controller.EventGenerator import ReachingTargetEvent
        for agv in allAGVs:
            if(not isinstance(agv.event, ReachingTargetEvent)):
                started_nodes.add(agv.current_node)
        if(len(started_nodes) == 0):
            return self.graph_processor.started_nodes
        return started_nodes
        
    def write_to_file(self, agv_id_and_new_start = None, new_halting_edges = None, filename="TSG.txt"):
        #    pdb.set_trace()
        M = max(target.id for target in self.graph_processor.get_targets())
        m1 = max(edge[1] for edge in new_halting_edges)
        M = max(M, m1)
        num_halting_edges = len(new_halting_edges) if new_halting_edges is not None else 0
        #pdb.set_trace()
        sorted_edges = sorted(self.adjacency_list.items(), key=lambda x: x[0])
        num_edges = self.count_edges()
        num_edges = num_edges + num_halting_edges
        
        with open(filename, 'w') as file:
            file.write(f"p min {M} {num_edges}\n")
            #    pdb.set_trace()
            
            started_nodes = self.getAllNewStartedNodes()
            if(len(started_nodes) != len(self.graph_processor.get_targets())):
                pdb.set_trace()
                started_nodes = self.getAllNewStartedNodes()
                targets = self.graph_processor.get_targets()

            for start_node in started_nodes:
                file.write(f"n {start_node} 1\n")
            for target in self.graph_processor.get_targets():
                target_id = target.id
                file.write(f"n {target_id} -1\n")
            #for edge in self.ts_edges:
            #for edge in self.tsedges:
            new_nodes = set()
            for source_id, edges in sorted_edges:
                for edge in edges:
                    t = edge[0] // self.graph_processor.M - (1 if edge[0] % self.graph_processor.M == 0 else 0)
                    file.write(f"a {source_id} {edge[0]} {edge[1].lower} {edge[1].upper} {edge[1].weight}\n")  
            for edge in new_halting_edges:
                file.write(f"a {edge[0]} {edge[1]} {edge[2]} {edge[3]} {edge[4]}\n")

    def __str__(self):
        return "\n".join(f"{start} -> {end} (Weight: {weight})" for start in self.adjacency_list for end, weight in self.adjacency_list[start])
