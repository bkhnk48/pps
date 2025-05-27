import platform
import time
from datetime import datetime
from model.Logger import Logger
import config
from model.hallway_simulator_module.HallwaySimulator import DirectoryManager
from openpyxl import load_workbook
import math
import numpy as np
import pdb

#Sẽ được lớp ReadingInputProcessor kế thừa
class StartNodeGenerator:
    def __init__(self):
        self._started_nodes = []
        self._ID = []
        self._earliness = 0
        self._tardiness = 0
        self._H = 0
        self._M = 0
        self._seed = 0
        
    # Getter và Setter cho seed
    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, value):
        if not isinstance(value, int):
            raise ValueError("seed must be an integer")
        self._seed = value
        
    # Getter and Setter for ID
    @property
    def ID(self):
        return self._ID

    @ID.setter
    def ID(self, value):
        self._ID = value

    # Getter and Setter for earliness
    @property
    def earliness(self):
        return self._earliness

    @earliness.setter
    def earliness(self, value):
        self._earliness = value

    # Getter and Setter for tardiness
    @property
    def tardiness(self):
        return self._tardiness

    @tardiness.setter
    def tardiness(self, value):
        self._tardiness = value    

    @property
    def M(self):
        return self._M
    @M.setter
    def M(self, value):
        self._M = value
        
    # Getter and Setter for H
    @property
    def H(self):
        return self._H

    @H.setter
    def H(self, value):
        self._H = value
    
    # Getter và Setter cho started_nodes
    @property
    def started_nodes(self):
        return self._started_nodes

    @started_nodes.setter
    def started_nodes(self, value):
        if not isinstance(value, list):
            raise ValueError("started_nodes must be a list")
        self._started_nodes = value
    
    def generate_numbers_student(self, G, H, M, N = 0, df=10):
        while True:
            self._seed = self._seed + 1
            self._seed = self._seed % G
            np.random.seed(self._seed)
            # Sinh 4 số ngẫu nhiên theo phân phối Student
            first_two = np.random.standard_t(df, size=2)
            numbers = np.random.standard_t(df, size=2)
            # Chuyển đổi các số này thành số nguyên trong khoảng từ 1 đến 100
            first_two = np.round((first_two - np.min(first_two)) / (np.max(first_two) - np.min(first_two)) * (G//3) + self._seed).astype(int)
            numbers = np.round((numbers - np.min(numbers)) / (np.max(numbers) - np.min(numbers)) * (H//3) + self._seed).astype(int)
            if first_two[0] < G and first_two[1] < G and numbers[0] <= numbers[1] and numbers[1] < H:
                # Kiểm tra điều kiện khoảng cách tối thiểu
                if (abs(first_two[0] - first_two[1]) >= M and abs(numbers[0] - numbers[1]) >= N):
                    return np.concatenate((first_two, numbers))
        
    def generate_start_nodes(self, num_of_agvs):
        if len(self.started_nodes) == 0:
            self.ID = []
            self.earliness = []
            self.tardiness = []
            #pdb.set_trace()
            for _ in range(num_of_agvs):
                [s, d, e, t] = self.generate_numbers_student(self.M, self.H, int(0.2*self.M))#, 100 if self.H > 100 else self.H//3)
                while s in self.started_nodes:
                    s += self.M
                    if s >= self.H * self.M:
                        break
                self.started_nodes.append(s)
                self.ID.append(d)
                self.earliness.append(e)
                self.tardiness.append(t)
            print(f'Start: {self.started_nodes} \n End: {self.ID} \n Earliness: {self.earliness} \n Tardiness: {self.tardiness}')
            config.started_nodes = self.started_nodes.copy()
            config.ID = self.ID.copy()
            config.earliness = self.earliness.copy()
            config.tardiness = self.tardiness.copy()
        
    
