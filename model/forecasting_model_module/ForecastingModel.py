from pyscipopt import Model, quicksum
import config
# Additional function to track running time
import time
import datetime
import os
import pdb

time_start = time.time()


class DimacsFileReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.problem_info = {}
        self.supply_nodes_dict = {}
        self.demand_nodes_dict = {}
        self.zero_nodes_dict = {}
        self.arc_descriptors_dict = {}
        self.earliness_tardiness_dict = {}

    def read_dimacs_file(self, file_path):
        self.problem_info = {}
        node_descriptors = []
        arc_descriptors = []
        comment_lines = []

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip().split(' ')
                if line[0] == 'c':
                    self.handle_comment(line, comment_lines)
                elif line[0] == 'p':
                    self.handle_problem_line(line)
                elif line[0] == 'n':
                    self.handle_node_descriptor(line, node_descriptors)
                elif line[0] == 'a':
                    self.handle_arc_descriptor(line, arc_descriptors)

        return node_descriptors, arc_descriptors, comment_lines

    def handle_comment(self, line, comment_lines):
        comment_lines.append(line)

    def handle_problem_line(self, line):
        _, problem_type, num_nodes, num_arcs = line
        self.problem_info['type'] = problem_type
        self.problem_info['num_nodes'] = int(num_nodes)
        self.problem_info['num_arcs'] = int(num_arcs)

    def handle_node_descriptor(self, line, node_descriptors):
        _, node_id, flow = line
        node_descriptors.append((int(node_id), int(flow)))

    def handle_arc_descriptor(self, line, arc_descriptors):
        _, src, dst, low, cap, cost = line
        arc_descriptors.append((int(src), int(dst), int(low), int(cap), int(cost)))

    # function to divide the node into supply and demand
    def divide_node(self, node_descriptors_dict, arc_descriptors_dict):
        supply_nodes = {}
        demand_nodes = {}
        zero_nodes = {}
        for node, flow in node_descriptors_dict.items():
            if flow > 0:
                supply_nodes[node] = flow
            elif flow < 0:
                demand_nodes[node] = flow

        for node in arc_descriptors_dict:
            if node[0] not in supply_nodes and node[0] not in demand_nodes and node[0] not in zero_nodes:
                zero_nodes[node[0]] = 0
            if node[1] not in supply_nodes and node[1] not in demand_nodes and node[1] not in zero_nodes:
                zero_nodes[node[1]] = 0

        return supply_nodes, demand_nodes, zero_nodes

    # function to sort all dictionary
    def sort_all_dicts(self, supply_nodes_dict, demand_nodes_dict, zero_nodes_dict, arc_descriptors_dict):
        # sort supply_nodes_dict by node_id from smallest to largest
        supply_nodes_dict = dict(sorted(supply_nodes_dict.items(), key=lambda item: item[0]))

        # sort demand_nodes_dict by node_id from smallest to largest
        demand_nodes_dict = dict(sorted(demand_nodes_dict.items(), key=lambda item: item[0]))

        # sort zero_nodes_dict by node_id from smallest to largest
        zero_nodes_dict = dict(sorted(zero_nodes_dict.items(), key=lambda item: item[0]))

        # sort arc_descriptors_dict by src from smallest to largest, then by dst from smallest to largest
        arc_descriptors_dict = dict(sorted(arc_descriptors_dict.items(), key=lambda item: (item[0][0], item[0][1])))

        return supply_nodes_dict, demand_nodes_dict, zero_nodes_dict, arc_descriptors_dict

    def read_custom_dimacs(self):  # call the previous function with additional parameter
        # Custom line for earliness-tardiness problem
        #  format: c tw <demand_node> <earliness> <tardiness>
        self.earliness_tardiness_dict = {}
        node_descriptors, arc_descriptors, comment_lines = self.read_dimacs_file(self.file_path)

        for line in comment_lines:  # line is a list eg, ['c', 'tw', '1', '0', '0']
            if line[1] == 'tw':
                _, _, node_id, earliness, tardiness = line
                self.earliness_tardiness_dict[int(node_id)] = (int(earliness), int(tardiness))

        # sort the node_descriptors and arc_descriptors to dictionary
        node_descriptors_dict = {}
        for i in node_descriptors:
            node_id = i[0]
            flow = i[1]
            node_descriptors_dict[node_id] = flow

        arc_descriptors_dict = {}
        for i in arc_descriptors:
            src = i[0]
            dst = i[1]
            low = i[2]
            cap = i[3]
            cost = i[4]
            arc_descriptors_dict[(src, dst)] = (low, cap, cost)

        # divide node into supply, demand, zero
        self.supply_nodes_dict, self.demand_nodes_dict, self.zero_nodes_dict = self.divide_node(node_descriptors_dict,
                                                                                                arc_descriptors_dict)

        # sort all dictionaries
        self.supply_nodes_dict, self.demand_nodes_dict, self.zero_nodes_dict, self.arc_descriptors_dict = self.sort_all_dicts(
            self.supply_nodes_dict, self.demand_nodes_dict, self.zero_nodes_dict, arc_descriptors_dict)

    def get_all_dicts(self):
        return self.problem_info, self.supply_nodes_dict, self.demand_nodes_dict, self.zero_nodes_dict, self.arc_descriptors_dict, self.earliness_tardiness_dict


