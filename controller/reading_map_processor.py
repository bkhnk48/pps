from controller.reading_input_processor import ReadingInputProcessor
import re
import config

ALLOWED_MAP_CHARS = set(".@OTSGW")
ALLOWED_ROW_RE = re.compile(r'^[.@OTSGW]+$')

class ReadingMapProcessor(ReadingInputProcessor):
    def _read_lines(self, filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n") for line in f]

    # -------------------- Validation Helpers --------------------
    def _map_error(self, msg):
        if getattr(self, 'print_out', False):
            print(f"[MAP ERROR] {msg}")
        return False

    def _sanitize_row(self, row, r_index):
        if ALLOWED_ROW_RE.match(row):
            return row
        chars = list(row)
        changed = False
        for c, ch in enumerate(chars):
            if ch not in ALLOWED_MAP_CHARS:
                changed = True
                if getattr(self, 'print_out', False):
                    print(f"[MAP WARN] Invalid character '{ch}' at (row={r_index}, col={c}) -> treated as obstacle")
                chars[c] = '@'
        return ''.join(chars) if changed else row

    def _validate_parsed_map(self, movement_type, height, width, map_grid):
        if movement_type != "octile":
            return self._map_error("type must be 'octile'")
        if not isinstance(height, int) or not isinstance(width, int):
            return self._map_error("height/width must be integers")
        if height <= 0 or width <= 0:
            return self._map_error("height and width must be positive")
        if len(map_grid) != height:
            return self._map_error(
                f"Map line count ({len(map_grid)}) does not match height ({height})")
        for i, row in enumerate(map_grid, 1):
            if len(row) != width:
                return self._map_error(
                    f"Map row {i} has length {len(row)} != width ({width})")
            sanitized = self._sanitize_row(row, i-1)
            if sanitized is not row:
                map_grid[i-1] = sanitized
        self._last_parsed_map = (movement_type, height, width, map_grid)
        return True

    def _is_valid_benchmark_map(self, lines):
        if not lines:
            return self._map_error("Empty file")
        # Quick header presence check to avoid parsing when obviously invalid
        needed = {
            'type': any(l.strip().startswith('type') for l in lines),
            'height': any(l.strip().startswith('height') for l in lines),
            'width': any(l.strip().startswith('width') for l in lines),
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

    # -------------------- Streaming Parse --------------------
    def _parse_validate_map_stream(self, filepath):
        movement_type = height = width = None
        map_grid = []
        in_map = False
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for raw in f:
                s = raw.strip()
                if not s:
                    continue
                if not in_map:
                    if ALLOWED_ROW_RE.match(s):
                        return self._map_error("Map row encountered before 'map' line")
                    key, *rest = s.split(None, 1)
                    kl = key.lower()
                    if kl == 'type':
                        if not rest: return self._map_error("Malformed type line")
                        movement_type = rest[0].lower()
                    elif kl == 'height':
                        try: height = int(rest[0])
                        except: return self._map_error("Malformed height line")
                    elif kl == 'width':
                        try: width = int(rest[0])
                        except: return self._map_error("Malformed width line")
                    elif s == 'map':
                        if None in (movement_type, height, width):
                            return self._map_error("Header incomplete before 'map'")
                        in_map = True
                else:
                    if len(map_grid) >= height:
                        return self._map_error("More map rows than specified height")
                    if len(s) != width:
                        return self._map_error(f"Map row {len(map_grid)+1} has length {len(s)} != width ({width})")
                    map_grid.append(self._sanitize_row(s, len(map_grid)))
        if None in (movement_type, height, width):
            return self._map_error("Missing required header lines")
        if not map_grid:
            return self._map_error("No map rows after 'map' line")
        if len(map_grid) != height:
            return self._map_error(f"Map line count ({len(map_grid)}) does not match height ({height})")
        return self._validate_parsed_map(movement_type, height, width, map_grid)

    def read_map_file(self, filepath, parsed=None):
        if parsed is None:
            if getattr(self, '_last_parsed_map', None) is None:
                if not self._parse_validate_map_stream(filepath):
                    return []
            parsed = self._last_parsed_map
        movement_type, height, width, map_grid = parsed
        unit_length = self.extract_unit_length(filepath)
        edges = self.generate_dimacs_edges(map_grid, movement_type, unit_length)
        node_id = self.build_node_ids(map_grid)
        self.M = len(node_id)
        self.space_edges = [
            ['a', str(e[0]), str(e[1]), str(e[2]), str(e[3]), str(e[4])] for e in edges
        ]
        config.M = self.M
        return self.space_edges

    def process_input_file(self, filepath):
        if self._parse_validate_map_stream(filepath):
            result = self.read_map_file(filepath, parsed=self._last_parsed_map)
            if self.print_out:
                print(f"Parsed benchmark map successfully, M = {self.M}")
            return result
        return super().process_input_file(filepath)
