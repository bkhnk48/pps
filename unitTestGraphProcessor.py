from model.Graph import Graph#, graph
from model.AGV import AGV
from model.Event import Event, debug
from controller.EventGenerator import StartEvent
from model.Graph import Graph
from controller.NodeGenerator import TimeWindowNode
from controller.NodeGenerator import RestrictionNode 
from controller.EdgeGenerator import TimeWindowEdge
from controller.EdgeGenerator import RestrictionEdge
import config
from controller.GraphProcessor import GraphProcessor
import subprocess
import sys
import pdb

def assert_Nodes(graph, current_time):
    M = graph.number_of_nodes_in_space_graph
    count = 0
    numOfNodes = max(graph.nodes, key=int) + 1 #because it includes 0
    descrease = 0
    for i in range(0, numOfNodes):
        if not (i in graph.nodes.keys()):
            #if (i // M - (1 if i % M == 0 else 0)) < current_time:
            descrease += 1
    for node in graph.nodes.values():
        if isinstance(node, (TimeWindowNode, RestrictionNode)):
            descrease += 1
    
    numOfNodes = numOfNodes - descrease

    for node in graph.nodes.values():
        if not isinstance(node, (TimeWindowNode, RestrictionNode)):
            time = node.id // M - (1 if node.id % M == 0 else 0)
            count += 1 if time >= current_time else 0
            """if time >= current_time:
                #print(node.id, end = " ")
                group.append(node.id)
    group.sort()
    print(group)"""
    assert_msg = f"Assertion failed as number of nodes which satisfies time >= {current_time} is {count} while it should be {numOfNodes}"
    assert count == numOfNodes, assert_msg


def assert_Edges(graph, current_time):
    M = graph.number_of_nodes_in_space_graph
    for source_id, edges in graph.adjacency_list.items():
        for destination_id, edge in edges:
            if not isinstance(edge, (TimeWindowEdge, RestrictionEdge)):
                time = source_id // M - (1 if source_id % M == 0 else 0)
                assert time >= current_time, f"Edge from {edge.start_node.id} to {edge.end_node.id} does not meet the constraint."

def assert_connection_TimeWindowNodes(graph):
    # Giả sử 'graph' là đối tượng đồ thị của bạn
    for node in graph.nodes.values():
        count = 0
        # Kiểm tra nếu node là TimeWindowNode
        if isinstance(node, TimeWindowNode):
            # Kiểm tra nếu có ít nhất một cạnh nối đến node
            for start_node in graph.nodes.values():
                if(start_node != node):
                    for end_id, edge in list(graph.adjacency_list[start_node.id]):
                        if(end_id == node.id):
                            count += 1
            assert(count > 0), f"TimeWindowNode with id {node.id} has no incoming edges"


