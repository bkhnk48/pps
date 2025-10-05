import pdb
from abc import ABC
import config
class ReroutingController:
    def __init__(self, graph_processor):
        super().__init__() 
        self.graph_processor = graph_processor
        self._started_nodes = graph_processor.started_nodes
        self._ts_edges = graph_processor.ts_edges

    def get_ts_edges(self):
        return getattr(self.graph_processor, 'ts_edges', [])

    def set_started_nodes(self, started_nodes):
        self._started_nodes = started_nodes

    def get_printable_edges(self, agv_id = None):
        return self.get_ts_edges()

    def _iter_edges_for_file(self):
        ts = getattr(self.graph_processor, 'ts_edges', None)
        if ts is not None and len(ts) > 0:
            for e in ts:
                yield e  
            return

        G = getattr(self.graph_processor, 'graph', None)
        if G is not None and hasattr(G, 'adjacency_list'):
            for sid, edges in sorted(G.adjacency_list.items()):
                for eid, data in edges:
                    yield (sid, eid, data.lower, data.upper, data.weight)
            return

        if G is not None and hasattr(G, 'edges'):
            for u, v, data in G.edges(data=True):
                lower = data.get('lower', 0)
                upper = data.get('upper', data.get('capacity', 1))
                weight = data.get('weight', data.get('cost', 0))
                yield (u, v, lower, upper, weight)

    def write_to_file(self, agv_id_and_new_start=None, new_halting_edges=None,
              supply=None, vs_id=None, vt_id=None, filename="TSG.txt"):
        targets = self.graph_processor.get_targets()

        M = max(target.id for target in targets)
        if new_halting_edges:
            M = max(M, max(e[1] for e in new_halting_edges))

        edges_main = list(self._iter_edges_for_file())
        num_edges = len(edges_main) + (len(new_halting_edges) if new_halting_edges else 0)

        with open(filename, 'w') as f:
            f.write(f"p min {M} {num_edges}\n")
            f.write(f"c number of spaces nodes is: {M}\n")
            starts = self._started_nodes if len(self._started_nodes) > 0 else self.graph_processor.started_nodes
            self._write_node_lines(f, starts, targets, supply, vs_id, vt_id)

            for e in edges_main:
                if hasattr(e, 'start_node'):
                    self._write_edge_lines(f, e)
                else:
                    f.write(f"a {e[0]} {e[1]} {e[2]} {e[3]} {e[4]}\n")

            if new_halting_edges:
                for e in new_halting_edges:
                    f.write(f"a {e[0]} {e[1]} {e[2]} {e[3]} {e[4]}\n")

        if getattr(self, "print_out", False):
            print("Đã cập nhật các cung mới vào file TSG.txt.")

    def _write_node_lines(self, f, starts, targets, supply, vs_id, vt_id):
        from controller.NodeGenerator import TimeWindowNode
        for t in targets:
            if isinstance(t, TimeWindowNode):
                f.write(f"c tw {t.id} {t.earliness} {t.tardiness}\n")
        for s in starts:
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
