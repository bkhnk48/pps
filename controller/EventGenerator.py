from model.Event import Event
import inspect
import pdb
import config
class HaltingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, start_node, end_node, delta_t, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        self.start_node = start_node
        self.end_node = end_node
        self.delta_t = delta_t
        #pdb.set_trace()
        current_frame = inspect.currentframe()
        # Lấy tên của hàm gọi my_function
        caller_name = inspect.getframeinfo(current_frame.f_back).function
        if(self.graph.graph_processor.print_out):
            print(f'HaltingEvent.py:14 {caller_name}')
        #print(self)

    def updateGraph(self):
        if(self.end_time >= self.graph.H):
            pass

    def calculate_cost_halting(self):
        #pdb.set_trace()
        # Tính chi phí dựa trên thời gian di chuyển thực tế
        cost_increase = float('inf') if(self.end_node != self.agv.target_node.id) else self.end_time - self.start_time
        self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
        return cost_increase

    def re_calculate_halting(self, path):
        cost = 0
        delta_cost = 0
        prev = 0
        M = self.graph.number_of_nodes_in_space_graph 
        D = self.graph.graph_processor.d
        P = len(path)
        for i in range(P):
            node = path[i]
            real_node = node % M + (M if node % M == 0 else 0)
            #pdb.set_trace()
            t2 = node // M - (1 if node % M == 0 else 0)
            t1 = prev // M - (1 if prev % M == 0 else 0)
            delta_cost = self.graph.graph_processor.alpha*(t2 - t1)
            if(i != P - 1):
                #print('===', end='')
                if(i > 0):
                    # print('===', end='')                                                            
                    cost = cost + delta_cost
                    print(f'({delta_cost})===', end='')
                print(f'{real_node}===', end='')
            else:
                delta_cost = (float('inf') if(self.end_node != self.agv.target_node.id) else self.end_time - self.start_time)
                cost = cost + delta_cost
                print(f'({self.delta_t})/({delta_cost})==={real_node}===END. ', end='')
            prev = path[i]
        print(f'Total cost: {cost}. The AGV reaches its destination at {self.end_time}')
    
    def process(self):
        #pdb.set_trace()
        # Thực hiện cập nhật đồ thị khi xử lý sự kiện di chuyển
        #self.updateGraph()
        M = self.graph.graph_processor.M
        start = self.agv.path[0]
        space_start_node = start % M + (M if start % M == 0 else 0)
        space_end_node = self.end_node % M + (M if self.end_node % M == 0 else 0)
        print(
            f"AGV {self.agv.id} moves from {start}({space_start_node}) to {self.end_node}({space_end_node}) but time outs!!!!"
        )
        print(f'Because it left {self.start_node }({self.start_node % M + (M if self.start_node % M == 0 else 0)}) as {self.start_time} and spending {self.delta_t} for moving')
        self.re_calculate_halting(self.agv.path)
        self.calculate_cost_halting()
        print(f"The total cost of {self.agv.id} is {self.agv.cost}")
        config.haltingAGVs = config.haltingAGVs + 1
        #self.getNext()
    
    def __str__(self):
        return f"HaltingEvent for {self.agv.id} because it leaves {self.start_node} at {self.start_time} and its finished time at {self.end_time}"

class HoldingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, duration, graph_processor):
        
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        self.duration = duration
        self.number_of_nodes_in_space_graph = Event.getValue("number_of_nodes_in_space_graph")
        #print(self)

    def updateGraph(self):
        # Calculate the next node based on the current node, duration, and largest ID
        current_node = self.agv.current_node if isinstance(self.agv.current_node, int) else self.agv.current_node.id
        next_node = current_node + (self.duration * self.number_of_nodes_in_space_graph) + 1

        # Check if this node exists in the graph and update accordingly
        if next_node in self.graph.nodes:
            self.graph.update_node(current_node, next_node)
        else:
            #print("Calculated next node does not exist in the graph.")
            pass

    def process(self):
        self.updateGraph()  # Optional, if there's a need to update the graph based on this event
        self.getNext()
        
    def __str__(self):
        return f"HoldingEvent for {self.agv.id} at {self.agv.current_node} in {self.duration}(s)"

from controller.EventGenerator import HaltingEvent
from discrevpy import simulator
from datetime import datetime

class MovingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, start_node, end_node, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        #pdb.set_trace()
        self.start_node = start_node
        self.end_node = end_node
        self.force_quit = False
        #print(self)
        M = self.graph.number_of_nodes_in_space_graph
        t1 = self.start_node // M - (self.graph.graph_processor.d if self.start_node % M == 0 else 0)
        if(t1 != self.start_time):
            if(self.graph.graph_processor.print_out):
                print("Errror")
                
    def __str__(self):
        M = self.graph.number_of_nodes_in_space_graph
        space_start_node = self.start_node % M + (M if self.start_node % M == 0 else 0)
        space_end_node = self.end_node % M + (M if self.end_node % M == 0 else 0)
        now = datetime.now()
        formatted_time = now.strftime("%j-%m-%y:%H-%M-%S")
        return f"\t . Now: {formatted_time}. MovingEvent for {self.agv.id} to move from {self.start_node}({space_start_node}) at {self.start_time} and agv reaches {space_end_node} at {self.end_time}"
      
    def updateGraph(self):
        M = self.graph.number_of_nodes_in_space_graph
        real_end_node = self.calculate_real_end_node(M)

        if real_end_node in self.graph.nodes:
            if self.graph.nodes[real_end_node].agv is not None:
                if self.graph.nodes[real_end_node].agv.id != self.agv.id:
                    self.handle_event(real_end_node, M)
                    return
            
            self.graph.nodes[real_end_node].agv = self.agv

        self.update_agv_nodes(real_end_node)

        if real_end_node != self.end_node:
            self.update_graph_and_traces(real_end_node)

    def calculate_real_end_node(self, M):
        return self.end_time * M + (M if self.end_node % M == 0 else self.end_node % M)

    def handle_event(self, real_end_node, M):
        delta_t = 0
        while True:
            delta_t += 1
            real_end_node += M * delta_t
            if self.end_time + delta_t < self.graph.graph_processor.H:
                if real_end_node in self.graph.nodes and self.graph.nodes[real_end_node].agv is not None:
                    if self.graph.nodes[real_end_node].agv.id != self.agv.id:
                        continue
                new_event = MovingEvent(self.start_time, self.end_time + delta_t, self.agv, self.graph, self.agv.current_node, real_end_node, self.graph_processor)
                break
            else:
                new_event = HaltingEvent(self.end_time, self.graph.graph_processor.H, self.agv, self.graph, self.agv.current_node, real_end_node, delta_t)    
                break                                    
        simulator.schedule(new_event.end_time, new_event.process)
        self.force_quit = True

    def update_agv_nodes(self, real_end_node):
        if self.start_node in self.graph.nodes:
            if self.start_node != real_end_node:
                self.graph.nodes[self.start_node].agv = None
        if self.end_node in self.graph.nodes:
            self.graph.nodes[self.end_node].agv = None

    def update_graph_and_traces(self, real_end_node):
        self.agv.current_node = real_end_node
        self.graph_processor.update_graph(self.start_node, self.end_node, real_end_node, self.agv.id)
        self.agv.update_traces(self.end_node, self.graph.nodes[real_end_node])
        self.graph_processor.reset_agv(real_end_node, self.agv)

    def calculate_cost_moving(self):
        #pdb.set_trace()
        # Tính chi phí dựa trên thời gian di chuyển thực tế
        cost_increase = self.graph.graph_processor.alpha*(self.end_time - self.start_time)
        self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
        return cost_increase

    def process(self):
        if(self.graph.graph_processor.print_out):
            print(self)
        self.calculate_cost_moving()
        # Thực hiện cập nhật đồ thị khi xử lý sự kiện di chuyển
        self.updateGraph()
        if(self.force_quit):
            return
        if(self.graph.graph_processor.print_out):
            print(
                f"AGV {self.agv.id} moves from {self.start_node} to {self.end_node} taking actual time {self.end_time - self.start_time}"
                )
        self.solve()
        #pdb.set_trace()
        next_node = self.graph.nodes[self.agv.current_node]
        new_event = next_node.goToNextNode(self)
        simulator.schedule(new_event.end_time, new_event.process)

