from model.Graph import Graph, bcolors#, graph
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


def get_os():
    os_name = platform.system()
    if os_name == 'Darwin':
        return "macOS"
    elif os_name == 'Windows':
        return "Windows"
    elif os_name == 'Linux':
        return "Linux"
    else:
        return "Undefined OS"


def choose_solver():
    print("Choose the method for solving:")
    print("1 - Use LINK II solver")
    print("2 - Use parallel network-simplex")
    print("3 - Use NetworkX")
    choice = 3
    if(config.count % 2 == 0):
        choice = 1
        config.solver_choice = 'solver'
    else:
        if(config.count <= 1):
            choice = input("Enter your choice (1 or 2 or 3): ")
            if choice == '1':
                 config.solver_choice = 'solver'
            elif choice == '2':
                 config.solver_choice = 'network-simplex'
            elif choice == '3':
                 config.solver_choice = 'networkx'
            else:
                 print("Invalid choice. Defaulting to Network X.")
                 config.solver_choice = 'networkx'
        else:
            config.solver_choice = 'networkx'    


def choose_time_measurement():
    # choose to run sfm or not
    if(config.count == 1 and config.test_automation == 0):
        print("Choose level of Time Measurement:")
        print("0 - Fully Random")
        print("1 - Random in a list")
        print("2 - SFM")
        choice = input("Enter your choice (0 to 2): ")
        if choice == '0':
            config.level_of_simulation = 0
        elif choice == '1':
            config.level_of_simulation = 1
        elif choice == '2':
            config.level_of_simulation = 2
        else:
            print("Invalid choice. Defaulting to run SFM.")
            config.level_of_simulation = 2
    else:
        if(config.count <= 2):
            config.level_of_simulation = 0
        elif(config.count <= 4):
            config.level_of_simulation = 1
        elif(config.count <= 6):
            config.level_of_simulation = 2            
            
def choose_test_automation():
    if(config.count == 1):
        print("Choose level of Test automation:")
        print("0 - Manual")
        print("1 - Automation")
        choice = input("Enter your choice (0 or 1): ")
        if choice == '0':
            config.test_automation = 0
        else:
            print("Defaulting to run Automation")
            config.test_automation = 1

allAGVs = set()
TASKS = set()

x = {}
y = {}

config.count = 0
logger = Logger()
while(config.count < 2*3):#*12 and config.numOfAGVs <= 10):
    #pdb.set_trace()
    config.count = config.count + 1
    if(config.count >= 5 and get_os() != 'Linux'):
        print("The current OS doesnt support SFM Simulation")
        continue
    if config.count > 1:
        print(f"{bcolors.WARNING}Start half cleanup{bcolors.ENDC}")
        dm.half_cleanup()
        if(config.count % 2 == 0):
            print("Start using solver at: ", config.count)
        else:
            print("Start using NetworkX at: ", config.count)
        #    pdb.set_trace()
        #config.numOfAGVs = config.numOfAGVs + 2*(config.count % 2)
    choose_solver()
    choose_test_automation()
    choose_time_measurement()
    graph_processor = GraphProcessor()
    start_time = time.time()
    #print("main.py:96, ", config.count)
    #if(config.count == 3):
    #pdb.set_trace()
    graph_processor.use_in_main(config.count != 1)
    end_time = time.time()
    graph_processor.print_out = False
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
        logger.log("Log.csv", config.filepath, config.numOfAGVs, config.H, \
            config.d, config.solver_choice, config.reachingTargetAGVs, config.haltingAGVs, \
                config.totalCost, elapsed_time, config.timeSolving, config.level_of_simulation, formatted_now)
        reset(simulator)
