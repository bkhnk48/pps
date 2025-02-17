# This module is used as interface to call and get the simulation results from the hallway simulator
# input: hallway ID, list of AGV IDs, list of AGV directions, number of people in the hallway, human type distribution(lst), time stamp(seconds), event type(0: new_event, 1: update_event(reuse the previous event with new AGV))
# output: Run time of all AGVs (get from json file)

import json
import os
import time
import sys
import platform

class DirectoryManager: # just use to manage the directory(like create, remove, check if exists)
    def full_cleanup(self):
        # check if the directory exists
        if not os.path.exists("data/input"):
            os.makedirs("data/input")
        if not os.path.exists("data/output"):
            os.makedirs("data/output")
        if not os.path.exists("data/timeline"):
            os.makedirs("data/timeline")
        if not os.path.exists("data/tmp"):
            os.makedirs("data/tmp")
        os.system("rm -rf data/input/*")
        os.system("rm -rf data/output/*")
        os.system("rm -rf data/timeline/*")
        os.system("rm -rf data/tmp/*")
    def half_cleanup(self):
        os.system("rm -rf data/input/*")
        os.system("rm -rf data/output/*")
        files = os.listdir("data/tmp")
        for file in files:
            with open(f"data/tmp/{file}", "r") as f:
                data = json.load(f)
                for event in data["timeline"]:
                    event["agvs"] = []
            with open(f"data/tmp/{file}", "w") as f:
                output_json = json.dumps(data, indent=4)
                f.write(output_json)

