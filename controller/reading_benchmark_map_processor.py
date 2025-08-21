from controller.reading_input_processor import ReadingInputProcessor
import re
import config
import warnings
from model.Logger import Logger

ALLOWED_MAP_CHARS = set(".@OTSGW")
ALLOWED_ROW_RE = re.compile(r'^[.@OTSGW]+$')  # Only allowed map symbols (no spaces)

class ReadingBenchmarkMapProcessor(ReadingInputProcessor):
    def _read_lines(self, filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n").rstrip("\r") for line in f]

    # -------------------- Validation Helpers --------------------
    def _map_error(self, msg):
        raise ValueError(f"[MAP ERROR] {msg}")

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
            return self._map_error("Empty file")
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
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for raw in f:
                line_no += 1
                s = raw.rstrip('\n').rstrip('\r')
                if not s:
                    if in_map:
                        self._map_error(f"Empty line inside map at line {line_no}")
                    continue
                if not in_map:
                    # Detect accidental map row before 'map'
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
        if self._parse_validate_map_stream(filepath):
            result = self.read_map_file(filepath, parsed=self._last_parsed_map)
            if self.print_out:
                print(f"Parsed benchmark map successfully, M = {self.M}")
            return result
        return super().process_input_file(filepath)