def assert_number_TimeWindowEdges(graph, current_time):
    old_time_window_edges = []
    for source_id, edges in graph.adjacency_list.items():
        for destination_id, edge in edges:
            if isinstance(edge, TimeWindowEdge):
                old_time_window_edges.append(edge)
    M = graph.number_of_nodes_in_space_graph
    new_time_window_edges = [edge for edge in old_time_window_edges if (edge.start_node.id // M - (1 if edge.start_node.id % M == 0 else 0)) >= current_time]

    old_edges_count = len(old_time_window_edges)
    new_edges_count = len(new_time_window_edges)
    invalid_edges_count = len([edge for edge in old_time_window_edges if (edge.start_node.id // M - (1 if edge.start_node.id % M == 0 else 0)) < current_time])

    assert new_edges_count == old_edges_count - invalid_edges_count, "Number of new TimeWindowEdges does not meet the constraint"

def assert_RestrictionNodes(graph):
    for node in graph.nodes.values():
        if isinstance(node, RestrictionNode):
            assert len(graph.adjacency_list[node.id]) > 0, f"RestrictionNode with id {node.id} has no incoming edges"

def assert_new_RestrictionNodes(graph):
    old_time_window_edges = []
    for source_id, edges in graph.adjacency_list.items():
        for destination_id, edge in edges:
            if isinstance(edge, TimeWindowEdge):
                old_time_window_edges.append(edge)

    M = graph.number_of_nodes_in_space_graph
    
    old_restriction_edges = [edge for edge in old_time_window_edges if isinstance(edge, RestrictionEdge) and not isinstance(edge.start_node, RestrictionNode)]
    new_restriction_edges = [edge for edge in old_restriction_edges if (edge.start_node.id // M - (1 if edge.start_node.id % M == 0 else 0)) >= current_time]
    
    old_restriction_edges_with_time_less_than_current = [
        edge for edge in old_restriction_edges 
        if (edge.start_node.id // M - (1 if edge.start_node.id % M == 0 else 0)) < current_time
    ]
    
    assert len(new_restriction_edges) == (len(old_restriction_edges) - len(old_restriction_edges_with_time_less_than_current)), \
    "Number of new RestrictionEdges with non-RestrictionNode start nodes does not meet the constraint"

def assert_numberOf_RestrictionNodes(graph):
    M = graph.number_of_nodes_in_space_graph
    # Lấy danh sách các TimeWindowEdge
    old_time_window_edges = []
    for source_id, edges in graph.adjacency_list.items():
        for destination_id, edge in edges:
            if isinstance(edge, TimeWindowEdge):
                old_time_window_edges.append(edge)
    
    # Lấy danh sách các RestrictionEdge cũ (có đỉnh đích không phải RestrictionNode)
    old_restriction_edges = [
        edge for edge in old_time_window_edges 
        if isinstance(edge, RestrictionEdge) and not isinstance(edge.end_node, RestrictionNode)
    ]
    
    # Lấy danh sách các RestrictionEdge mới (có đỉnh đích không phải RestrictionNode) 
    # với thời điểm của đỉnh đích >= thời điểm hiện tại
    new_restriction_edges = [
        edge for edge in old_restriction_edges 
        if (edge.end_node.id // M - (1 if edge.end_node.id % M == 0 else 0)) >= current_time
    ]
    
    # Lấy danh sách các RestrictionEdge cũ (có đỉnh đích không phải RestrictionNode) 
    # với thời điểm của đỉnh đích < thời điểm hiện tại
    old_edges_with_time_less_than_current = [
        edge for edge in old_restriction_edges 
        if (edge.end_node.id // M - (1 if edge.end_node.id % M == 0 else 0)) < current_time
    ]
    
    # Kiểm tra số lượng các RestrictionEdge mới có đúng bằng số lượng các RestrictionEdge cũ 
    # trừ đi số lượng các RestrictionEdge có thời điểm của đỉnh đích < thời điểm hiện tại hay không
    assert len(new_restriction_edges) == len(old_restriction_edges) - len(old_edges_with_time_less_than_current), \
        "Number of new RestrictionEdges with non-RestrictionNode end nodes does not meet the constraint"
    

processor = GraphProcessor()
print("Test cho file 2ndSimple.txt")
processor.print_out = False
filepath = "2ndSimple.txt"
processor.started_nodes = [1, 10]
processor.process_input_file(filepath)
processor.H = 10
processor.generate_hm_matrix()
processor.d = 2
processor.generate_adj_matrix()
processor.create_tsg_file()
count = 0
while(count <= 1):
    processor.ID = 3
    processor.earliness = 4 if count == 0 else 7
    processor.tardiness = 6 if count == 0 else 9
    processor.alpha = 1
    processor.beta = 1
    processor.add_time_windows_constraints()
    count += 1
processor.gamma = 1
processor.restriction_count = 1
processor.start_ban = 2
processor.end_ban = 5
processor.restrictions = [[2, 3]]
processor.ur = 1
processor.process_restrictions()

graph = Graph(processor)
#pdb.set_trace()
processor.init_nodes_n_edges(graph)
assert (graph.count_edges() == len(processor.tsedges)), "Missing some edges elsewhere"
assert (len(graph.nodes) == len(processor.ts_nodes)), f"Missing some nodes elsewhere as {len(graph.nodes)} != {len(processor.ts_nodes)}"

id1 = 1
id2 = 8
c12 = 3
processor.update_graph(id1, id2, c12)
current_time = id1 // processor.M + c12
#pdb.set_trace()

""" Cần có các assert như sau:
(1) Tất cả các Node (không kể các TimeWindowNode và RestrictionNode) mà có time >= thời điểm hiện tại* thì bằng 27"""
assert_Nodes(graph, current_time)
"""(2) Tất cả các Edge (không kể các TimeWindowEdge và RestrictionEdge) thì đỉnh nguồn của chúng phải có time >= thời điểm hiện tại*"""
assert_Edges(graph, current_time)

"""
(3) Tất cả các TimeWindowNode thì vẫn còn các đỉnh khác nối đến chúng"""
assert_connection_TimeWindowNodes(graph)

"""(4) Tất cả các RestrictionNode thì vẫn còn đỉnh nối đến chúng"""
assert_RestrictionNodes(graph)

"""(5) Số các TimeWindowNode sẽ bằng 2"""
time_window_nodes = [node for node in graph.nodes.values() if isinstance(node, TimeWindowNode)]
assert len(time_window_nodes) == 2, "Number of TimeWindowNodes is not equal to 2"

"""(6) Số các TimeWindowEdge mới sẽ bằng số TimeWindowsEdge cũ trừ đi số TimeWindowEdge có đỉnh nguồn với thời điểm của 
đỉnh nguồn < thời điểm hiện tại"""
assert_number_TimeWindowEdges(graph, current_time)

# (7) Số các RestrictionEdge mới (có đỉnh nguồn không phải RestrictionNode) sẽ bằng số RestrictionEdge 
# (có đỉnh nguồn không phải RestrictionNode) cũ trừ đi số RestrictionEdge có đỉnh nguồn (không phải RestrictionNode) với 
# thời điểm của đỉnh nguồn < thời điểm hiện tại
assert_new_RestrictionNodes(graph)

"""
(8) Số các RestrictionEdge mới (có đỉnh đích không phải RestrictionNode) sẽ bằng số
     RestrictionEdge (có đỉnh đích không phải RestrictionNode) cũ trừ đi 
     số RestrictionEdge có đỉnh đích (không phải RestrictionNode) với thời điểm của đỉnh đích < thời điểm hiện tại     
*thời điểm hiện tại: có công thức tính thời điểm hiện tại từ tham số của hàm update_file 
"""
assert_numberOf_RestrictionNodes(graph)
