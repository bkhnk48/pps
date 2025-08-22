from controller.reading_input_processor import ReadingInputProcessor
import re
import config
import warnings
from model.Logger import Logger
import os

ALLOWED_MAP_CHARS = set(".@OTSGW")
ALLOWED_ROW_RE = re.compile(r'^[.@OTSGW]+$')  # Only allowed map symbols (no spaces)
INT_TOKEN_RE = re.compile(r'^[+-]?\d+$')  # Only plain integer tokens (no commas, dots, letters)

class ReadingBenchmarkMapProcessor(ReadingInputProcessor):
    def _read_lines(self, filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n").rstrip("\r") for line in f]

    def _is_effectively_empty_file(self, filepath) -> bool:
        try:
            if os.path.getsize(filepath) == 0:
                return True
        except Exception:
            pass
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for raw in f:
                    if raw.strip():
                        return False
            return True
        except Exception:
            return False

    # -------------------- Validation Helpers --------------------
    def _map_error(self, msg):
        raise ValueError(f"[BENCHMARK ERROR] {msg}")

    def _map_warn(self, msg):
        if not hasattr(self, "_map_warnings"):
            self._map_warnings = []
        self._map_warnings.append(msg)
        try:
            if not hasattr(self, "_logger"):
                self._logger = Logger()
            self._logger.log(f"[MAP WARN] {msg}")
        except Exception:
            pass
        warnings.warn(f"[MAP WARN] {msg}", UserWarning, stacklevel=2)

    def get_map_warnings(self):
        return getattr(self, "_map_warnings", [])

    def _dimacs_error(self, msg):
        raise ValueError(f"[DIMACS ERROR] {msg}")

    # Quick format detection
    def _detect_input_format(self, filepath):
        bench_hits = 0
        dimacs_hits = 0
        a_hits = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for raw in f:
                    s = raw.strip()
                    if not s:
                        continue
                    sl = s.lower()
                    if sl.startswith('type ') or sl.startswith('height ') or sl.startswith('width ') or s == 'map':
                        bench_hits += 1
                        continue
                    if ALLOWED_ROW_RE.match(s):
                        bench_hits += 1
                        continue
                    tok = sl.split()[0]
                    if tok in ('a', 'p', 'n', 'c', 'alpha', 'beta', '#'):
                        dimacs_hits += 1
                        if tok == 'a':
                            a_hits += 1
                        continue
            if bench_hits > 0:
                return 'benchmark'
            if a_hits > 0 or dimacs_hits > 1:
                return 'dimacs'
            return 'unknown'
        except Exception:
            return 'unknown'

    def _sanitize_row(self, row, r_index):
        # Replace invalid characters with '@'
        if ALLOWED_ROW_RE.match(row):
            return row
        chars = list(row)
        changed = False
        for c, ch in enumerate(chars):
            if ch not in ALLOWED_MAP_CHARS:
                changed = True
                self._map_warn(f"Invalid character '{ch}' at (row={r_index}, col={c}) -> replaced by '@'")
                chars[c] = '@'
        return ''.join(chars) if changed else row

    def _validate_parsed_map(self, movement_type, height, width, map_grid):
        # if movement_type != "octile":
        #     return self._map_error("type must be 'octile'")
        if not isinstance(height, int) or not isinstance(width, int):
            return self._map_error("height/width must be integers")
        if height <= 0 or width <= 0:
            return self._map_error("height and width must be positive")
        if len(map_grid) != height:
            return self._map_error(f"Map line count ({len(map_grid)}) does not match height ({height})")

        walkable_found = False
        for i, row in enumerate(map_grid, 1):
            if len(row) != width:
                return self._map_error(f"Map row {i} has length {len(row)} != width ({width})")
            sanitized = self._sanitize_row(row, i - 1)
            if sanitized is not row:
                map_grid[i - 1] = sanitized
            if any(ch in ('.', 'S') for ch in sanitized):
                walkable_found = True

        if not walkable_found:
            return self._map_error("No walkable cell ('.' or 'S') found")

        self._last_parsed_map = (movement_type, height, width, map_grid)
        return True

    def _is_valid_benchmark_map(self, lines):
        # Fast header existence check
        if not lines:
            raise ValueError("[MAP ERROR] Empty file")
        needed = {
            'type': any(l.strip().lower().startswith('type') for l in lines),
            'height': any(l.strip().lower().startswith('height') for l in lines),
            'width': any(l.strip().lower().startswith('width') for l in lines),
            'map': any(l.strip() == 'map' for l in lines)
        }
        for k, ok in needed.items():
            if not ok:
                return self._map_error(f"Missing '{k}' line")
        try:
            movement_type, height, width, map_grid = self.parse_map_file(lines)
        except Exception as e:
            return self._map_error(f"Cannot parse file: {e}")
        return self._validate_parsed_map(movement_type, height, width, map_grid)

    # -------------------- Streaming Parse (preferred) --------------------
    def _parse_validate_map_stream(self, filepath):
        movement_type = height = width = None
        map_grid = []
        in_map = False
        seen_type = seen_height = seen_width = False
        line_no = 0
        had_non_empty = False
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for raw in f:
                line_no += 1
                s = raw.rstrip('\n').rstrip('\r')
                if not s:
                    if in_map:
                        self._map_error(f"Empty line inside map at line {line_no}")
                    continue
                had_non_empty = True
                if not in_map:
                    if ALLOWED_ROW_RE.match(s) and not (s.lower().startswith('type ') or
                                                        s.lower().startswith('height ') or
                                                        s.lower().startswith('width ') or
                                                        s == 'map'):
                        self._map_error("Map row encountered before 'map' line")
                    parts = s.split()
                    key = parts[0].lower()
                    if key == 'type':
                        if seen_type:
                            self._map_error("Duplicate 'type' line")
                        if len(parts) < 2:
                            self._map_error("Malformed type line")
                        movement_type = parts[1].lower()
                        seen_type = True
                    elif key == 'height':
                        if seen_height:
                            self._map_error("Duplicate 'height' line")
                        if len(parts) != 2 or not parts[1].isdigit():
                            self._map_error("Malformed height line")
                        height = int(parts[1])
                        seen_height = True
                    elif key == 'width':
                        if seen_width:
                            self._map_error("Duplicate 'width' line")
                        if len(parts) != 2 or not parts[1].isdigit():
                            self._map_error("Malformed width line")
                        width = int(parts[1])
                        seen_width = True
                    elif s == 'map':
                        in_map = True
                        missing = []
                        if movement_type is None:
                            missing.append("type")
                        if height is None:
                            missing.append("height")
                        if width is None:
                            missing.append("width")
                        if missing:
                            self._map_error("Missing header(s): " + ", ".join(missing))
                    else:
                        self._map_error(f"Unexpected line before 'map': '{s}'")
                else:
                    # Inside map region
                    if len(map_grid) >= height:
                        self._map_error("Extra map row beyond declared height")
                    if len(s) != width:
                        self._map_error(f"Map row {len(map_grid)+1} length {len(s)} != width {width}")
                    map_grid.append(self._sanitize_row(s, len(map_grid)))
        if not had_non_empty:
            raise ValueError("[MAP ERROR] Empty file")
        if not in_map:
            self._map_error("Missing 'map' line")
        missing = []
        if movement_type is None:
            missing.append("type")
        if height is None:
            missing.append("height")
        if width is None:
            missing.append("width")
        if missing:
            self._map_error("Missing header(s): " + ", ".join(missing))
        if len(map_grid) != height:
            self._map_error(f"Map line count ({len(map_grid)}) does not match height ({height})")
        return self._validate_parsed_map(movement_type, height, width, map_grid)

    def _dimacs_int(self, token: str, field_name: str, line_no: int) -> int:
        if not INT_TOKEN_RE.match(token):
            self._dimacs_error(
                f"Line {line_no}: invalid character in field '{field_name}': '{token}' (must be integer)"
            )
        try:
            return int(token)
        except Exception:
            self._dimacs_error(f"Line {line_no}: field '{field_name}' must be integer, got '{token}'")

    # -------------------- DIMACS format detection & validation --------------------
    def _is_valid_dimacs_file(self, filepath):
        edge_count = 0
        max_node_id = 0
        declared_nodes = None
        declared_edges = None

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line_no, raw in enumerate(f, 1):
                s = raw.strip()
                if not s:
                    continue
                parts = s.split()
                tag = parts[0].lower()

                if tag == 'a':
                    if len(parts) < 6:
                        self._dimacs_error(
                            f"Line {line_no}: 'a' line must have at least 6 fields: a source target lower upper cost"
                        )
                    # Parse mandatory integer fields with strict char check
                    source = self._dimacs_int(parts[1], 'source', line_no)
                    target = self._dimacs_int(parts[2], 'target', line_no)
                    lower  = self._dimacs_int(parts[3], 'lower',  line_no)
                    upper  = self._dimacs_int(parts[4], 'upper',  line_no)
                    cost   = self._dimacs_int(parts[5], 'cost',   line_no)
                    if source <= 0 or target <= 0:
                        self._dimacs_error(f"Line {line_no}: source/target must be positive integers (> 0)")
                    if upper < lower:
                        self._dimacs_error(f"Line {line_no}: upper ({upper}) < lower ({lower})")
                    edge_count += 1
                    max_node_id = max(max_node_id, source, target)

                elif tag == 'p':
                    if len(parts) < 4:
                        self._dimacs_error(f"Line {line_no}: malformed 'p' line. Expect: p <type> <nodes> <edges>")
                    declared_nodes = self._dimacs_int(parts[2], 'nodes', line_no)
                    declared_edges = self._dimacs_int(parts[3], 'edges', line_no)
                    if declared_nodes <= 0:
                        self._dimacs_error(f"Line {line_no}: declared nodes must be > 0")
                    if declared_edges < 0:
                        self._dimacs_error(f"Line {line_no}: declared edges must be >= 0")

                elif tag == 'n':
                    if len(parts) < 3:
                        self._dimacs_error(f"Line {line_no}: malformed 'n' line. Expect: n <id> <value>")
                    nid  = self._dimacs_int(parts[1], 'id',    line_no)
                    nval = self._dimacs_int(parts[2], 'value', line_no)
                    if nid <= 0:
                        self._dimacs_error(f"Line {line_no}: node id must be > 0")
                    max_node_id = max(max_node_id, nid)

                elif tag in ('c', 'alpha', 'beta', '#'):
                    if tag == 'c' and len(parts) >= 2 and parts[1].lower() == 'n':
                        for i, tok in enumerate(parts[2:], start=1):
                            _ = self._dimacs_int(tok, f"c n param[{i}]", line_no)
                    if tag in ('alpha', 'beta') and len(parts) >= 2:
                        _ = self._dimacs_int(parts[1], tag, line_no)
                    continue

                else:
                    self._dimacs_error(
                        f"Line {line_no}: unexpected token '{parts[0]}'. Expected one of: a, p, n, c, alpha, beta"
                    )

        if edge_count == 0:
            self._dimacs_error("No 'a' arc lines found")
        if declared_edges is not None and edge_count != declared_edges:
            self._dimacs_error(
                f"Edge count mismatch: file has {edge_count} 'a' lines but 'p' declares {declared_edges}"
            )
        if declared_nodes is not None and max_node_id > declared_nodes:
            self._dimacs_error(
                f"Node id {max_node_id} exceeds declared nodes {declared_nodes}"
            )
        return True

    def read_map_file(self, filepath, parsed=None):
        # Parse (streaming) if not already parsed
        if parsed is None:
            if getattr(self, '_last_parsed_map', None) is None:
                if not self._parse_validate_map_stream(filepath):
                    return []
            parsed = self._last_parsed_map

        movement_type, height, width, map_grid = parsed
        unit_length = self.extract_unit_length(filepath)
        edges = self.generate_dimacs_edges(map_grid, movement_type, unit_length)
        self.build_node_ids(map_grid)  
        self.M = height * width
        self.space_edges = [
            ['a', str(e[0]), str(e[1]), str(e[2]), str(e[3]), str(e[4])]
            for e in edges
        ]
        config.M = self.M
        return self.space_edges

    def process_input_file(self, filepath):
        try:
            if self._is_effectively_empty_file(filepath):
                raise ValueError("[MAP ERROR] Empty file")
        except FileNotFoundError:
            raise
        except Exception:
            pass

        fmt = self._detect_input_format(filepath)
        if fmt == 'benchmark':
            try:
                if self._parse_validate_map_stream(filepath):
                    result = self.read_map_file(filepath, parsed=self._last_parsed_map)
                    if getattr(self, 'print_out', False):
                        print(f"Parsed benchmark map successfully, M = {self.M}")
                    return result
            except Exception as e:
                raise
        if fmt == 'dimacs':
            try:
                if self._is_valid_dimacs_file(filepath):
                    return super().process_input_file(filepath)
            except Exception:
                raise
        bench_err = None
        dimacs_err = None
        try:
            self._parse_validate_map_stream(filepath)
            return self.read_map_file(filepath, parsed=self._last_parsed_map)
        except Exception as e:
            bench_err = str(e)
        try:
            if self._is_valid_dimacs_file(filepath):
                return super().process_input_file(filepath)
        except Exception as e:
            dimacs_err = str(e)
        def is_tagged(msg: str) -> bool:
            return isinstance(msg, str) and (
                msg.startswith("[BENCHMARK ERROR]") or msg.startswith("[DIMACS ERROR]") or msg.startswith("[MAP ERROR]")
            )
        if is_tagged(bench_err):
            raise ValueError(bench_err)
        if is_tagged(dimacs_err):
            raise ValueError(dimacs_err)
        raise ValueError("Invalid file format. Not a Benchmark map nor a valid DIMACS file.")