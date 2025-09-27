from controller.rerouting_controller import ReroutingController
from model.AGV import AGV
import pdb
class SingleFlowRerouting (ReroutingController):
    def __init__(self, graph_processor):
        super().__init__(graph_processor)
    
    """def write_to_file(self, agv_id_and_new_start=None, new_halting_edges=None,
          supply=None, vs_id=None, vt_id=None, filename="TSG.txt"):
        pass"""
    
    def get_printable_edges(self, agv_id = None):
        if agv_id is None:
            return super().get_printable_edges()
        ts_edges = self.get_ts_edges()
        printable_edges = set()
        all_AGVs = AGV.all_instances()
        for agv in all_AGVs:
            pdb.set_trace
            if agv.id != agv_id:
                for e in ts_edges:
                    if e is not None and (e.start_node.agv.id == agv.id \
                        or e.end_node.agv.id == agv.id):
                        continue
                    printable_edges[e] = True
        #return self.ts_edges