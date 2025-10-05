from controller.NodeGenerator import ArtificialNode
from controller.RestrictionController import RestrictionController
from controller.max_flow_pipeline import MaxFlowPipeline
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
        if use_config_data or getattr(config, "max_flow_conditions_initialized", False):
            return config.max_flow_conditions
        if getattr(config, "max_flow_conditions", None) is not None:
            config.max_flow_conditions_initialized = True
            return config.max_flow_conditions

        conditions = []
        H = getattr(self.graph_processor, "H", getattr(config, "H", None))

        while True:
            line = input("Nhập các bộ điều kiện x y a b (default: none,  hint: '1 2 3 4') - Enter để dừng nhập: ").strip()
            if not line:
                break
            try:
                x, y, a, b = map(int, line.split())
                is_valid = (x != y) and (a < b) and (H is None or b <= H)
                if not is_valid:    
                    print("⚠️  Điều kiện không hợp lệ. Yêu cầu: x != y và a < b" + (f" và b <= H({H})" if H is not None else "") + ".")
                    conditions = None
                    break
                conditions.append((x, y, a, b))
            except Exception:
                print("⚠️  Nhập không hợp lệ. Định dạng đúng: x y a b")
                conditions = None
                break

        if conditions is not None and len(conditions) == 0:
            conditions = None

        config.max_flow_conditions = conditions
        if hasattr(config, "invalid_conditions"):
            config.invalid_conditions = (conditions is None)
        return conditions

    def compute_max_flow(self, use_config_data=False):
        """Chạy MaxFlow và trả về giá trị F."""
        self.graph_processor.pipeline = MaxFlowPipeline(self.graph_processor)
        conditions = self.get_max_flow_conditions(use_config_data)
        if not conditions:
            # Không có điều kiện hoặc điều kiện không hợp lệ: F = U (maxflow bằng ngưỡng trên)
            U = self.get_artificial_upper_bound(use_config_data)
            if getattr(config, "print_out", False):
                print(f"Không có bộ điều kiện MaxFlow. Gán F = U = {U}.")
            return U
        F = self.graph_processor.pipeline.run_all(conditions)
        return F
    
    def insert_artificial_objects(self, F, U=None, gamma=None, use_config_data=False):
        """Chèn node/cung ảo nếu cần thiết."""
        if U is None:
            U = self.get_artificial_upper_bound(use_config_data)
        if gamma is None:
            gamma = self.get_artificial_gamma(use_config_data)
        #print(f"✅ Max Flow F = {F}, U = {U}")
        from controller.artificial_node_inserter import ArtificialNodeInserter
        if F > U and F != 0:
            if self.graph_processor.graph is None:
                self.graph_processor.graph = Graph(self.graph_processor)
            ArtificialNodeInserter(self.graph_processor).run(U, gamma)
            
    def get_artificial_upper_bound(self, use_config_data=False):
        if config.artificial_upper_bound is not None or use_config_data:
            return config.artificial_upper_bound or 1
        U_input = input("Nhập U (default: 1): ")
        U = int(U_input) if U_input.strip() else 1
        config.artificial_upper_bound = U
        return U

    def get_artificial_gamma(self, use_config_data=False):
        if config.artificial_gamma is not None or use_config_data:
            return config.artificial_gamma or 1230919231
        gamma_input = input("Nhập gamma (default: 1230919231): ")
        gamma = int(gamma_input) if gamma_input.strip() else 1230919231
        config.artificial_gamma = gamma
        return gamma
