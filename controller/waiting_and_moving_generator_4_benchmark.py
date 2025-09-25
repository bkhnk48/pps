from controller.NodeGenerator import TimeWindowNode  # only for exclusion
from controller.waiting_and_moving_generator import WaitingAndMovingEdgesGenerator
from model.BenchmarkNode import TopOrBottomBulbNode


class WaitingAndMovingEdgesGenerator4Benchmark(WaitingAndMovingEdgesGenerator):
    def insert_halting_edges(self):  # type: ignore[override]
        fmt = getattr(self, "_input_format", None)
        if fmt != "benchmark":
            return super().insert_halting_edges()

        M = getattr(self, "M", None)
        H = getattr(self, "H", None)
        if not M or H is None:
            return super().insert_halting_edges()

        halting_nodes: set[int] = set()
        for edge in (getattr(self, "ts_edges", []) or []):
            end = getattr(edge, "end_node", None)
            if not isinstance(end, TopOrBottomBulbNode):
                continue
            try:
                node_id = int(getattr(end, "id", -1))
                time_idx = node_id // M - (1 if node_id % M == 0 else 0)
                if time_idx >= H:
                    halting_nodes.add(node_id)
            except Exception:
                continue
        if not halting_nodes:
            return  # Nothing to add
        targets = self.get_targets()
        if not targets:
            return

        penalty_cost = H * H  
        new_edges = {
            (h_node, target.id, 0, 1, penalty_cost)
            for h_node in halting_nodes
            for target in targets
        }
        if new_edges:
            self.create_set_of_edges(new_edges)