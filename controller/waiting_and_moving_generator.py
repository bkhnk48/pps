from controller.NodeGenerator import TimeWindowNode
from controller.time_window_generator import TimeWindowGenerator
import pdb

#Sẽ được lớp EdgeModifier kế thừa
class WaitingAndMovingEdgesGenerator (TimeWindowGenerator):
    def __init__(self, dm):
        super().__init__(dm) 
        self._graph = None

    # Getter và Setter cho graph
    @property
    def graph(self):
        return self._graph
    
    @graph.setter
    def graph(self, value):
        self._graph = value
    
    def get_ts_edges(self, checking_list):
        """Lấy danh sách các cạnh tạm thời."""
        if checking_list is None:
            #return self.ts_edges
            return self.ts_edges
        return [[item[1].start_node.id, item[1].end_node.id] 
                for sublist in checking_list.values() for item in sublist]
        
    def is_edge_present(self, ID, j, ts_edges):
        """Kiểm tra xem cạnh đã tồn tại trong ts_edges chưa."""
        #return any(edge[0] == ID and edge[1] == j for edge in ts_edges)
        #pdb.set_trace()
        for i, e in enumerate(ts_edges):
            if isinstance(e, list):
                if(e[0] == ID and e[1] == j):
                    return True
            else:
                if(e.start_node.id == ID and e.end_node.id == j):
                    return True
                #pdb.set_trace()
                #print(f"[!] self.ts_edges[{i}] là list: {e}")
        #if(len(ts_edges) == 0):
        #    return False
        return False
        #return any(edge.start_node.id == ID and edge.end_node.id == j for edge in ts_edges)
    
    def create_edge_output(self, output_lines, ID, j, cost_info, checking_list):
        """Tạo dòng output cho cạnh mới và thêm vào danh sách."""
        upper, cost = cost_info
        if ((ID // self.M - (1 if ID % self.M == 0 else 0))>= self.H):
            output_lines.append(f"a {ID} {j} 0 1 {cost} Exceed")
        else:
            output_lines.append(f"a {ID} {j} 0 {upper} {cost}")

        """if checking_list is None:
            self.ts_edges.append((ID, j, 0, upper, cost))"""

        self.check_and_add_nodes([ID, j])
        edge = self.find_node(ID).create_edge(self.find_node(j), self.M, self.d, [ID, j, 0, upper, cost])
        if checking_list is None:
            self.ts_edges.append(edge)
            
    def create_holding_edge_output(self, output_lines, ID, j, checking_list):
        """Tạo dòng output cho cạnh holding và thêm vào danh sách."""
        output_lines.append(f"a {ID} {j} 0 1 {self.d}")

        """if checking_list is None:
            self.ts_edges.append((ID, j, 0, 1, self.d))"""

        self.check_and_add_nodes([ID, j])
        edge = self.find_node(ID).create_edge(self.find_node(j), self.M, self.d, [ID, j, 0, 1, self.d])
        if checking_list is None:
            self.ts_edges.append(edge)
            
    def init_nodes_n_edges(self):
        #no longer use self.tsedges
        for edge in self.ts_edges:
            if edge is not None:
                self.insertEdgesAndNodes(edge.start_node, edge.end_node, edge)
                
    def update_edges_after_restrictions(self, R):
        """Cập nhật danh sách các cạnh sau khi áp dụng hạn chế."""
        #assert len(self._edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.ts_edges)}"
        #self.ts_edges = [e for e in self._edges if [e[0], e[1]] not in [r[:2] for r in R]]
        self.ts_edges = [e for e in self.ts_edges if [e.start_node.id, e.end_node.id] not in [r[:2] for r in R]]
        
    def create_new_edges(self, restriction, R, maxid):
        """Tạo các cạnh mới dựa trên các hạn chế đã chỉ định."""
        a_s, a_t, a_sub_t = maxid, maxid + 1, maxid + 2
        self.check_and_add_nodes([a_s, a_t, a_sub_t], True, "Restriction")

        self.restriction_controller.add_nodes_and__re_node(
            R[0][0], R[0][1], restriction, a_s, a_t
        )

        new_edges = {
            (a_s, a_t, 0, self.H, int(self.gamma/self.alpha)),
            (a_s, a_sub_t, 0, self.ur, 0),
            (a_sub_t, a_t, 0, self.H, 0)
        }

        for e in R:
            new_edges.add((e[0], a_s, 0, 1, 0))
            new_edges.add((a_t, e[1], 0, 1, e[2]))

        return new_edges
    
    def insert_halting_edges(self):
        #no longer use self.tsedges:
        halting_nodes = set()
        for edge in self.ts_edges:
            if(isinstance(edge.end_node, TimeWindowNode)):
                continue
            time = edge.end_node.id // self.M - (1 if edge.end_node.id % self.M == 0 else 0)
            if(time >= self.H):
                #print(f"time = {time} at node.id = {edge.end_node.id}")
                halting_nodes.add(edge.end_node.id)
        targets = self.get_targets()
        new_a = set()
        for h_node in halting_nodes:
            #pdb.set_trace()
            for target in targets:
                e = (h_node, target.id, 0, 1, self.H*self.H)
                new_a.update({e})
        #self.ts_edges.extend(e for e in new_a if e not in self.ts_edges)
        self.create_set_of_edges(new_a)
    def write_to_file(self, agv_id_and_new_start=None, new_halting_edges=None,
                  supply=None, vs_id=None, vt_id=None, filename="TSG.txt"):
        get_targets = self.get_targets \
            if hasattr(self, 'get_targets') \
                else self.graph_processor.get_targets
        targets = get_targets()
        M = max(target.id for target in targets)
        if new_halting_edges: M = max(M, max(e[1] for e in new_halting_edges))
        num_edges = (self.count_edges() \
            if hasattr(self, 'count_edges') \
                else len(self.ts_edges)) + (len(new_halting_edges) if new_halting_edges else 0)

        with open(filename, 'w') as f:
            f.write(f"p min {M} {num_edges}\n")
            starts = self.started_nodes#getattr(self, 'started_nodes', self.graph.getAllNewStartedNodes())
            self._write_node_lines(f, starts, targets, supply, vs_id, vt_id)

            if hasattr(self, 'ts_edges'):
                for e in self.ts_edges: self._write_edge_lines(f, e)
            elif hasattr(self, 'adjacency_list'):
                for sid, edges in sorted(self.adjacency_list.items()):
                    for eid, data in edges:
                        f.write(f"a {sid} {eid} {data.lower} {data.upper} {data.weight}\n")

            if new_halting_edges:
                for e in new_halting_edges:
                    f.write(f"a {e[0]} {e[1]} {e[2]} {e[3]} {e[4]}\n")

        if getattr(self, "print_out", False):
            print("Đã cập nhật các cung mới vào file TSG.txt.")

    def _write_edge_lines(self, f, edge):
        if edge is None: return
        if edge.weight == self.H * self.H \
            and (edge.start_node.id // self.M - (edge.start_node.id % self.M == 0)) >= self.H:
            f.write(f"c Exceed {edge.weight} {edge.weight // self.M}\n")
        f.write(f"a {edge.start_node.id} {edge.end_node.id} "
            f"{edge.lower} {edge.upper} {edge.weight}\n")
        
    def _write_node_lines(self, f, starts, targets, supply, vs_id, vt_id):
        for s in starts:
            f.write(f"n {s} {supply if supply and vs_id == s else 1}\n")
        for t in targets:
            f.write(f"n {t.id} {-supply if supply and vt_id == t.id else -1}\n")

