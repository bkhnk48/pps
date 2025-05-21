from controller.GraphProcessor import GraphProcessor
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
import networkx as nx
from unittest.mock import patch
from model.Graph import Graph


def read_dimac_file(file_path = "TSG.txt"):
    TSG = list()
    virtual_node = set()
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if parts[0] == 'c' and len(parts) == 5:
                virtual_node.add(int(parts[2]))
            if parts[0] == 'n' and len(parts) == 3 and int(parts[2]) == -1:
                virtual_node.add(int(parts[1]))
            if parts[0] == 'a':
                ID1 = int(parts[1])
                ID2 = int(parts[2])
                if ID1 in virtual_node or ID2 in virtual_node:
                    continue
                L = int(parts[3])
                U = int(parts[4])
                C = int(parts[5])
                TSG.append((ID1, ID2,L, U, C))
    print(virtual_node)
    return TSG
result = 4


graph_processor = GraphProcessor() 
with patch('builtins.input' , side_effect=["QuardNodes.txt","10" ,"0" , "1","1","1","2 5", "4 1 1 2", "1", "1","","2"]):
    graph_processor.use_in_main()

print(graph_processor.num_max_agvs)
print(graph_processor.target_nodes)
print(graph_processor.started_nodes)

 
restriction = graph_processor.restriction_for_timeframe_controller
TSG = read_dimac_file("TSG.txt")   

omega = restriction.identify_restricted_edges( [[4,1],[1,2]] , 2, 5 )
print(omega) 
restriction_nodes = restriction.indentify_restricted_nodes( omega )
incoming_capacity_for_restricted_nodes = restriction.calculate_incoming_capacity_for_restricted_nodes( TSG, restriction_nodes)
print(incoming_capacity_for_restricted_nodes)
outgoing_capacity_for_restricted_nodes = restriction.calculate_outgoing_capacity_for_restricted_nodes( TSG , restriction_nodes)
print(outgoing_capacity_for_restricted_nodes)
max_flow = restriction.calulate_max_flow( omega , incoming_capacity_for_restricted_nodes , outgoing_capacity_for_restricted_nodes )
assert max_flow == result, f"Max flow should be {result}, but got {max_flow}"
print(f"Test passed! Max flow is {max_flow}")