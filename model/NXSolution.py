import networkx as nx
import pdb
import config
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class NetworkXSolution:
    def __init__(self):#, edges_with_costs, startednodes, targetnodes):
        self.startednodes = None #startednodes
        self.targetnodes = None #targetnodes
        self.edges_with_costs = None #edges_with_costs
        self.flowCost = 0
        self.flowDict = defaultdict(list)
        self.M = config.M
    
    def plot_graph_3d_interactive(self, G):
        if(config.draw == 0):
            return
        pos = nx.spring_layout(G, dim=3)
        
        my_dict = {}
        for key, value in self.flowDict.items():
            for inner_key, inner_value in value.items():
                if(inner_value > 0):
                    my_dict[(key, inner_key)] = 1
        edge_trace = []
        for edge in G.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_trace.append(go.Scatter3d(
                x=[x0, x1, None], y=[y0, y1, None], z=[z0, z1, None],
                mode='lines',
                line=dict(color='red' if (edge[0], edge[1]) in my_dict else ('yellow' if (int(edge[1]) - int(edge[0])) == self.M else 'black'), width=2),
                hoverinfo='none'
            ))
        #pdb.set_trace()
        color_map = {
            -1: 'red',
            0: 'blue',
            1: 'green'
        }
        #node_colors = ['red' if G.nodes[node].get('demand', 0) == -1 else  else 'blue' for node in G.nodes()]
        node_colors = [color_map[G.nodes[node].get('demand', 0)] for node in G.nodes()]
        node_trace = go.Scatter3d(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            z=[pos[node][2] for node in G.nodes()],
            mode='markers+text',
            #marker=dict(size=10, color='blue'),
            marker=dict(size=10, color=node_colors),
            text=[str(node) for node in G.nodes()],
            hoverinfo='text'
        )
        # Tạo bảng
        table_trace = go.Table(
            header=dict(values=['Edge: Lower Bound/Upper Bound/Cost']),
            cells=dict(values=[
                [f"({edge[0]}, {edge[1]}): 0/{G.edges[edge].get('capacity', 0)}/{G.edges[edge].get('weight', 0)}" for edge in G.edges()]
                ])
        )
        #fig = go.Figure(data=edge_trace + [node_trace, table_trace])
        # Tạo subplot với hai cột
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.2, 0.8],
            specs=[[{"type": "table"}, {"type": "scatter3d"}]]
            )
        
        fig.add_trace(table_trace, row=1, col=1)
        fig.add_trace(node_trace, row=1, col=2)
        for trace in edge_trace:
            fig.add_trace(trace, row=1, col=2)
        fig.update_layout(showlegend=False, title = 'Vẽ đồ thị cho tôi:',\
            title_text='3D Graph Visualization')
        fig.show()

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
        self.flowCost, self.flowDict = nx.network_simplex(G)
        end_time = time.time()
        config.timeSolving += (end_time - start_time)
        config.totalSolving += 1
        filtered_data = {}
        for key, sub_dict in self.flowDict.items():
            # Lọc các phần tử có giá trị khác 0
            filtered_sub_dict = {k: v for k, v in sub_dict.items() if v != 0}
            if filtered_sub_dict:
                filtered_data[key] = filtered_sub_dict
        self.flowDict = filtered_data
        self.plot_graph_3d_interactive(G)
        
    def write_trace(self, file_path = 'traces.txt'):
        #pdb.set_trace()

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