# model class
class ForecastingModel:
    def __init__(self, problem_info, supply_nodes_dict, demand_nodes_dict, zero_nodes_dict, arc_descriptors_dict,
                 earliness_tardiness_dict):
        self.problem_info = problem_info
        self.model = Model("Minimum Cost Flow Problem")
        self.supply_nodes_dict = supply_nodes_dict  # {node_id(int): supply(int)}
        self.demand_nodes_dict = demand_nodes_dict  # {node_id(int): demand(int)}
        self.zero_nodes_dict = zero_nodes_dict  # {node_id(int): 0}
        self.arc_descriptors_dict = arc_descriptors_dict  # {(src(int), dst(int)): (low(int), cap(int), cost(int))}
        self.earliness_tardiness_dict = earliness_tardiness_dict  # {node_id(int): (earliness(int), tardiness(int))}
        self.z_vars = None
        self.solve_time = None
        self.create_model()
        self.add_constraints()
        self._graph = None
    
    @property
    def graph(self):
        return self._graph
    
    @graph.setter
    def graph(self, value):
        self._graph = value
    

    def create_model(self):
        self.vars_dict_index_i = {}
        self.vars_dict_index_j = {}
        
        self.create_arc_variables()
        self.create_earliness_tardiness_variables()
        
        self.all_vars = self.model.getVars()
        self.all_vars_dict = {var.name: var for var in self.all_vars}
        
        self.cost_dict = self.create_cost_dictionary()

    def create_arc_variables(self):
        for supply_node in self.supply_nodes_dict:
            for (i, j), _ in self.arc_descriptors_dict.items():
                var_name = f"x{supply_node}_{i}_{j}"
                self.vars_dict_index_i.setdefault(i, []).append(var_name)
                self.vars_dict_index_j.setdefault(j, []).append(var_name)

                self.model.addVar(vtype="B", name=var_name)

    def create_earliness_tardiness_variables(self):
        if self.earliness_tardiness_dict:
            self.z_vars = {}
            self.z_vars_tw = {}
            z_vars_TW_E = {}
            z_vars_TW_T = {}

            for supply_node in self.supply_nodes_dict:
                z_var_name = f"z{supply_node}"
                self.z_vars[supply_node] = self.model.addVar(vtype="I", name=z_var_name)
                for demand_node, (earliness, tardiness) in self.earliness_tardiness_dict.items():
                    z_var_name_tw_e = f"z{supply_node}TW{demand_node}E"
                    z_var_name_tw_t = f"z{supply_node}TW{demand_node}T"
                    z_vars_TW_E[(supply_node, demand_node)] = self.model.addVar(vtype="C", name=z_var_name_tw_e)
                    z_vars_TW_T[(supply_node, demand_node)] = self.model.addVar(vtype="C", name=z_var_name_tw_t)

            for supply_node in self.supply_nodes_dict:
                for demand_node, (earliness, tardiness) in self.earliness_tardiness_dict.items():
                    self.z_vars_tw[(supply_node, demand_node)] = (
                        z_vars_TW_E[(supply_node, demand_node)], 
                        z_vars_TW_T[(supply_node, demand_node)]
                    )

    def create_cost_dictionary(self):
        cost_dict = {}
        for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items():
            for supply_node in self.supply_nodes_dict:
                var_name = f"x{supply_node}_{i}_{j}"
                cost_dict[var_name] = cost
        return cost_dict

    def add_constraints(self):
        self.add_capacity_constraints()
        self.add_supply_node_constraints()
        self.add_demand_node_constraints()
        self.add_zero_node_constraints()
        self.add_supply_node_traffic_flow_constraints()
        self.add_demand_node_traffic_flow_constraints()
        self.add_earliness_tardiness_constraints()

    def add_capacity_constraints(self):
        """ Constraint 1: Limit the flow of each arc to its capacity """
        for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items():
            lst = [self.all_vars_dict[f"x{supply_node}_{i}_{j}"] for supply_node in self.supply_nodes_dict]
            self.model.addCons(quicksum(lst) <= cap)

    def add_supply_node_constraints(self):
        """ Constraint 2: Sum of all arcs out of each supply node must equal 1 """
        for supply_node in self.supply_nodes_dict:
            arc_out = [f"x{supply_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() if i == supply_node]
            self.model.addCons(quicksum(self.all_vars_dict[var] for var in arc_out) == 1)

    def add_demand_node_constraints(self):
        """ Constraint 3: Sum of all arcs into each demand node must equal 1 """
        for demand_node in self.demand_nodes_dict:
            arc_in = [f"x{supply_node}_{i}_{j}" for supply_node in self.supply_nodes_dict for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() if j == demand_node]
            self.model.addCons(quicksum(self.all_vars_dict[var] for var in arc_in) == 1)

    def add_zero_node_constraints(self):
        """ Constraint 4: Flow into zero nodes must equal flow out of zero nodes """
        for zero_node in self.zero_nodes_dict:
            for supply_node in self.supply_nodes_dict:
                arc_in = [f"x{supply_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() if j == zero_node]
                arc_out = [f"x{supply_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() if i == zero_node]
                self.model.addCons(quicksum(self.all_vars_dict[var] for var in arc_in) == quicksum(self.all_vars_dict[var] for var in arc_out))

    def add_supply_node_traffic_flow_constraints(self):
        """ Constraint 5: Traffic flow for supply nodes """
        for supply_node in self.supply_nodes_dict:
            arc_in = [f"x{vehicle_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() for vehicle_node in self.supply_nodes_dict if j == supply_node]
            arc_out = [f"x{vehicle_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() for vehicle_node in self.supply_nodes_dict if i == supply_node]
            self.model.addCons(1 + quicksum(self.all_vars_dict[var] for var in arc_in) == quicksum(self.all_vars_dict[var] for var in arc_out))

    def add_demand_node_traffic_flow_constraints(self):
        """ Constraint 6: Traffic flow for demand nodes """
        for demand_node in self.demand_nodes_dict:
            arc_in = [f"x{supply_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() for supply_node in self.supply_nodes_dict if j == demand_node]
            arc_out = [f"x{supply_node}_{i}_{j}" for (i, j), (low, cap, cost) in self.arc_descriptors_dict.items() for supply_node in self.supply_nodes_dict if i == demand_node]
            self.model.addCons(quicksum(self.all_vars_dict[var] for var in arc_in) == 1 + quicksum(self.all_vars_dict[var] for var in arc_out))

    def add_earliness_tardiness_constraints(self):
        """ Constraint 7: Handle earliness and tardiness variables """
        if self.earliness_tardiness_dict:
            for supply_node in self.supply_nodes_dict:
                z_var = self.z_vars[supply_node]
                supply_node_vars = [var for var in self.all_vars if f"x{supply_node}_" in var.name]
                self.model.addCons(z_var == quicksum(self.cost_dict[var.name] * var for var in supply_node_vars))

            for (supply_node, demand_node), (z_var_tw_e, z_var_tw_t) in self.z_vars_tw.items():
                z_var = self.z_vars[supply_node]
                z_vars_src_dst = {var.name: var for var in self.all_vars if f"x{supply_node}_" in var.name and var.name.endswith(str(demand_node))}
                earliness, tardiness = self.earliness_tardiness_dict[demand_node]
                vars_sum = quicksum(z_vars_src_dst.values())
                self.model.addCons(z_var_tw_t >= 0)
                self.model.addCons(z_var_tw_e >= 0)
                self.model.addCons(z_var_tw_t >= (z_var - tardiness) * vars_sum)
                self.model.addCons(z_var_tw_e >= (earliness * vars_sum) - z_var)




    def solve(self):
        config.totalSolving += 1
        if self.z_vars is not None:
            alpha = 1
            beta = 1
            # quick sum z_vars and multiply with alpha
            alpha_sum = quicksum(alpha * z_var for z_var in self.z_vars.values())

            # quick sum z_vars_TW_E and z_vars_TW_T and multiply with beta
            beta_sum = quicksum(
                beta * z_var_tw for (_, _), (z_var_tw_e, z_var_tw_t) in self.z_vars_tw.items() for z_var_tw in
                (z_var_tw_e, z_var_tw_t))

            self.model.setObjective(alpha_sum + beta_sum, "minimize")
        else:
            self.model.setObjective(quicksum(
                self.arc_descriptors_dict[(i, j)][2] * self.all_vars_dict[f"x{supply_node}_{i}_{j}"] for supply_node in
                self.supply_nodes_dict for (i, j) in self.arc_descriptors_dict), "minimize")

        self.model.hideOutput()
        self.model.optimize() 
        self.solve_time = self.model.getSolvingTime()
        self.total_time = self.model.getTotalTime()
        config.timeSolving += self.total_time
        self.reading_time = self.model.getReadingTime()
        self.presolving_time = self.model.getPresolvingTime()

    def output_solution(self):
        if self.model.getStatus() == "optimal":
            pass
        else:
            print("No solution found")
            #pdb.set_trace()
            #pass

    def save_solution(self, filename, dirname):
        # check if output folder exists
        folder = dirname
        if not os.path.exists(folder):
            os.makedirs(folder)

        # generate filename base on file input and current time(DD-MM-YYYY_HH-MM-SS)
        main_filename = filename.split(".")[0]
        self.datetime_info = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = main_filename + "_" + self.datetime_info + ".log"
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w') as f:
            if self.model.getStatus() == "optimal":
                f.write("Run time: " + str(time.time() - time_start) + " SEC\n")
                f.write("Solver time: " + str(self.solve_time) + "\n")
                f.write("Total time: " + str(self.total_time) + "\n")
                f.write("Reading time: " + str(self.reading_time) + "\n")
                f.write("Presolving time: " + str(self.presolving_time) + "\n")
                f.write("Optimal value: " + str(self.model.getObjVal()) + "\n")
                f.write("Solution:\n")
                # Lấy tất cả các biến từ mô hình
                vars = self.model.getVars()
                # In giá trị của tất cả các biến
                for var in vars:
                    if self.model.getVal(var) > 0:
                        f.write(f"{var.name} = {self.model.getVal(var)}\n")
            else:
                f.write("No solution found")

    def create_traces(self, filepath, graph_version):
        """ Main function to create and write traces based on optimal solution. """
        self.check_time_limit()
        
        if self.model.getStatus() == "optimal":
            tmp_traces = self.parse_variables_to_traces()
            
            if self.graph.graph_processor.print_out:
                self.print_traces_summary(tmp_traces)

            traces = self.sort_and_construct_traces(tmp_traces)
            self.write_traces_to_file(traces, filepath)

    def check_time_limit(self):
        """ Checks and logs if the process has taken too long. """
        import time
        milliseconds = int(round(time.time())) 
        seconds = milliseconds / (1000 * 1000)
        if (seconds > 60 * 100):
            print(seconds/(60*100))

    def parse_variables_to_traces(self):
        """ Parse variables to build initial traces. """
        vars = self.model.getVars()
        tmp_traces = {}

        for var in vars:
            if self.model.getVal(var) > 0 and var.name.startswith("x"):
                parts = var.name.split("_")
                agvID, i, j = parts[0], int(parts[1]), int(parts[2])
                cost = int(self.cost_dict[var.name])
                tmp_traces.setdefault(agvID, []).append((i, j, cost))

        return tmp_traces

    def print_traces_summary(self, tmp_traces):
        """ Print a summary of traces for debugging and verification purposes. """
        print("====>")
        for key in tmp_traces.keys():
            print(f"\t {key}: {tmp_traces[key]}", end='')
            last = tmp_traces[key][-1][0]
            M = self.graph.graph_processor.M
            real_last = last % M if last % M != 0 else M
            first = tmp_traces[key][0][0]
            if first in self.graph.nodes and self.graph.nodes[first].agv is not None:
                print(f"{self.graph.nodes[first].agv.id} gonna reach", end='')
            print(f" Last = {real_last}")

    def sort_and_construct_traces(self, tmp_traces):
        """ Sort traces and construct final trace paths. """
        # Sort initial traces by starting node `i`
        for agvID in tmp_traces:
            tmp_traces[agvID].sort(key=lambda x: x[0])

        traces = {agvID: [tmp_traces[agvID][0]] for agvID in tmp_traces}

        for agvID in tmp_traces:
            for i in range(len(tmp_traces[agvID])):
                for arc in tmp_traces[agvID]:
                    if i < len(traces[agvID]):
                        try:
                            if traces[agvID][i][1] == arc[0]:
                                traces[agvID].append(arc)
                                break
                        except IndexError as e:
                            print(f"IndexError: {e}")

        return traces

    def write_traces_to_file(self, traces, filepath):
        """ Write the final traces to the specified file. """
        cost = 0
        with open(filepath, "w") as file:
            for agvID in traces:
                for trace in traces[agvID]:
                    file.write(f"a {trace[0]} {trace[1]}    {cost}  +  {trace[2]}  =  {cost + trace[2]}\n")
                    cost += trace[2]

    def get_problem_info(self):
        return self.problem_info

    def get_solution(self):
        if self.model.getStatus() == "optimal":
            return self.model.getObjVal(), self.model.getVars()
        else:
            return None

    def get_solution_dict(self):
        if self.model.getStatus() == "optimal":
            return {var.name: self.model.getVal(var) for var in self.model.getVars()}
        else:
            return None
