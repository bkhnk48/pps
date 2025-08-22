from controller.reading_input_processor import ReadingInputProcessor
import re
import config
import warnings
from model.Logger import Logger

ALLOWED_MAP_CHARS = set(".@OTSGW")
ALLOWED_ROW_RE = re.compile(r'^[.@OTSGW]+$')
INT_TOKEN_RE = re.compile(r'^[+-]?\d+$')
HEADER_PREFIX = ('type ', 'height ', 'width ')
DIMACS_TOKENS = {'a', 'p', 'n', 'c', 'alpha', 'beta', '#'}

class ReadingBenchmarkMapProcessor(ReadingInputProcessor):
    def _read_lines(self, filepath):
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            return [line.rstrip("\n").rstrip("\r") for line in f]

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

    def _is_ignorable_line(self, s: str) -> bool:
        return not s or s.startswith('```')

    # -------------------- Format detection --------------------
    def _detect_input_format(self, filepath):
        bench_hits = dimacs_hits = a_hits = 0
        non_empty_seen = 0
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                for raw in f:
                    s = raw.strip()
                    if self._is_ignorable_line(s):
                        continue
                    non_empty_seen += 1
                    sl = s.lower()
                    if sl.startswith(HEADER_PREFIX) or s == 'map':
                        return 'benchmark'
                    if ALLOWED_ROW_RE.match(s):
                        bench_hits += 1
                        if bench_hits >= 2:
                            return 'benchmark'
                        continue
                    tok = sl.split(' ', 1)[0]  # faster single split
                    if tok in DIMACS_TOKENS:
                        dimacs_hits += 1
                        if tok == 'a':
                            a_hits += 1
                            return 'dimacs'
                        if dimacs_hits >= 3:
                            return 'dimacs'
                    if non_empty_seen >= 64:
                        break
            if non_empty_seen == 0:
                return 'empty'
            if bench_hits > 0:
                return 'benchmark'
            if a_hits > 0 or dimacs_hits > 1:
                return 'dimacs'
            return 'unknown'
        except Exception:
            return 'unknown'

    # -------------------- Benchmark helpers --------------------
    def _sanitize_row(self, row, r_index):
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
        if not isinstance(height, int) or not isinstance(width, int):
            return self._map_error("height/width must be integers")
        if height <= 0 or width <= 0:
            return self._map_error("height and width must be positive")
        if len(map_grid) != height:
            return self._map_error(f"Map line count ({len(map_grid)}) does not match height ({height})")
        if not getattr(self, "_bench_walkable", False):
            return self._map_error("No walkable cell ('.' or 'S') found")
        self._last_parsed_map = (movement_type, height, width, map_grid)
        return True

    def _bench_state(self):
        return {
            'movement_type': None, 'height': None, 'width': None,
            'map_grid': [], 'in_map': False,
            'seen': {'type': False, 'height': False, 'width': False},
            'had_non_empty': False,
            'walkable_found': False,
        }

    def _bench_process_header(self, s, st, line_no):
        sl = s.lower()
        if ALLOWED_ROW_RE.match(s) and not (sl.startswith('type ') or
                                            sl.startswith('height ') or
                                            sl.startswith('width ') or
                                            s == 'map'):
            self._map_error("Map row encountered before 'map' line")
        parts = s.split()
        key = parts[0].lower()
        seen = st['seen']
        if key == 'type':
            if seen['type']:
                self._map_error("Duplicate 'type' line")
            if len(parts) < 2:
                self._map_error("Malformed type line")
            st['movement_type'] = parts[1].lower(); seen['type'] = True
        elif key == 'height':
            if seen['height']:
                self._map_error("Duplicate 'height' line")
            if len(parts) != 2 or not parts[1].isdigit():
                self._map_error("Malformed height line")
            st['height'] = int(parts[1]); seen['height'] = True
        elif key == 'width':
            if seen['width']:
                self._map_error("Duplicate 'width' line")
            if len(parts) != 2 or not parts[1].isdigit():
                self._map_error("Malformed width line")
            st['width'] = int(parts[1]); seen['width'] = True
        elif s == 'map':
            st['in_map'] = True
            missing = [k for k in ('type', 'height', 'width')
                       if (k == 'type' and st['movement_type'] is None) or
                          (k == 'height' and st['height'] is None) or
                          (k == 'width' and st['width'] is None)]
            if missing:
                self._map_error("Missing header(s): " + ", ".join(missing))
        else:
            self._map_error(f"Unexpected line before 'map': '{s}'")

    def _bench_process_map_row(self, s, st):
        h, w = st['height'], st['width']
        if len(st['map_grid']) >= h:
            self._map_error("Extra map row beyond declared height")
        if len(s) != w:
            self._map_error(f"Map row {len(st['map_grid'])+1} length {len(s)} != width {w}")
        sanitized = self._sanitize_row(s, len(st['map_grid']))
        st['map_grid'].append(sanitized)
        if not st['walkable_found'] and any(ch in ('.', 'S') for ch in sanitized):
            st['walkable_found'] = True

    def _bench_finalize(self, st):
        if not st['had_non_empty']:
            raise ValueError("[MAP ERROR] Empty file")
        if not st['in_map']:
            self._map_error("Missing 'map' line")
        vals = {'type': st['movement_type'], 'height': st['height'], 'width': st['width']}
        missing = [k for k, v in vals.items() if v is None]
        if missing:
            self._map_error("Missing header(s): " + ", ".join(missing))
        if len(st['map_grid']) != st['height']:
            self._map_error(f"Map line count ({len(st['map_grid'])}) does not match height ({st['height']})")
        self._bench_walkable = st['walkable_found']
        return self._validate_parsed_map(vals['type'], vals['height'], vals['width'], st['map_grid'])

    # -------------------- Benchmark parser (streaming) --------------------
    def _parse_validate_map_stream(self, filepath):
        st = self._bench_state()
        map_error = self._map_error
        proc_header = self._bench_process_header
        proc_row = self._bench_process_map_row
        with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line_no, raw in enumerate(f, 1):
                s = raw.rstrip('\n').rstrip('\r').strip()
                if self._is_ignorable_line(s):
                    if s and st['in_map']:
                        map_error(f"Empty line inside map at line {line_no}")
                    continue
                st['had_non_empty'] = True
                if not st['in_map']:
                    proc_header(s, st, line_no)
                else:
                    proc_row(s, st)
        return self._bench_finalize(st)

    # -------------------- DIMACS helpers --------------------
    def _dimacs_int(self, token: str, field_name: str, line_no: int) -> int:
        if not INT_TOKEN_RE.match(token):
            self._dimacs_error(f"Line {line_no}: invalid character in field '{field_name}': '{token}' (must be integer)")
        try:
            return int(token)
        except Exception:
            self._dimacs_error(f"Line {line_no}: field '{field_name}' must be integer, got '{token}'")

    def _dimacs_state(self):
        return {'edge_count': 0, 'max_node_id': 0, 'declared_nodes': None, 'declared_edges': None}

    def _dimacs_handle_a(self, parts, line_no, st):
        if len(parts) < 6:
            self._dimacs_error("Line {0}: 'a' line must have at least 6 fields: a source target lower upper cost".format(line_no))
        src = self._dimacs_int(parts[1], 'source', line_no)
        tgt = self._dimacs_int(parts[2], 'target', line_no)
        low = self._dimacs_int(parts[3], 'lower', line_no)
        upp = self._dimacs_int(parts[4], 'upper', line_no)
        cost = self._dimacs_int(parts[5], 'cost', line_no)
        if src <= 0 or tgt <= 0:
            self._dimacs_error(f"Line {line_no}: source/target must be positive integers (> 0)")
        if low < 0:
            self._dimacs_error(f"Line {line_no}: lower must be >= 0")
        if upp <= 0:
            self._dimacs_error(f"Line {line_no}: upper must be > 0")
        if upp < low:
            self._dimacs_error(f"Line {line_no}: upper ({upp}) < lower ({low})")
        st['edge_count'] += 1
        st['max_node_id'] = max(st['max_node_id'], src, tgt)

    def _dimacs_handle_p(self, parts, line_no, st):
        if len(parts) < 4:
            self._dimacs_error(f"Line {line_no}: malformed 'p' line. Expect: p <type> <nodes> <edges>")
        st['declared_nodes'] = self._dimacs_int(parts[2], 'nodes', line_no)
        st['declared_edges'] = self._dimacs_int(parts[3], 'edges', line_no)
        if st['declared_nodes'] <= 0:
            self._dimacs_error(f"Line {line_no}: declared nodes must be > 0")
        if st['declared_edges'] < 0:
            self._dimacs_error(f"Line {line_no}: declared edges must be >= 0")

    def _dimacs_handle_n(self, parts, line_no, st):
        if len(parts) < 3:
            self._dimacs_error(f"Line {line_no}: malformed 'n' line. Expect: n <id> <value>")
        nid = self._dimacs_int(parts[1], 'id', line_no)
        _ = self._dimacs_int(parts[2], 'value', line_no)
        if nid <= 0:
            self._dimacs_error(f"Line {line_no}: node id must be > 0")
        st['max_node_id'] = max(st['max_node_id'], nid)

    def _dimacs_handle_comment(self, tag, parts, line_no):
        if tag == 'c' and len(parts) >= 2 and parts[1].lower() == 'n':
            for i, tok in enumerate(parts[2:], start=1):
                _ = self._dimacs_int(tok, f"c n param[{i}]", line_no)
        if tag in ('alpha', 'beta') and len(parts) >= 2:
            _ = self._dimacs_int(parts[1], tag, line_no)

    def _dimacs_finalize(self, st):
        if st['edge_count'] == 0:
            self._dimacs_error("No 'a' arc lines found")
        if st['declared_edges'] is not None and st['edge_count'] != st['declared_edges']:
            self._dimacs_error(
                f"Edge count mismatch: file has {st['edge_count']} 'a' lines but 'p' declares {st['declared_edges']}"
            )
        if st['declared_nodes'] is not None and st['max_node_id'] > st['declared_nodes']:
            self._dimacs_error(f"Node id {st['max_node_id']} exceeds declared nodes {st['declared_nodes']}")
        return True

    # -------------------- DIMACS validator --------------------
    def _is_valid_dimacs_file(self, filepath):
        st = self._dimacs_state()
        dimacs_handle_a = self._dimacs_handle_a
        dimacs_handle_p = self._dimacs_handle_p
        dimacs_handle_n = self._dimacs_handle_n
        dimacs_handle_c = self._dimacs_handle_comment
        dimacs_error = self._dimacs_error
        with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line_no, raw in enumerate(f, 1):
                s = raw.strip()
                if self._is_ignorable_line(s):
                    continue
                parts = s.split()
                tag = parts[0].lower()
                if tag == 'a':
                    dimacs_handle_a(parts, line_no, st)
                elif tag == 'p':
                    dimacs_handle_p(parts, line_no, st)
                elif tag == 'n':
                    dimacs_handle_n(parts, line_no, st)
                elif tag in DIMACS_TOKENS:
                    dimacs_handle_c(tag, parts, line_no)
                else:
                    dimacs_error(
                        f"Line {line_no}: unexpected token '{parts[0]}'. Expected one of: a, p, n, c, alpha, beta"
                    )
        return self._dimacs_finalize(st)

    # -------------------- Reading & Orchestration --------------------
    def read_map_file(self, filepath, parsed=None):
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
        self.space_edges = [['a', str(e[0]), str(e[1]), str(e[2]), str(e[3]), str(e[4])] for e in edges]
        config.M = self.M
        return self.space_edges

    def _try_benchmark(self, filepath):
        if self._parse_validate_map_stream(filepath):
            result = self.read_map_file(filepath, parsed=self._last_parsed_map)
            if getattr(self, 'print_out', False):
                print(f"Parsed benchmark map successfully, M = {self.M}")
            return result

    def _try_dimacs(self, filepath):
        if self._is_valid_dimacs_file(filepath):
            return super().process_input_file(filepath)

    def _is_tagged(self, msg: str) -> bool:
        return isinstance(msg, str) and (
            msg.startswith("[BENCHMARK ERROR]") or msg.startswith("[DIMACS ERROR]") or msg.startswith("[MAP ERROR]")
        )

    def process_input_file(self, filepath):
        fmt = self._detect_input_format(filepath)
        if fmt == 'empty':
            raise ValueError("[MAP ERROR] Empty file")
        if fmt == 'benchmark':
            return self._try_benchmark(filepath)
        if fmt == 'dimacs':
            return self._try_dimacs(filepath)
        bench_err = dimacs_err = None
        try:
            return self._try_benchmark(filepath)
        except Exception as e:
            bench_err = str(e)
        try:
            return self._try_dimacs(filepath)
        except Exception as e:
            dimacs_err = str(e)
        if self._is_tagged(bench_err):
            raise ValueError(bench_err)
        if self._is_tagged(dimacs_err):
            raise ValueError(dimacs_err)
        raise ValueError("Invalid file format. Not a Benchmark map nor a valid DIMACS file.")