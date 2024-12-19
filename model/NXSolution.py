import networkx as nx
import pdb
import config
from collections import defaultdict

class NetworkXSolution:
    def __init__(self):#, edges_with_costs, startednodes, targetnodes):
        self.startednodes = None #startednodes
        self.targetnodes = None #targetnodes
        self.edges_with_costs = None #edges_with_costs
        self.flowCost = 0
        self.flowDict = defaultdict(list)
        self.M = 0
    
    def read_dimac_file(self, file_path):
        G = nx.DiGraph()
        #pdb.set_trace()
        countDemands = 0
        posList = []
        negList = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()
                if parts[0] == 'n':
                    ID = parts[1]
                    demand = (-1)*int(parts[2])
                    countDemands += 1
                    if demand > 0:
                        posList.append(demand)
                    else:
                        negList.append(demand)
                    G.add_node(ID, demand = demand)
                elif parts[0] == 'a':
                    ID1 = (parts[1])
                    ID2 = (parts[2])
                    U = int(parts[4])
                    C = int(parts[5])
                    G.add_edge(ID1, ID2, weight=C, capacity=U)
        import time
        start_time = time.time()
        #print("=============> Demands ", countDemands)
        #if(countDemands == 8):
        #    pdb.set_trace()
        #    print(posList)
        #    print(negList)
        self.flowCost, self.flowDict = nx.network_simplex(G)
        end_time = time.time()
        config.timeSolving += (end_time - start_time)
        config.totalSolving += 1
    def write_trace(self, file_path = 'traces.txt'):
        #pdb.set_trace()
        filtered_data = {}
        for key, sub_dict in self.flowDict.items():
            # Lọc các phần tử có giá trị khác 0
            filtered_sub_dict = {k: v for k, v in sub_dict.items() if v != 0}
            if filtered_sub_dict:
                filtered_data[key] = filtered_sub_dict
        self.flowDict = filtered_data

        with open(file_path, "w") as file:
            for key, value in self.flowDict.items():
                for inner_key, inner_value in value.items():
                    if(inner_value > 0):
                        s = int(key) // self.M + (self.M if int(key) // self.M == 0 else 0)
                        t = int(inner_key) // self.M + (self.M if int(inner_key) // self.M == 0 else 0)
                        cost = self.edges_with_costs.get((s, t), [-1, -1])[1]
                        result = inner_value*cost
                        #print(f"a {key} {inner_key} 0 + {result} = {result}")
                        file.write(f"a {key} {inner_key} 0 + {result} = {result}\n")