class HallwaySimulator:
    def __init__(self):
        self.hallway_id = 0 # string
        self.hallway_length = 0 # int
        self.hallway_width = 0 # int
        self.agv_ids = [] # list of int
        self.agv_directions = [] # list of int
        self.num_people = 0 # int
        self.human_type_distribution = [] # list of int
        self.time_stamp = 0 # int
        self.event_type = 0 # int
        self.run_time = [] # list of tuple (AGV ID, run time)
        self.machine_arch = platform.machine()

    def set_params(self,
                   hallway_id,
                   hallway_length,
                   hallway_width,
                   agv_ids,
                   agv_directions,
                   num_people,
                   human_type_distribution,
                   time_stamp,
                   event_type):
        self.hallway_id = hallway_id
        self.hallway_length = hallway_length
        self.hallway_width = hallway_width
        self.agv_ids = agv_ids
        self.agv_directions = agv_directions
        self.num_people = num_people
        self.human_type_distribution = human_type_distribution
        self.time_stamp = time_stamp
        self.event_type = event_type

    def json2params(self, json_data):
        self.set_params(
            json_data["hallway_id"],
            json_data["hallway_length"],
            json_data["hallway_width"],
            json_data["agv_ids"],
            json_data["agv_directions"],
            json_data["num_people"],
            json_data["human_type_distribution"],
            json_data["time_stamp"],
            json_data["event_type"]
        )

    def create_json(self):
        """
        json filename: <hallway_id>_<time_stamp>.json
        {
          "numOfAgents": {
            "description": "Number of agents",
            "value": 50
          },
          "TDDegree": {
            "description": "T-Distribution' degree of freedom",
            "value": 15
          },
          "totalCrowdLength": {
            "description": "Crowd total length",
            "value": 50
          },
          "headCrowdLength": {
            "description": "Crowd head/tail length",
            "value": 10
          },
          "crowdWidth": {
            "description": "Crowd width",
            "value": 2
          },
          "acceleration": {
            "description": "Acceleration of AGV",
            "value": 0
          },
          "agvDesiredSpeed": {
            "description": "Desired speed of AGV (m/s)",
            "value": 0.6
          },
          "thresDistance": {
            "description": "Threshold distance for agv to stop when colliding with a person",
            "value": 0.3
          },
          "stopAtHallway": {
            "description": "Percentage of people stopping at the hallway",
            "value": 2
          },
          "p1": {
            "description": "Percentage of agents (No disability, without overtaking behavior)",
            "value": 22
          },
          "p2": {
            "description": "Percentage of agents (No disability, with overtaking behavior)",
            "value": 5
          },
          "p3": {
            "description": "Percentage of agents (Walking with crutches)",
            "value": 17
          },
          "p4": {
            "description": "Percentage of agents (Walking with sticks)",
            "value": 22
          },
          "p5": {
            "description": "Percentage of agents (Wheelchairs)",
            "value": 17
          },
          "p6": {
            "description": "Percentage of agents (The blind)",
            "value": 17
          },
          "hallwayLength": {
            "description": "Hallway length",
            "value": 60
          },
          "hallwayWidth": {
            "description": "Hallway width",
            "value": 6
          },
          "agvDirections": {
            "description": "Run direction of the AGV: left to right (0), right to left (1)",
            "value": [1]
          },
          "agvIDs": {
            "description": "AGV ID",
            "value": [2]
          },
          "timeline_pointer": {
            "description": "Timeline pointer",
            "value": 15
          },
          "hallwayID": {
            "description": "Arc ID",
            "value": "j0"
          },
          "experimentalDeviation": {
            "description": "Experimental deviation (percent)",
            "value": 10
          }
        }
        """
        data = {
            "numOfAgents": {
                "description": "Number of agents",
                "value": self.num_people
            },
            "TDDegree": {
                "description": "T-Distribution' degree of freedom",
                "value": 15
            },
            "totalCrowdLength": {
                "description": "Crowd total length",
                "value": 50
            },
            "headCrowdLength": {
                "description": "Crowd head/tail length",
                "value": 10
            },
            "crowdWidth": {
                "description": "Crowd width",
                "value": 2
            },
            "acceleration": {
                "description": "Acceleration of AGV",
                "value": 0.25
            },
            "agvDesiredSpeed": {
                "description": "Desired speed of AGV (m/s)",
                "value": 0.6
            },
            "thresDistance": {
                "description": "Threshold distance for agv to stop when colliding with a person",
                "value": 0.3
            },
            "stopAtHallway": {
                "description": "Percentage of people stopping at the hallway",
                "value": 2
            },
            "p1": {
                "description": "Percentage of agents (No disability, without overtaking behavior)",
                "value": self.human_type_distribution[0]
            },
            "p2": {
                "description": "Percentage of agents (No disability, with overtaking behavior)",
                "value": self.human_type_distribution[1]
            },
            "p3": {
                "description": "Percentage of agents (Walking with crutches)",
                "value": self.human_type_distribution[2]
            },
            "p4": {
                "description": "Percentage of agents (Walking with sticks)",
                "value": self.human_type_distribution[3]
            },
            "p5": {
                "description": "Percentage of agents (Wheelchairs)",
                "value": self.human_type_distribution[4]
            },
            "p6": {
                "description": "Percentage of agents (The blind)",
                "value": self.human_type_distribution[5]
            },
            "hallwayLength": {
                "description": "Hallway length",
                "value": self.hallway_length
            },
            "hallwayWidth": {
                "description": "Hallway width",
                "value": self.hallway_width
            },
            "agvDirections": {
                "description": "Run direction of the AGV: left to right (0), right to left (1)",
                "value": self.agv_directions
            },
            "agvIDs": {
                "description": "AGV ID",
                "value": self.agv_ids
            },
            "timeline_pointer": {
                "description": "Timeline pointer",
                "value": int(self.time_stamp)
            },
            "hallwayID": {
                "description": "Arc ID",
                "value": f"{self.hallway_id}"
            },
            "experimentalDeviation": {
                "description": "Experimental deviation (percent)",
                "value": 10
            }
        }
        filename = f"data/input/{self.hallway_id}_{self.time_stamp}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        return filename

    def create_map(self):
        """
        map filename: <hallway_id>_<time_stamp>.txt
        1
        6
        J1 2 3 3

        explain:
        <don't care -> keep the same>
        <Hallway width>
        <Hallway ID> <dont_care -> keep the same> <hallway length> <hallway length>
        """
        filename = f"data/input/{self.hallway_id}_{self.time_stamp}.txt"
        with open(filename, "w") as f:
            f.write("1\n")
            f.write(f"{self.hallway_width}\n")
            f.write(f"J{self.hallway_id} 2 {self.hallway_length} {self.hallway_length}")
        return filename

    def run_simulation(self):
        json_file = self.create_json()
        map_file = self.create_map()
        tmp_file = f"data/tmp/{self.hallway_id}.json" # remove the last 2 characters and before the extension
        # check if in input folder has the json file and map file
        if not os.path.exists(json_file) or not os.path.exists(map_file) or not os.path.exists(tmp_file):
            if not os.path.exists(json_file):
                print(f"json file {json_file} not found")
            if not os.path.exists(map_file):
                print(f"map file {map_file} not found")
            if not os.path.exists(f"data/tmp/{tmp_file}"):
                print(f"tmp file {tmp_file} not found")
            #print("event_type 0")
            os.system(f"model/hallway_simulator_module/sim/{str(self.machine_arch)}/app {json_file} {map_file} 0")

        else:
            #print("event_type 1")
            os.system(f"model/hallway_simulator_module/sim/{str(self.machine_arch)}/app {json_file} {map_file} 1")


        # scan the model/hallway_simulator_module/sim/data/output folder to get the run time of all AGVs (all in json format)
        time.sleep(1)
        files = os.listdir("data/output")
        # result_agv_1.json, result_agv_2.json, ...
        for agv_id in self.agv_ids:
            log_name = f"result_agv_{agv_id}.json"
            for file in files:
                if log_name == file:
                    with open(f"data/output/{file}", "r") as f:
                        data = json.load(f)
                        # "AGVRealTime" is the key to get the run time of the AGV(divided the number to 1000)
                        real_time = int(data["AGVRealTime"]/1000)
                        ID = int(file.split("_")[2].split(".")[0])
                        self.run_time.append((ID, real_time)) # (AGV ID, run time)
        return self.run_time

    def clean(self):
        os.system("rm -rf data/input/*")
        os.system("rm -rf data/output/*")
        # reset all variables
        self.hallway_id = 0
        self.hallway_length = 0
        self.hallway_width = 0
        self.agv_ids = []
        self.agv_directions = []
        self.num_people = 0
        self.human_type_distribution = []
        self.time_stamp = 0
        self.event_type = 0

    def full_clean(self):
        os.system("rm -rf data/input/*")
        os.system("rm -rf data/output/*")
        os.system("rm -rf data/timeline/*")
        os.system("rm -rf data/tmp/*")
        # reset all variables
        self.hallway_id = 0
        self.hallway_length = 0
        self.hallway_width = 0
        self.agv_ids = []
        self.agv_directions = []
        self.num_people = 0
        self.human_type_distribution = []
        self.time_stamp = 0
        self.event_type = 0