from model.AGV import AGV
class ReachingTargetEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, target_node, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        self.target_node = target_node
        node = self.graph.nodes[target_node]
        M = self.graph.number_of_nodes_in_space_graph
        if not hasattr(node, 'earliness'):
            try:
                node = next(node for node in self.graph.graph_processor.get_targets() if node.id == target_node)
                #print(f"Đối tượng Node với id {target_id} được tìm thấy.")
                self.graph.nodes[target_node] = node
            except StopIteration:
                pass
        self.earliness = node.earliness
        self.tardiness = node.tardiness
        #if(self.end_time != time):
        #if(self.agv.id == 'AGV4'):
        #pdb.set_trace()
        t1 = [self.earliness - self.end_time, 0, self.end_time - self.tardiness]
        
        self.last_cost = self.graph.graph_processor.beta*(max(t1))/self.graph.graph_processor.alpha
        if(self.graph.graph_processor.print_out):
            print(f"Last cost: {self.last_cost}")
        self.updateGraph()  # Optional: update the graph if necessary
        #print(self)

    def updateGraph(self):
        # Không làm gì cả, vì đây là sự kiện đạt đến mục tiêu
        self.graph_processor.remove_node_and_origins(self.target_node)
        if(self.agv.path[-1] != self.target_node):
            self.target_node = self.agv.path[-1]
            pdb.set_trace()
        new_target_nodes = [node for node in self.graph.graph_processor.target_nodes if node.id != self.target_node]
        if(len(new_target_nodes) != len(self.graph.graph_processor.target_nodes) - 1):
            pdb.set_trace()
        self.graph.graph_processor.target_nodes = new_target_nodes
        for source_id in self.graph.graph_processor.time_window_controller.TWEdges:
            if(self.graph.graph_processor.time_window_controller.TWEdges[source_id] is not None):
                edges = self.graph.graph_processor.time_window_controller.TWEdges[source_id]
                indices = []
                index = -1
                for e in edges:
                    index = index + 1
                    if(e[0].id == self.target_node):
                        if(index not in indices):
                            indices.append(index)
                indices.reverse()
                for index in indices:
                    #if(index in self.graph.graph_processor.time_window_controller.TWEdges[source_id]):
                    #pdb.set_trace()
                    del self.graph.graph_processor.time_window_controller.TWEdges[source_id][index]

    def calculate_cost_reaching(self):
        # Retrieve the weight of the last edge traversed by the AGV
        if self.agv.previous_node is not None and self.target_node is not None:
            last_edge_weight = self.last_cost
            if last_edge_weight is not None:
                # Calculate cost based on the weight of the last edge
                cost_increase = last_edge_weight
                self.agv.update_cost(cost_increase)
                if(self.graph.graph_processor.print_out):
                    print(
                        f"Cost for reaching target node {self.target_node} is based on last edge weight: {cost_increase}."
                    )
            else:
                if(self.graph.graph_processor.print_out):
                    print("No last edge found; no cost added.")
        else:
            if(self.graph.graph_processor.print_out):
                print("Previous node or target node not set; no cost calculated.")
        return self.agv.cost


    def re_calculate_reaching(self, path):
        cost = 0
        delta_cost = 0
        prev = 0
        M = self.graph.number_of_nodes_in_space_graph 
        D = self.graph.graph_processor.d
        P = len(path)
        for i in range(P):
            node = path[i]
            real_node = node % M + (M if node % M == 0 else 0)
            #pdb.set_trace()
            t2 = node // M - (1 if node % M == 0 else 0)
            t1 = prev // M - (1 if prev % M == 0 else 0)
            delta_cost = self.graph.graph_processor.alpha*(t2 - t1)
            if(i != P - 1):
                #print('===', end='')
                if(i > 0):
                    # print('===', end='')                                                            
                    cost = cost + delta_cost
                    print(f'({delta_cost})===', end='')
                print(f'{real_node}===', end='')
            else:
                cost = cost + self.last_cost #+ delta_cost
                delta_cost = self.last_cost #+ delta_cost
                #print(f'({delta_cost})==={real_node}/{node}===END. ', end='')
                print(f'({delta_cost})==={node}===END. ', end='')
            prev = path[i]
        dest = path[-2]
        real_dest = M if dest % M == 0 else dest % M
        print(f'Total cost: {cost}. The AGV reaches its destination: {real_dest} at {self.end_time} along with earliness = {self.earliness} and tardiness = {self.tardiness}')
    def process(self):
        if(self.graph.graph_processor.print_out):
            # Đây là phương thức để xử lý khi AGV đạt đến mục tiêu
            print(
                f"AGV {self.agv.id} has reached the target node {self.target_node} at time {self.end_time}"
                )
        #pdb.set_trace()
        #print(self.agv.path)
        self.re_calculate_reaching(self.agv.path)
        cost = self.calculate_cost_reaching()  # Calculate and update the cost of reaching the target
        #print("DSFFDdsfsdDF")
        
        print(f"The total cost of {self.agv.id} is {cost}")
        config.totalCost = config.totalCost + cost
        config.reachingTargetAGVs = config.reachingTargetAGVs + 1
        self.agv.destroy()
        del self.agv
    
    def __str__(self):
        return f"ReachingTargetEvent for {self.agv.id} at time: {self.end_time} and it reaches the artificial node {self.target_node}"

class RestrictionEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, start_node, end_node, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        self.start_node = start_node
        self.end_node = end_node

    def updateGraph(self):
        # Giả định thời gian di chuyển thực tế khác với dự đoán do các ràng buộc đặc biệt
        actual_time = self.end_time - self.start_time
        predicted_time = self.graph.get_edge(self.start_node, self.end_node).weight

        if actual_time != predicted_time:
            # Cập nhật trọng số của cung trên đồ thị để phản ánh thời gian thực tế
            self.graph.update_edge(self.start_node, self.end_node, actual_time)

            # Đánh dấu AGV cuối cùng thay đổi đồ thị
            self.graph.lastChangedByAGV = self.agv.id

    def calculate_cost_restriction(self):
        # Chi phí của AGV sẽ được tăng thêm một lượng bằng trọng số của cung mà AGV đi trên đồ thị TSG
        edge = self.graph.get_edge(self.start_node, self.end_node)
        if edge:
            cost_increase = edge.weight
            self.agv.cost += cost_increase
            print(
                f"Cost increased by {cost_increase} for AGV {self.agv.id} due to RestrictionEvent from {self.start_node} to {self.end_node}"
            )
        else:
            print("No edge found or incorrect edge weight.")

    def process(self):
        # Xử lý khi sự kiện được gọi
        print(
            f"AGV {self.agv.id} moves from {self.start_node} to {self.end_node} under restrictions, taking {self.end_time - self.start_time} seconds"
        )
        self.updateGraph()
        self.calculate_cost_restriction()

class TimeWindowsEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, target_node, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        self.target_node = target_node  # Mục tiêu mà AGV phải đạt đến trong một khoảng thời gian nhất định

    def calculate_cost_time(self):
        # Chi phí dựa trên trọng số của cung mà AGV đi trên đồ thị TSG
        edge = self.graph.get_edge(self.agv.current_node, self.target_node)
        if edge:
            cost_increase = edge.weight
            self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
            print(
                f"Cost increased by {cost_increase} for AGV {self.agv.id} due to TimeWindowsEvent at {self.target_node}"
            )
        else:
            print("No edge found or incorrect edge weight.")

    def getNext(self):
        # Tính toán chi phí
        self.calculate_cost_time()
        # Có thể thực hiện các hành động tiếp theo tùy thuộc vào logic của bạn
        # Ví dụ: kiểm tra xem có sự kiện tiếp theo cần được lên lịch không

    def process(self):
        # Xử lý khi sự kiện được gọi
        print(
            f"AGV {self.agv.id} processes TimeWindowsEvent at {self.target_node} at time {self.end_time}"
        )
        self.getNext()
    
class StartEvent(Event):
    static_index = 0
    def __init__(self, start_time, end_time, agv, graph, graph_processor):
        super().__init__(start_time, end_time, agv, graph, graph_processor)
        StartEvent.static_index += 1
        print(self)

    def process(self):
        #pdb.set_trace()
        if(self.graph.graph_processor.print_out):
            print(f"StartEvent processed at time {self.start_time} for {self.agv.id}. The AGV is currently at node {self.agv.current_node}.")
        self.getNext()
        
    def __str__(self):
        return f"{StartEvent.static_index}) StartEvent for {self.agv.id} to kick off its route from {self.agv.current_node} at {self.start_time}"
    
    def getNext(self, debug = False):
        self.solve()
        if(debug):
            pdb.set_trace()
        next_node = self.graph.nodes[self.agv.current_node]
        #if(self.agv.id == 'AGV23'):
        #    pdb.set_trace()
        new_event = next_node.goToNextNode(self)
        if(new_event.end_time < 0):
            pdb.set_trace()
            new_event = next_node.goToNextNode(self)
        simulator.schedule(new_event.end_time, new_event.process)
