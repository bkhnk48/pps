from model.BenchmarkNode import BenchmarkNode
from model.BenchmarkEdge import BenchmarkEdge
import os

class BenchmarkGraph:
    def __init__(self, height=-1, width=-1, is_octile=False, file_map=None):
        self.height = height
        self.width = width
        self.is_octile = is_octile
        self.found_type = 0
        self.found_height = 0
        self.found_width = 0
        self.found_map = 0
        self.prev_line = ""
        self.curr_line = ""
        # Default map file path
        if file_map is None:
            self.file_map = os.path.join("data", "Benchmark", "simplest.map")
        else:
            self.file_map = file_map
        self.V = {}  # node.id -> BenchmarkNode
        self.E = {}  # edge_key -> BenchmarkEdge

    def get_edge_key(self, a, b):
        # Cantor pairing for undirected edge key
        u, v = min(a, b), max(a, b)
        s = u + v
        return int(s * (s + 1) / 2 + v)

    def add_node(self, node):
        # Add node to graph
        if not isinstance(node, BenchmarkNode):
            raise ValueError("node must be BenchmarkNode")
        self.V[node.id] = node

    def add_edge(self, edge):
        # Add edge to graph
        if not isinstance(edge, BenchmarkEdge):
            raise ValueError("edge must be BenchmarkEdge")
        key = self.get_edge_key(edge.start_node.id, edge.end_node.id)
        self.E[key] = edge

    def _check_valid(self, line):
        # Check and parse map file header
        if line.startswith("type"):
            self.found_type += 1
            if self.found_type > 1:
                raise ValueError("Multiple 'type' lines")
            if "octile" in line:
                self.is_octile = True
        elif line.startswith("height"):
            self.found_height += 1
            if self.found_height > 1:
                raise ValueError("Multiple 'height' lines")
            self.height = int(line.split()[-1])
            if self.height < 1:
                raise ValueError("Height must be positive")
        elif line.startswith("width"):
            self.found_width += 1
            if self.found_width > 1:
                raise ValueError("Multiple 'width' lines")
            self.width = int(line.split()[-1])
            if self.width < 1:
                raise ValueError("Width must be positive")
        elif line.strip() == "map":
            self.found_map += 1
            if self.found_map > 1:
                raise ValueError("Multiple 'map' lines")
        elif (self.found_type == 1 and self.found_height == 1 and
              self.found_width == 1 and self.found_map == 1):
            return True
        return False

    def connect(self, i, j, allowed_chars={'.', 'S'}, disallowed_chars={'T', 'W', '@'}):
        # Connect node to neighbors if allowed
        id = j + self.width * i
        if j > 0 and self.curr_line[j-1] in allowed_chars:
            left_id = (j-1) + self.width * i
            self.add_edge(BenchmarkEdge(self.V[id], self.V[left_id], 0, 1, 1))
        if i > 0 and self.prev_line[j] in allowed_chars:
            above_id = j + self.width * (i-1)
            self.add_edge(BenchmarkEdge(self.V[id], self.V[above_id], 0, 1, 1))
        if self.is_octile:
            if i > 0 and j > 0 and self.prev_line[j-1] in allowed_chars:
                diag_id = (j-1) + self.width * (i-1)
                self.add_edge(BenchmarkEdge(self.V[id], self.V[diag_id], 0, 1, 1))
            if i > 0 and j < self.width-1 and self.prev_line[j+1] in allowed_chars:
                diag_id = (j+1) + self.width * (i-1)
                self.add_edge(BenchmarkEdge(self.V[id], self.V[diag_id], 0, 1, 1))
        elif self.curr_line[j] not in disallowed_chars:
            print(f"Warning: Character '{self.curr_line[j]}' is invalid. By default, this cell is considered non-walkable.")

    def reset_state(self):
        # Reset graph state before reading new map
        self.found_type = 0
        self.found_height = 0
        self.found_width = 0
        self.found_map = 0
        self.prev_line = ""
        self.curr_line = ""
        self.V = {}
        self.E = {}

    def _get_valid_map_path(self, file_path):
        # Get valid map file path, fallback to default if not found
        if file_path is None:
            file_path = self.file_map
        if not os.path.exists(file_path):
            file_path = os.path.join("data", "Benchmark", "simplest.map")
        return file_path

    def generate_space_graph(self, file_path=None):
        # Generate graph from map file
        self.reset_state()
        file_path = self._get_valid_map_path(file_path)
        self.file_map = file_path
        i = 0
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if self._check_valid(line):
                    self.curr_line = line
                    for j in range(self.width):
                        if self.curr_line[j] in {'.', 'S'}:
                            id = j + self.width * i
                            node = BenchmarkNode(id)
                            self.add_node(node)
                            self.connect(i, j)
                    self.prev_line = self.curr_line
                    i += 1
        if self.found_map == 0:
            raise ValueError("Missing map line")
        if self.height == -1 or self.width == -1:
            raise ValueError("Missing height or width")

    def export_space_graph_dimacs_file(self, space_graph_file_path="./BenchmarkGraph.txt"):
        # Export graph to DIMACS format
        edges_list = list(self.E.values())
        edges_list.sort(key=lambda e: (e.start_node.id, e.end_node.id))
        with open(space_graph_file_path, "w", encoding="utf-8") as f:
            for edge in edges_list:
                u = edge.start_node.id
                v = edge.end_node.id
                lower = edge.lower
                upper = edge.upper
                weight = edge.weight
                if lower is None or upper is None or weight is None:
                    raise ValueError(f"Missing lower/upper/weight for edge {u}→{v}")
                if upper < lower:
                    raise ValueError(f"upper < lower for edge {u}→{v}")
                line = f"a {u} {v} {lower} {upper} {weight}\n"
                f.write(line)