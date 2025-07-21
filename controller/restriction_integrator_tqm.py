from controller.NodeGenerator import ArtificialNode
from controller.RestrictionController import RestrictionController
from controller.MaxFlowPipeline import MaxFlowPipeline
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx
import config
import pdb

class RestrictionIntegratorTQM(RestrictionController):
    def __init__(self, graph_processor):
        super().__init__(graph_processor)
    def get_max_flow_conditions(self, use_config_data=False):
        if config.max_flow_conditions is not None or use_config_data:
            return config.max_flow_conditions or [(1, 2, 3, 4)]
        conditions = []
        while True:
            line = input("Nhập các bộ điều kiện x y a b (default: '1 2 3 4'): ").strip()
            if not line:
                break
            try:
                x, y, a, b = map(int, line.split())
                conditions.append((x, y, a, b))
            except:
                print("⚠️  Nhập không hợp lệ. Nhập lại theo định dạng: x y a b")
        if not conditions:
            conditions = [(1, 2, 3, 4)]
        config.max_flow_conditions = conditions
        return conditions

    def compute_max_flow(self, use_config_data=False):
        """Chạy MaxFlow và trả về giá trị F."""
        self.graph_processor.pipeline = MaxFlowPipeline(self.graph_processor)
        conditions = self.get_max_flow_conditions(use_config_data)
        F = self.graph_processor.pipeline.run_all(conditions)
        return F
    
    def insert_artificial_objects(self, F, U=None, gamma=None, use_config_data=False):
        """Chèn node/cung ảo nếu cần thiết."""
        if U is None:
            U = get_artificial_upper_bound(use_config_data)
        if gamma is None:
            gamma = get_artificial_gamma(use_config_data)
        #print(f"✅ Max Flow F = {F}, U = {U}")
        import controller.ArtificialNodeInserter
        if F > U and F != 0:
            if self.graph_processor.graph is None:
                self.graph_processor.graph = Graph(self.graph_processor)
            ArtificialNodeInserter(self.graph_processor).run(U, gamma)