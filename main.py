from model.Graph import Graph#, graph
from model.AGV import AGV
from model.Event import Event, debug
from controller.EventGenerator import StartEvent
from model.Logger import Logger
import config
from discrevpy import simulator
from controller.GraphProcessor import GraphProcessor
import subprocess
import sys
import pdb
import time
from datetime import datetime
import os
import platform

from model.hallway_simulator_module.HallwaySimulator import DirectoryManager
dm = DirectoryManager()
dm.full_cleanup()

allAGVs = set()
TASKS = set()
x = {}
y = {}
config.count = 0
#logger = Logger()
while(config.count < 2*3):#*12 and config.numOfAGVs <= 10):
    graph_processor = GraphProcessor(dm)
    if not graph_processor.start_round():  # Nếu gặp trường hợp OS không hỗ trợ SFM
        break
    # --- Thiết lập cấu hình ban đầu ---
    graph_processor.choose_solver()
    graph_processor.choose_test_automation()
    graph_processor.choose_time_measurement()

    start_time = time.time()
    graph_processor.use_in_main(config.count != 1)
    end_time = time.time()
    # Tính thời gian thực thi
    execution_time = end_time - start_time
    if(execution_time >= 5 and graph_processor.print_out):
        print(f"Thời gian thực thi: {execution_time} giây")
    
    graph = Graph(graph_processor)  # Assuming a Graph class has appropriate methods to handle updates
    
    events = []
    Event.setValue("number_of_nodes_in_space_graph", graph_processor.M) #sẽ phải đọc file Edges.txt để biết giá trị cụ thể
    Event.setValue("debug", 0)
    # Kiểm tra xem có tham số nào được truyền qua dòng lệnh không
    if len(sys.argv) > 1:
        Event.setValue("debug", 1 if sys.argv[1] == '-g' else 0)
    
    number_of_nodes_in_space_graph = Event.getValue("number_of_nodes_in_space_graph")
    # Mở file để đọc
    #pdb.set_trace()
    graph_processor.init_agvs_n_events(allAGVs, events, graph, graph_processor)
    graph_processor.init_tasks(TASKS)
    graph_processor.init_nodes_n_edges() 
    events = sorted(events, key=lambda x: x.start_time)
    Event.setValue("allAGVs", allAGVs)
    
    
    def schedule_events(events):
        for event in events:
            #pdb.set_trace()
            simulator.schedule(event.start_time, event.process)
    
    def reset(simulator):
        config.totalCost = 0
        config.reachingTargetAGVs = 0
        config.haltingAGVs = 0
        config.totalSolving = 0
        config.timeSolving = 0
        #pdb.set_trace()
        if config.solver_choice == 'networkx':
            config.solver_choice = 'solver'
        AGV.reset()
        simulator.reset()
    
    if __name__ == "__main__":
        import time
        start_time = time.time()
        simulator.ready()
        schedule_events(events)
        simulator.run()
        end_time = time.time()
        # Tính toán thời gian chạy
        elapsed_time = end_time - start_time
        # Chuyển đổi thời gian chạy sang định dạng hh-mm-ss
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        config.timeSolving = config.timeSolving / config.totalSolving
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        #runTime = f'{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)
        print("Thời gian chạy: {:02}:{:02}:{:02} để giả lập việc di chuyển của {} AGVs".format(int(hours), int(minutes), int(seconds), config.num_max_agvs))
        graph_processor.logger.log("Log.csv", config.filepath, config.numOfAGVs, config.H, \
            config.d, config.solver_choice, config.reachingTargetAGVs, config.haltingAGVs, \
                config.totalCost, elapsed_time, config.timeSolving, config.level_of_simulation, formatted_now)
        reset(simulator)
