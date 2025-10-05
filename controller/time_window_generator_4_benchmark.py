from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from controller.time_window_generator import TimeWindowGenerator
from controller.NodeGenerator import TimeWindowNode
from controller.TimeWindowController import TimeWindowController
import config


class TimeWindowGenerator4Benchmark(TimeWindowGenerator):
    SCEN_SPLIT_RE = re.compile(r"\s+")

    # ---------- helpers ----------
    def _project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _benchmark_dir(self) -> str:
        return os.path.join(self._project_root(), "data", "benchmark")

    def _parse_scen_file(self, path: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                for raw in f:
                    s = raw.strip()
                    if not s or s.lower().startswith("version"):
                        continue
                    parts = self.SCEN_SPLIT_RE.split(s)
                    if len(parts) < 9:
                        continue
                    try:
                        rows.append(
                            {
                                "bucket": parts[0],
                                "map": parts[1],
                                "width": int(parts[2]),
                                "height": int(parts[3]),
                                "sx": int(parts[4]),
                                "sy": int(parts[5]),
                                "gx": int(parts[6]),
                                "gy": int(parts[7]),
                                "opt": float(parts[8]),
                            }
                        )
                    except Exception:
                        continue
        except Exception:
            # Missing/invalid scen file -> ignore
            pass
        return rows

    def _gather_scenarios_for_map(self, bench_dir: str, map_basename: str) -> List[Dict[str, Any]]:
        cases: List[Dict[str, Any]] = []
        for root, _, files in os.walk(bench_dir):
            for fn in files:
                if not fn.lower().endswith(".scen"):
                    continue
                scen_path = os.path.join(root, fn)
                for row in self._parse_scen_file(scen_path):
                    if os.path.basename(row["map"]) == map_basename:
                        row["__scen_path"] = scen_path
                        cases.append(row)
        return cases

    def _current_max_node_id(self) -> int:
        max_id = 0
        # From built time-space graph (benchmark path)
        tsg_nodes = getattr(self, "tsg_nodes", None)
        if isinstance(tsg_nodes, dict) and tsg_nodes:
            try:
                max_id = max(max_id, max(tsg_nodes.keys()))
            except Exception:
                pass
        # From edges recorded (objects with start_node/end_node)
        ts_edges = getattr(self, "ts_edges", None)
        if isinstance(ts_edges, list) and ts_edges:
            for e in ts_edges:
                try:
                    max_id = max(max_id, int(e.start_node.id), int(e.end_node.id))
                except Exception:
                    continue
        # From nodes list
        ts_nodes = getattr(self, "ts_nodes", None)
        if isinstance(ts_nodes, list) and ts_nodes:
            try:
                max_id = max(max_id, max(getattr(n, "id", 0) for n in ts_nodes))
            except Exception:
                pass
        M = getattr(self, "M", 0)
        H = getattr(self, "H", 0)
        if max_id == 0 and M and H:
            max_id = M * (H + 1)
        return int(max_id)

    # ------- override -------
    def add_time_window_first_time(
        self,
        num_of_agvs: int = 0,
    ) -> None:
        fmt = getattr(self, "_input_format", None)
        if fmt == "dimacs":
            return super().add_time_window_first_time(num_of_agvs)

        parsed = getattr(self, "_last_parsed_map", None)
        if not parsed:
            # Map not parsed yet -> cannot proceed
            return
        movement_type, height, width, map_grid = parsed
        node_id = self.build_node_ids(map_grid)

        scenarios = self._determine_scenarios()
        if not scenarios:
            return super().add_time_window_first_time(num_of_agvs)

        requested_agvs = self._ask_agv_count_once()
        speed = self._ask_speed_once()

        scenarios = self._decide_take(scenarios, requested_agvs, num_of_agvs)

        self._init_state_and_controller()

        created_targets = self._build_entries_per_scenario(scenarios, node_id, speed)

        self._wire_targets_into_controller(created_targets)

        self._materialize_time_window_edges(created_targets)

        self._update_config_after_generation()

        print(
                f"Start: {self.started_nodes}\nEnd: {self.ID}\n"
                f"Earliness: {self.earliness}\nTardiness: {self.tardiness}"
            )

    # ------- helpers -------
    def _determine_scenarios(self) -> List[Dict[str, Any]]:
        # Determine which .scen files to use (matching current map name)
        current_map_path = getattr(config, "filepath", None)
        map_name = os.path.basename(current_map_path) if current_map_path else None
        bench_dir = self._benchmark_dir()
        scenarios = self._gather_scenarios_for_map(bench_dir, map_name) if map_name else []
        return scenarios

    def _ask_agv_count_once(self) -> int:
        # Ask how many AGVs to use
        requested_agvs = config.benchmark_agv_count
        if requested_agvs is None:
            try:
                agv_in = input("Enter number of AGVs (press Enter to use all scenarios from .scen files): ").strip()
            except Exception:
                agv_in = ""
            if agv_in:
                try:
                    requested_agvs = int(agv_in)
                except Exception:
                    requested_agvs = 0
            else:
                requested_agvs = 0
            config.benchmark_agv_count = requested_agvs
        return requested_agvs or 0

    def _ask_speed_once(self) -> float:
        # Ask for speed only the first time
        speed = config.benchmark_agv_speed if config.benchmark_agv_speed is not None else None
        if speed is None:
            try:
                sp_in = input("Enter AGV speed (cells per time unit, default 1): ").strip()
            except Exception:
                sp_in = ""
            try:
                speed = float(sp_in) if sp_in else 1.0
                if speed <= 0:
                    speed = 1.0
            except Exception:
                speed = 1.0
            config.benchmark_agv_speed = speed
        return float(speed)

    def _decide_take(self, scenarios: List[Dict[str, Any]], requested_agvs: int, num_of_agvs: int) -> List[Dict[str, Any]]:
        # Decide how many scenarios to take
        if isinstance(requested_agvs, int) and requested_agvs > 0:
            take = requested_agvs
        elif isinstance(num_of_agvs, int) and num_of_agvs > 0:
            take = num_of_agvs
        else:
            take = len(scenarios)
        return scenarios[:take]

    def _init_state_and_controller(self) -> None:
        self.started_nodes = []
        self.ID = []
        self.earliness = []
        self.tardiness = []
        self.alpha = 1
        self.beta = 1
        if self.time_window_controller is None:
            self.time_window_controller = TimeWindowController(self.alpha, self.beta, self.gamma, self.d, self.H)

    def _build_entries_per_scenario(
        self,
        scenarios: List[Dict[str, Any]],
        node_id: Dict[Tuple[int, int], int],
        speed: float,
    ) -> List[Tuple[int, TimeWindowNode]]:
        # Build entries per scenario
        cur_max = self._current_max_node_id()
        created_targets: List[Tuple[int, TimeWindowNode]] = []
        for row in scenarios:
            sx, sy, gx, gy = row["sx"], row["sy"], row["gx"], row["gy"]
            start_rc = (sy, sx)  # (row, col) = (y, x)
            goal_rc = (gy, gx)
            if start_rc not in node_id or goal_rc not in node_id:
                continue
            u = int(node_id[start_rc])  # space id of start
            v = int(node_id[goal_rc])   # space id of goal
            # time-space start at i=0 -> id=u
            self.started_nodes.append(u)
            # earliness/tardiness from optimal length and speed
            e_val = int(round(row["opt"] / (speed if speed else 1.0)))
            if e_val < 0:
                e_val = 0
            t_val = e_val + 1
            self.earliness.append(e_val)
            self.tardiness.append(t_val)
            self.ID.append(v)  # goal SPACE id
            # Create a TimeWindowNode target with fresh id
            cur_max += 1
            target = TimeWindowNode(cur_max, "TimeWindow")
            self.ts_nodes.append(target)
            self.append_target(target)
            created_targets.append((v, target))
        return created_targets

    def _wire_targets_into_controller(self, created_targets: List[Tuple[int, TimeWindowNode]]) -> None:
        for (goal_space_id, target_node), e_val, t_val in zip(created_targets, self.earliness, self.tardiness):
            self.time_window_controller.add_source_and_TWNode(goal_space_id, target_node, e_val, t_val)

    def _materialize_time_window_edges(self, created_targets: List[Tuple[int, TimeWindowNode]]) -> None:
        # Cost follows the same formula used by TimeWindowController.
        M = getattr(self, "M", None)
        H = getattr(self, "H", None)
        d = getattr(self, "d", None)
        if M and H is not None and d:
            new_edges = set()
            for (goal_space_id, target_node), e_val, t_val in zip(created_targets, self.earliness, self.tardiness):
                for i in range(0, int(H) + 1):
                    if(i + d > H + 1): break
                    j = int(M) * i + int(goal_space_id)
                    # Compute penalty cost C
                    C = int(int(self.beta) * max(e_val - i, 0, i - t_val) / int(self.alpha))
                    new_edges.add((j, int(target_node.id), 0, 1, C))
            if new_edges:
                self.create_set_of_edges(new_edges)

    def _update_config_after_generation(self) -> None:
        config.started_nodes = list(self.started_nodes)
        config.ID = list(self.ID)
        config.earliness = list(self.earliness)
        config.tardiness = list(self.tardiness)
        config.numOfAGVs = len(self.ID)
        config.num_max_agvs = len(self.ID)