class BulkHallwaySimulator:
    def __init__(self, scenario_id, MaxAgents, hallways_list, functions_list, events_list):
        self.scenario_id = scenario_id
        self.Scenario = {}
        self.AGV_COMPLETION_LOGS = {}
        self.MaxAgents = int(MaxAgents)
        self.hallways_list = hallways_list
        self.functions_list = functions_list
        self.events_list = events_list


    def read_function(self, function):
        splitted = function.split(" ")
        a = splitted[2]
        b = splitted[6]

        # split 7 then remove '(' and ')'
        from_to = splitted[7].replace("(", "").replace(")", "").split(",")

        return a, b, from_to

    def agent_calculator(self, agents_distribution, time_stamp):
        selected_function = ""
        for function in self.functions_list:
            _, _, from_to = self.read_function(function)
            if int(from_to[0]) <= time_stamp <= int(from_to[1]):
                selected_function = function
                #print(selected_function)
                break

        a, b, _ = self.read_function(selected_function)
        if int(int(a) * int(time_stamp) + int(b)) > self.MaxAgents:
            return int(self.MaxAgents / 100 * agents_distribution)
        if int(int(a) * int(time_stamp) + int(b)) < 0:
            return 0
        return int(int(int(a) * int(time_stamp) + int(b)) / 100 * agents_distribution)


    def init2json(self):
        self.Scenario["Scenario_ID"] = self.scenario_id
        self.Scenario["MaxAgents"] = self.MaxAgents
        self.Scenario["Events"] = []
        self.Scenario["hallway_width"] = 4

        for hallway in self.hallways_list:
            for event in self.events_list:
                if event["hallway_id"] == hallway["hallway_id"]:
                    agents_count = self.agent_calculator(hallway["agents_distribution"], event["time_stamp"])
                    self.Scenario["Events"].append(
                        {"hallway_id": hallway["hallway_id"],
                            "length": hallway["length"],
                            "width": hallway["width"],
                            "agv_ids": event["AgvIDs"],
                            "agv_directions": event["AgvDirections"],
                            "human_type_distribution": [22, 5, 17, 22, 17, 17],
                            "num_people": agents_count,
                            "time_stamp": event["time_stamp"]
                            })


    def prepare_data(self):
        # check the time_stamp and create a list of time_stamp(empty json object)
        time_stamps = set()
        for event in self.Scenario["Events"]:
            time_stamps.add(event["time_stamp"])
        time_stamps = sorted(list(time_stamps))

        # create json object for each time_stamp
        self.run_dict = {}
        for time_stamp in time_stamps:
            self.run_dict[time_stamp] = []
            for event in self.Scenario["Events"]:
                if event["time_stamp"] == time_stamp:
                    self.run_dict[time_stamp].append(event)

        # generate variables for logging the completion time of each AGV
        # read all AGV IDs from the hallways
        agv_ids = set()
        self.AGV_COMPLETION_LOGS = {}
        for event in self.Scenario["Events"]:
            for id in event["agv_ids"]:
                #print(id)
                agv_ids.add(int(id))
        #print(agv_ids)
        for agv_id in agv_ids:
            self.AGV_COMPLETION_LOGS[agv_id] = {}


    def run_simulation(self):
        self.init2json()
        self.prepare_data()
        # call class HallwaySimulator to run the simulation
        hallway_simulator = HallwaySimulator()

        for time_stamp in self.run_dict:
            for hallway in self.run_dict[time_stamp]:
                hallway_simulator.set_params(
                    hallway["hallway_id"],
                    hallway["length"],
                    hallway["width"],
                    hallway["agv_ids"],
                    hallway["agv_directions"],
                    hallway["num_people"],
                    hallway["human_type_distribution"],
                    time_stamp,
                    0
                )
                output = hallway_simulator.run_simulation()
                #print(output)
                for agv in output:
                    self.AGV_COMPLETION_LOGS[agv[0]][hallway['hallway_id']] = {"time_stamp": time_stamp, "completion_time": agv[1]}

        #print(self.AGV_COMPLETION_LOGS)
        return self.AGV_COMPLETION_LOGS

#    def output_filter(self):
