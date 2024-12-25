from model.utility import get_largest_id_from_map
import inspect
from sortedcontainers import SortedSet
import pdb
from inspect import currentframe, getframeinfo
import numpy as np
from datetime import datetime

class AGV:
    _all_instances = set()
    def __init__(self, id, current_node, graph, cost = 0, version_of_graph = -1):
        self.id = id
        self._current_node = current_node
        self.previous_node = None
        self._target_node = None
        self.state = 'idle'
        self._cost = cost
        self.version_of_graph = version_of_graph
        self._traces = [] #các đỉnh sắp đi qua
        self._path = SortedSet([]) #các đỉnh đã đi qua 
        self.graph = graph
        if current_node not in self.graph.nodes.keys():
            #pdb.set_trace()
            node = self.graph.graph_processor.find_node(current_node)
            self.graph.nodes[current_node] = node
        self.graph.nodes[current_node].agv = self
        self.event = None
        AGV._all_instances.add(self)
        
    def destroy(self):
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        remaining_AGVs = len(AGV._all_instances) - 1
        print(f"Huy doi tuong {self.id} trong ham huy __del__ cua AGV.py. Con lai {remaining_AGVs} AGV(s). Time: {formatted_now}")
        AGV._all_instances.discard(self)
        
    @property
    def current_node(self):
        #pdb.set_trace()
        return self._current_node
    @current_node.setter
    def current_node(self, value):
        self._current_node = value
    
    @property
    def path(self):
        #pdb.set_trace()
        return self._path
    
    @path.setter
    def path(self, value):
        #pdb.set_trace()
        self._path = value
    
    @property
    def cost(self):
        return self._cost
    
    @cost.setter
    def cost(self, value):
        if(self.id == 'AGV4' and False):
            pdb.set_trace()
        self._cost = value
    
    @property
    def target_node(self):
        return self._target_node
    
    @staticmethod
    def all_instances():
        return AGV._all_instances
    @staticmethod
    def reset():
        AGV._all_instances.clear()
    
    @target_node.setter
    def target_node(self, value):
        if(value is None and (self.id == 'AGV23' or self.id == 'AGV32')):
            pdb.set_trace()
        self._target_node = value
    def update_info(self, width, length, speed):
        self.width = width
        self.length = length
        self.speed = speed
        
    def update_cost(self, amount):
        self.cost += amount
        if(self.graph.graph_processor.print_out):
            print(f"Cost updated for AGV {self.id}: {self.cost}.")

    def get_next_node(self, ended_event = False):
        #stack = inspect.stack()
        #for frame in stack[1:]:
        #pdb.set_trace()
            #print(f"Hàm '{frame.function}' được gọi từ file '{frame.filename}' tại dòng {frame.lineno}")
        if self._traces:
            if(ended_event):
                print(self.id)
                pdb.set_trace()
                self.current_node = self._traces.pop(0)
            next_node = None
            for node in self._traces:
                if(node.agv == self):
                    next_node = node
                    break
            if(next_node is None):
                next_node = self._traces[0]
            if(self.graph.graph_processor.ut):
                print(f"AGV {self.id} is moving to next node: {next_node} from current node: {self.current_node}.")
            return next_node
        else:
            print(f"AGV {self.id} has no more nodes in the trace. Remaining at node: {self.current_node}.")
            return None
    
    def get_traces(self):
        return self._traces
    
    def set_traces(self, traces):
        self._traces = traces
    
    def update_traces(self, predicted_id_node, real_node):
        #pdb.set_trace()
        index = 0
        M = self.graph.graph_processor.M
        for node in self._traces:
            if node.id % M == predicted_id_node % M:
                break
            else:
                index = index + 1
        if(index >= len(self._traces)):
            if(self.graph.graph_processor.print_out):
                print(f'{self.id} has _traces: {self._traces} needs to be inserted {real_node} at [{index}]')
            #pdb.set_trace()
            self._traces = [real_node]
        else:    
            self._traces[index] = real_node
    def move_to(self, event = None):
        if len(self._traces) >= 1:
            self.previous_node = self.current_node
            self.current_node = self.get_traces()[0].id
            self._traces.pop(0)
            self.state = 'moving'
            if(self.graph.graph_processor.print_out):
                print(f"AGV {self.id} moved from {self.previous_node} to {self.current_node}. State updated to 'idle'.")
            self.state = 'idle'
        else:
            if(self.graph.graph_processor.print_out):
                print(f"AGV {self.id} has no further destinations to move to.")

    def wait(self, duration):
        print(f"AGV {self.id} is waiting at node {self.current_node} for {duration} seconds.")
        self.state = 'waiting'
        # Simulate waiting
        self.state = 'idle'
        print(f"AGV {self.id} finished waiting at node {self.current_node}.")
    def add_traces(self, node):
        pdb.set_trace()
        self._traces.append(node)
        print(f"Node {node} added to AGV {self.id}'s trace. Current trace path: {self.traces}")

    def print_status(self):
        """ Utility method to print current status of the AGV """
        print(f"AGV {self.id}: Current Node: {self.current_node}, Previous Node: {self.previous_node}, State: {self.state}, Cost: {self.cost}, Upcoming Path: {self.traces}")
        
