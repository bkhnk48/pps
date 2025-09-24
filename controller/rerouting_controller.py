import pdb
from abc import ABC

class ReroutingController:
    def __init__(self, graph_processor):
        super().__init__() 
        self.graph_processor = graph_processor
        #Cần khởi tạo ban đầu này
        self._started_nodes = graph_processor.started_nodes
        self._ts_edges = graph_processor.ts_edges
        
    def get_ts_edges(self):
        return self._ts_edges
    
    def set_started_nodes(self, started_nodes):
        self._started_nodes = started_nodes
    
    def get_printable_edges(self, agv_id = None):
        return self._ts_edges
    def write_to_file(self, agv_id_and_new_start=None, new_halting_edges=None,
              supply=None, vs_id=None, vt_id=None, filename="TSG.txt"):
        get_targets = self.get_targets \
            if hasattr(self, 'get_targets') \
                else self.graph_processor.get_targets
        targets = get_targets()
        #pdb.set_trace()
        M = max(target.id for target in targets)
        if new_halting_edges: M = max(M, max(e[1] for e in new_halting_edges))
        num_edges = len(self.get_printable_edges(None if agv_id_and_new_start is None else agv_id_and_new_start[0])) + \
            (len(new_halting_edges) if new_halting_edges else 0)

        with open(filename, 'w') as f:
            f.write(f"p min {M} {num_edges}\n")
            f.write(f"c number of spaces nodes is: {M}\n")
            starts = self._started_nodes if len(self._started_nodes) > 0 else self.graph_processor.started_nodes
            self._write_node_lines(f, starts, targets, supply, vs_id, vt_id)

            #if hasattr(self, 'ts_edges') or hasattr(self, '_ts_edges'):
            if self.graph_processor.graph is None:
                for e in self._ts_edges: self._write_edge_lines(f, e)
            elif hasattr(self.graph_processor.graph, 'adjacency_list'):
                for sid, edges in sorted(self.graph_processor.graph.adjacency_list.items()):
                    for eid, data in edges:
                        f.write(f"a {sid} {eid} {data.lower} {data.upper} {data.weight}\n")

            if new_halting_edges:
                for e in new_halting_edges:
                    f.write(f"a {e[0]} {e[1]} {e[2]} {e[3]} {e[4]}\n")
        if getattr(self, "print_out", False):
            print("Đã cập nhật các cung mới vào file TSG.txt.")
    
    def _write_node_lines(self, f, starts, targets, supply, vs_id, vt_id):
        for s in starts:
            # if(s == 855):
            #     pdb.set_trace()
            f.write(f"n {s} {supply if supply and vs_id == s else 1}\n")
        for t in targets:
            f.write(f"n {t.id} {-supply if supply and vt_id == t.id else -1}\n")
    
    def _write_edge_lines(self, f, edge):
        if edge is None: 
            return
        M = self.graph_processor.M
        H = self.graph_processor.H
        if edge.weight == H * H \
            and (edge.start_node.id // M - (edge.start_node.id % M == 0)) >= H:
            f.write(f"c Exceed {edge.weight} {edge.weight // M}\n")
        f.write(f"a {edge.start_node.id} {edge.end_node.id} "
            f"{edge.lower} {edge.upper} {edge.weight}\n")