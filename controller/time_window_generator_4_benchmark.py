from __future__ import annotations
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional

from controller.time_window_generator import TimeWindowGenerator
import config


class TimeWindowGenerator4Benchmark(TimeWindowGenerator):
    SCEN_SPLIT_RE = re.compile(r'\s+')

    # ---------- helpers ----------
    def _project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def _benchmark_dir(self) -> str:
        return os.path.join(self._project_root(), 'data', 'benchmark')

    def _parse_scen_file(self, path: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
                for raw in f:
                    s = raw.strip()
                    if not s or s.lower().startswith('version'):
                        continue
                    parts = self.SCEN_SPLIT_RE.split(s)
                    if len(parts) < 9:
                        continue
                    rows.append({
                        'bucket': parts[0],
                        'map': parts[1],
                        'width': int(parts[2]),
                        'height': int(parts[3]),
                        'sx': int(parts[4]),
                        'sy': int(parts[5]),
                        'gx': int(parts[6]),
                        'gy': int(parts[7]),
                        'opt': float(parts[8]),
                    })
        except Exception:
            pass
        return rows

    def _gather_scenarios_for_map(self, bench_dir: str, map_basename: str) -> List[Dict[str, Any]]:
        cases: List[Dict[str, Any]] = []
        for root, _, files in os.walk(bench_dir):
            for fn in files:
                if not fn.lower().endswith('.scen'):
                    continue
                scen_path = os.path.join(root, fn)
                for row in self._parse_scen_file(scen_path):
                    if os.path.basename(row['map']) == map_basename:
                        row['__scen_path'] = scen_path
                        cases.append(row)
        return cases

    # ---------- override ----------
    def add_time_window_first_time(self, num_of_agvs: int = 0, speed: float = 1.0,
                                   bench_dir: Optional[str] = None):
        fmt = getattr(self, "_input_format", None)
        if fmt != 'benchmark':
            return super().add_time_window_first_time(num_of_agvs)

        parsed = getattr(self, "_last_parsed_map", None)
        if not parsed:
            return
        movement_type, height, width, map_grid = parsed

        M = getattr(self, "M", height * width)

        bench_dir = bench_dir or self._benchmark_dir()

        current_map_path = getattr(config, 'filepath', None)
        map_name = os.path.basename(current_map_path) if current_map_path else None
        if not map_name:
            return

        scenarios = self._gather_scenarios_for_map(bench_dir, map_name)
        if not scenarios:
            return super().add_time_window_first_time(num_of_agvs)

        node_id = self.build_node_ids(map_grid)

        self.started_nodes = []
        self.ID = []
        self.earliness = []
        self.tardiness = []
        self.alpha = 1
        self.beta = 1

        for row in scenarios:
            sx, sy = row['sx'], row['sy']
            gx, gy = row['gx'], row['gy']

            start_rc = (sy, sx)  # (row, col)
            goal_rc = (gy, gx)

            if start_rc not in node_id or goal_rc not in node_id:
                continue

            u = node_id[start_rc]
            v = node_id[goal_rc]

            start_ts = np.int64(u)
            goal_space = np.int64(v)

            spd = float(speed) if speed else 1.0
            e_val = int(round(row['opt'] / spd))
            if e_val < 0:
                e_val = 0
            e = np.int64(e_val)
            t = np.int64(e_val + 1)

            self.started_nodes.append(start_ts)
            self.ID.append(goal_space)
            self.earliness.append(e)
            self.tardiness.append(t)

        print(f'Start: {self.started_nodes} \n End: {self.ID} \n Earliness: {self.earliness} \n Tardiness: {self.tardiness}')

        config.started_nodes = list(self.started_nodes)
        config.ID = list(self.ID)
        config.earliness = list(self.earliness)
        config.tardiness = list(self.tardiness)
        config.numOfAGVs = len(self.ID)
        config.num_max_agvs = len(self.ID)

        # for _ in range(len(self.ID)):
        #     # add_time_window_constraints() tiêu thụ phần tử đầu tiên qua get_initial_conditions
        #     self.add_time_window_constraints()