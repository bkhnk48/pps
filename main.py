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

def check_file_existence():
    # Đường dẫn cho từng hệ điều hành
    mac_path = 'model/hallway_simulator_module/sim/arm64/app'
    linux_path = 'model/hallway_simulator_module/sim/x86_64/app'

    # Kiểm tra hệ điều hành
    if platform.system() == 'Darwin':  # macOS
        file_path = mac_path
    elif platform.system() == 'Linux':  # Linux
        file_path = linux_path
    else:
        print("Non support OS.")
        return False

    # Kiểm tra sự tồn tại của file
    if os.path.isfile(file_path):
        return True
    else:
        print(f"File {file_path} not found!")
        return False

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

def run_full_tests():
    #pdb.set_trace()
    if(config.min_horizontal_time > 0 and config.max_horizontal_time >= config.min_horizontal_time and\
        config.step_horizontal_time > 0 and config.min_AGVs > 0\
            and config.max_AGVs >= config.min_AGVs):
        return
    print("Full test: from 300(s) to 900(s), from 2 AGVs to 10 AGVs, for all levels of pedestrian simulation, from networkX to solver")
    answer = input("Do you want to run full test?(Y/y/1/N/n/0): ")
    if(answer == "Y" or answer == "y" or answer == "1" or answer == ''):
        typed_value = input("Minimum horizontal time (default 300): ")
        if typed_value.isdigit():
            config.min_horizontal_time = int(typed_value)
        else:
            config.min_horizontal_time = 300
        typed_value = input("Maximum horizontal time (default 900): ")
        if typed_value.isdigit():
            config.max_horizontal_time = int(typed_value)
        else:
            config.max_horizontal_time = 900
        typed_value = input("Step of horizontal time (default 300): ")
        if typed_value.isdigit():
            config.step_horizontal_time = int(typed_value)
        else:
            config.step_horizontal_time = 300
        typed_value = input("Minimum AGVs (default 2): ")
        if typed_value.isdigit():
            config.min_AGVs = int(typed_value)
        else:
            config.min_AGVs = 2
        typed_value = input("Maximum AGVs (default 10): ")
        if typed_value.isdigit():
            config.max_AGVs = int(typed_value)
        else:
            config.max_AGVs = 10
    elif(answer == "N" or answer == "n" or answer == "0"):
        pass

def choose_time_measurement():
    # choose to run sfm or not
    if(config.count == 1 and config.test_automation == 0):
        print("Choose level of Time Measurement:")
        print("0 - Fully Random")
        print("1 - Random in a list")
        print("2 - SFM")
        print("3 - Ideal moving")
        choice = input("Enter your choice (0 to 3): ")
        if choice == '0':
            config.level_of_simulation = 0
        elif choice == '1':
            config.level_of_simulation = 1
        elif choice == '2':
            config.level_of_simulation = 2
        elif choice == '3':
            config.level_of_simulation = 3
        else:
            print("Invalid choice. Defaulting to run SFM.")
            config.level_of_simulation = 3
    else:
        #config.level_of_simulation = ((config.count - 1) // 2) % 3
        if(config.count == 1 or config.count == 2):
            config.level_of_simulation = 0
        elif(config.count == 3 or config.count == 4):
            config.level_of_simulation = 1
        elif(config.count == 5 or config.count == 6):
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
    if(config.test_automation == 1):
        run_full_tests()

allAGVs = set()
TASKS = set()

x = {}
y = {}

config.count = 0
logger = Logger()
#pdb.set_trace()
num_of_solvers = 2
num_of_all_ped_sim = 4
num_of_agv_groups = 5
num_of_horizontal_time = 3
default_num_loops = num_of_solvers * num_of_all_ped_sim * num_of_agv_groups * 2 * num_of_horizontal_time
while(config.count < default_num_loops and \
    (config.numOfAGVs <= config.max_AGVs or config.max_AGVs == -1) and \
        (config.numOfAGVs >= config.min_AGVs or config.min_AGVs == -1)):
    #pdb.set_trace()
    StartEvent.static_index = 0
    config.level_of_simulation = (config.count // num_of_solvers) % num_of_all_ped_sim
    config.count = config.count + 1
    if config.count > 1:
        print(f"{bcolors.WARNING}Start half cleanup{bcolors.ENDC}")
        dm.half_cleanup()
        if(config.count % num_of_solvers == 0):
            print("Start using solver at: ", config.count)
        else:
            print("Start using NetworkX at: ", config.count)
        
        #if(config.count % num_of_solvers == 1 and config.count > 1):
        #    config.numOfAGVs = config.count % (num_of_solvers*num_of_agv_groups)
        #    pdb.set_trace()
            """if config.numOfAGVs in [1, 2]:
                config.numOfAGVs = 2
            elif config.numOfAGVs in [3, 4]:
                config.numOfAGVs = 4
            elif config.numOfAGVs in [5, 6]:
                config.numOfAGVs = 6
            elif config.numOfAGVs in [7, 8]:
                config.numOfAGVs = 8
            elif config.numOfAGVs in [9, 0]:
                config.numOfAGVs = 10"""
            #if(config.numOfAGVs / num_of_solvers <= config.numOfAGVs // num_of_solvers):
            #    config.numOfAGVs = config.numOfAGVs // num_of_solvers
            #else:
        
        import math
        config.numOfAGVs = math.ceil(config.count / (num_of_solvers * num_of_all_ped_sim))
        #    config.numOfAGVs = (config.numOfAGVs % num_of_agv_groups) + 1
        config.numOfAGVs *= 2
        config.numOfAGVs = (config.numOfAGVs % (num_of_agv_groups*2))
        config.numOfAGVs = num_of_agv_groups*2 if config.numOfAGVs == 0 else config.numOfAGVs
        if(config.min_horizontal_time != -1):
            quotient = config.count / (num_of_solvers* num_of_all_ped_sim * num_of_agv_groups)
            if quotient <= 1:
                config.H = config.min_horizontal_time
            elif quotient <= 2 and quotient > 1:
                config.H = config.min_horizontal_time + config.step_horizontal_time*1
            elif quotient <= 3:
                config.H = config.min_horizontal_time + config.step_horizontal_time*2
        #    pdb.set_trace()
        #config.numOfAGVs = config.numOfAGVs + 2*(config.count % 2)
    choose_solver()
    choose_test_automation()
    choose_time_measurement()
    graph_processor = GraphProcessor()
    start_time = time.time()
    #print("main.py:96, ", config.count)
    #if(config.count == 3):
    #    pdb.set_trace()
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
        print(f'Simulate: {config.numOfAGVs} AGVs run for {config.H} (s) using {config.solver_choice} and pedestrian simulate mode: {config.level_of_simulation}')
        if(config.level_of_simulation == 2):
            #pdb.set_trace()
            if(not check_file_existence()): #and (config.level_of_simulation == 2)):
                continue
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
        #config.timeSolving = config.timeSolving / config.totalSolving
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        #runTime = f'{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)
        print("Thời gian chạy: {:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))
        logger.log("Log.csv", config.filepath, config.numOfAGVs, config.H, \
            config.d, config.solver_choice, config.reachingTargetAGVs, config.haltingAGVs, \
                config.totalCost, elapsed_time, config.timeSolving, config.level_of_simulation, formatted_now)
        #reset(simulator)
