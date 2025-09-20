from model.utility import utility
from model.Graph import Graph
import subprocess
from discrevpy import simulator
from model.AGV import AGV
from model.Edge import Edge
import pdb
import os
from collections import defaultdict
import config
from inspect import currentframe, getframeinfo
from model.NXSolution import NetworkXSolution

number_of_nodes_in_space_graph = 0
debug = 0
allAGVs = {}
numOfCalling = 0

class Event:
    def __init__(self, start_time, end_time, agv, graph, graph_processor):
        self.start_time = int(start_time)
        self.end_time = int(end_time)
        self.agv = agv
        self.agv.event = self
        self.graph = graph
        self.graph_processor = graph_processor
        self.pns_path = ""
        if(config.solver_choice == 'solver'):
            pdb.set_trace()

    def setValue(name, value):
        if name == "debug":
            global debug
            debug = value
        if name == "number_of_nodes_in_space_graph":
            global number_of_nodes_in_space_graph
            number_of_nodes_in_space_graph = value
        if name == "allAGVs":
            global allAGVs
            allAGVs = value

    def getValue(name):
        if name == "debug":
            global debug
            return debug
        if name == "number_of_nodes_in_space_graph":
            global number_of_nodes_in_space_graph
            return number_of_nodes_in_space_graph
        if name == "allAGVs":
            global allAGVs
            return allAGVs

    def process(self):
        if(config.solver_choice == 'solver'):
            pdb.set_trace()
        #pdb.set_trace()
        edge = self.graph.get_edge(self.start_node, self.end_node)
        if edge is not None:
            print(
                f"Edge found from {self.start_node} to {self.end_node} with weight {edge}"
            )
        else:
            print(f"No edge found from {self.start_node} to {self.end_node}")

    def __repr__(self):
        return f"(time=[{self.start_time}, {self.end_time}], agv_id={self.agv.id})"

    def getWait(self, wait_time):
        obj = utility()
        graph = Graph(self.x)
        self.pos = self.pos + wait_time * obj.M
        self.time = self.time + wait_time
        graph.writefile(self.pos, 1)
        
    def getForecast(self, nextpos, forecastime):
        obj = utility()
        self.pos = obj.M * (int(self.pos / obj.M) + forecastime) + obj.getid(nextpos)
        self.time = self.time + forecastime
        graph = Graph(self.x)
        graph.writefile(self.pos, 1)

    def saveGraph(self):
        # Lưu đồ thị vào file DIMACS và trả về tên file
        filename = "TSG.txt"
        #filename = "input_dimacs/supply_03_demand_69_edit.txt"
        # Code để lưu đồ thị vào file
        return filename
    
    def solve(self):
        from model.forecasting_model_module.ForecastingModel import ForecastingModel, DimacsFileReader
        #pdb.set_trace()
        if self.graph.number_of_nodes_in_space_graph == -1:
            global number_of_nodes_in_space_graph
            self.graph.number_of_nodes_in_space_graph = number_of_nodes_in_space_graph
        if (self.graph.version != self.agv.version_of_graph or self.graph.version == -1):
            self.find_path(DimacsFileReader, ForecastingModel)

    def getNext(self):
        from controller.EventGenerator import HaltingEvent
        from controller.EventGenerator import MovingEvent
        from controller.EventGenerator import HoldingEvent
        if(self.agv.id == 'AGV23' and self.start_time == 20 and self.end_time == 30):
            if(self.agv.current_node == 1303 and config.solver_choice == 'solver'):
                pdb.set_trace()
        self.solve()

        if(len(self.agv.get_traces()) == 0):
            pdb.set_trace()
        next_vertex = self.agv.get_next_node()

        if(next_vertex is None):
            print(f'{self.agv.id} at Event.py:155')
            pdb.set_trace()
        new_event = next_vertex.getEventForReaching(self)

        # Lên lịch cho sự kiện mới
        # new_event.setValue("allAGVs", self.allAGVs)
        # simulator.schedule(new_event.end_time, new_event.getNext, self.graph)
        simulator.schedule(new_event.end_time, new_event.process)

    def find_path(self, DimacsFileReader, ForecastingModel):
        """ Find the optimal path for AGVs based on the configured solver choice. """
        self.ensure_graph_updated()
        filename = self.saveGraph()
        
        if config.solver_choice == 'solver':
            pdb.set_trace()
            self.run_solver_trace(DimacsFileReader, filename, ForecastingModel)
        elif config.solver_choice == 'network-simplex':
            self.run_network_simplex(filename)
        elif config.solver_choice == 'networkx':
            self.run_networkx_solution()

        self.finalize_solution()
        from controller.EventGenerator import MovingEvent
        if (self.agv.id == 'AGV4' and self.start_time == 0 and self.agv.current_node == 3843):
            if(config.solver_choice == 'solver' and isinstance(self, MovingEvent)):
                pdb.set_trace()
        self.setTracesForAllAGVs()

    def ensure_graph_updated(self):
        """ Update the graph if versions are mismatched. """
        if self.graph.version == -1 == self.agv.version_of_graph:
            self.updateGraph()

    def run_solver_trace(self, DimacsFileReader, filename, ForecastingModel):
        """ Run the trace creation with the selected solver. """
        self.createTracesFromSolver(DimacsFileReader, filename, ForecastingModel)

    def run_network_simplex(self, filename):
        """ Execute the network-simplex algorithm using an external command. """
        if not self.pns_path:
            self.pns_path = input("Enter the path for pns-seq: ")
        command = f"{self.pns_path}/pns-seq -f {filename} > seq-f.txt"
        print("Running network-simplex:", command)
        subprocess.run(command, shell=True)
        self.filter_traces()

    def filter_traces(self):
        """ Filter traces after network-simplex run. """
        command = "python3 filter.py > traces.txt"
        print("Filtering traces:", command)
        subprocess.run(command, shell=True)

    def run_networkx_solution(self):
        """ Run the networkx solution for trace generation. """
        nx = NetworkXSolution()
        nx.read_dimac_file('TSG.txt')
        nx.edges_with_costs = {
            (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])]
            for edge in self.graph.graph_processor.space_edges
            if edge[3] == '0' and int(edge[4]) >= 1
        }
        nx.M = self.graph.graph_processor.M
        nx.write_trace()

    def finalize_solution(self):
        """ Finalize solution by updating graph version. """
        if self.graph.version == -1 == self.agv.version_of_graph:
            self.graph.version += 1

    def createTracesFromSolver(self, DimacsFileReader, filename, ForecastingModel):
        pdb.set_trace()
        from controller.EventGenerator import HoldingEvent, MovingEvent
        if(self.agv.id == 'AGV4' and self.start_time == 0 and \
            self.end_time == 60 and config.solver_choice == 'solver'\
                and isinstance(self, MovingEvent)):
            pdb.set_trace()
        dimacs_file_reader = DimacsFileReader(filename)
        dimacs_file_reader.read_custom_dimacs(self.graph_processor)
        problem_info, supply_nodes_dict, demand_nodes_dict, zero_nodes_dict, arc_descriptors_dict, \
            earliness_tardiness_dict = dimacs_file_reader.get_all_dicts()
        model = ForecastingModel(problem_info, supply_nodes_dict, demand_nodes_dict, zero_nodes_dict, arc_descriptors_dict, earliness_tardiness_dict)
        #if(model == None):
        #pdb.set_trace()
        model.graph = self.graph
        model.solve()
        model.output_solution()
        model.save_solution(filename, "test_ouput") # Huy: sửa lại để log ra file
        
        if(self.agv.id == 'AGV23' and self.start_time == 20 and \
            self.end_time == 30 and config.solver_choice == 'solver'\
                and isinstance(self, HoldingEvent)):
            pdb.set_trace()
        
        if(self.agv.id == 'AGV4' and self.start_time == 0 and \
            self.end_time == 60 and config.solver_choice == 'solver'\
                and isinstance(self, MovingEvent)):
            pdb.set_trace()
        model.create_traces("traces.txt", self.graph.version)

    def updateGraph(self):
        pass
        # Assuming that `self.graph` is an instance of `Graph`
        # edge = self.graph.get_edge(self.agv.start_node, self.end_node)
        # if edge:
        # Proceed with your logic
        # print("Edge found:", edge)
        # else:
        # print("No edge found between", self.start_node, "and", self.end_node)

    def calculate_cost_event(self):
        # Increase cost by the actual time spent in holding
        cost_increase = self.graph.graph_processor.alpha*(self.end_time - self.start_time)
        self.agv.cost += cost_increase
        return cost_increase

    def run_pns_sequence(self, filename):
        command = f"./pns-seq -f {filename} > seq-f.txt"
        subprocess.run(command, shell=True)
        command = "python3 filter.py > traces.txt"
        subprocess.run(command, shell=True)

    def setTracesForAllAGVs(self):
        config.count_set_traces += 1
        #if(config.count_set_traces == 2):
        #    pdb.set_trace()
        """ Set traces for all AGVs based on current graph traces and target nodes. """
        self.graph.setTrace("traces.txt")
        
        # Thiết lập traces cho AGV hiện tại
        temp_trace = self.graph.getTrace(self.agv)
        #from controller.TimeWindowNode import TimeWindowNode
        target_node_ids = {node.get_raw_id() for node in self.graph.graph_processor.target_nodes}
        """target_node_ids = {
            node.get_real_node_id() if isinstance(node, TimeWindowNode) else node.id
            for node in self.graph.graph_processor.target_nodes
        }"""
        
        # Chỉ giữ lại các node hợp lệ trong trace của AGV
        if temp_trace:
            temp_trace = self.trim_trace_to_target(temp_trace, target_node_ids)
            self.agv.set_traces(temp_trace)
        
        # Cập nhật phiên bản của đồ thị cho AGV
        self.agv.version_of_graph = self.graph.version
        self.update_target_node(self.agv, target_node_ids)

        # Thiết lập traces cho tất cả các AGVs khác
        global allAGVs
        #pdb.set_trace()
        #if len(allAGVs) == 0 or allAGVs is None:
        #    pdb.set_trace()
        for agv in allAGVs:
            if agv.id != self.agv.id: #and agv.version_of_graph < self.graph.version:
                temp_trace = self.graph.getTrace(agv)
                if temp_trace:
                    temp_trace = self.trim_trace_to_target(temp_trace, target_node_ids)
                    agv.set_traces(temp_trace)
                agv.version_of_graph = self.graph.version
                self.update_target_node(agv, target_node_ids)

    def trim_trace_to_target(self, trace, target_node_ids):
        original_ids = [str(node.id) for node in trace]
        ids_str = " -> ".join(original_ids)
        #if(ids_str == "664 -> 728 -> 792 -> 856 -> 920 -> 984 -> 1048 -> 1112 -> 1176 -> 1240 -> 1304 -> 1946"):
        #    pdb.set_trace()
        """ Trim trace to only include nodes leading to the target node. """
        while trace and trace[-1].get_raw_id() not in target_node_ids:
            trace.pop()
        if(len(trace) == 0):
            print(f"Trace emptied! Original IDs: {ids_str}")
            #pdb.set_trace()
        return trace

    def update_target_node(self, agv, target_node_ids):
        """ Update the target node for the AGV based on current traces. """
        if agv.get_traces():
            target_node = agv.get_traces()[-1]
        else:
            target_node = agv.target_node
        
        if target_node and (target_node.get_raw_id() in target_node_ids or target_node.id in target_node_ids):
            agv.target_node = self.graph.graph_processor.get_target_by_id(target_node.id)

def get_largest_id_from_map(filename):
    largest_id = 0
    with open(filename, "r") as file:
        for line in file:
            parts = line.strip().split()
            if parts[0] == "a":  # Assuming arcs start with 'a'
                # Parse the node IDs from the arc definition
                id1, id2 = int(parts[1]), int(parts[2])
                largest_id = max(largest_id, id1, id2)
    return largest_id
