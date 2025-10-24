from controller.edge_modifier import EdgeModifier
from model.Node import Node
from model.BenchmarkNode import WaitingNode, TopBulbNode, BottomBulbNode, BottleneckNode


class EdgeModifier4Benchmark(EdgeModifier):
	# -------- Overrides --------
	def insertEdgesAndNodes(self, start, end, edge):
		fmt = getattr(self, "_input_format", None)
		if fmt != 'benchmark':
			return super().insertEdgesAndNodes(start, end, edge)

		start_id, end_id = self._get_ids(start, end)
		self._ensure_buckets(start_id, end_id)
		self.graph.adjacency_list[start_id].append((end_id, edge))
		self._ensure_nodes(start_id, end_id, start, end)

	# -------- New features --------
	def write_trace(self, flowDict, file_path: str = 'traces.txt'):
		# Lấy bảng chi phí không gian (u, v) -> [upper, cost]
		edges_with_costs = self.extract_edges_with_cost()
		M = self.M
		H = getattr(self, 'H', None)
		# Ghi file theo đúng format của NXSolution
		with open(file_path, 'w') as f:
			for key, sub_dict in getattr(flowDict, 'items', lambda: [])():
				for inner_key, inner_value in getattr(sub_dict, 'items', lambda: [])():
					if inner_value > 0:
						cost_override = None
						try:
							s_node = self.find_node(int(key))
							t_node = self.find_node(int(inner_key))
							if isinstance(s_node, (WaitingNode, TopBulbNode)) and isinstance(t_node, BottleneckNode):
								cost_override = 0
							elif isinstance(s_node, BottleneckNode) and isinstance(t_node, (WaitingNode, BottomBulbNode)):
								cost_override = 0
							elif isinstance(s_node, BottleneckNode) and isinstance(t_node, BottleneckNode):
								# Lấy chi phí của cạnh ngay trên TSG nếu có
								c_ts = self._get_ts_edge_cost(int(key), int(inner_key))
								if c_ts is not None:
									cost_override = c_ts
						except Exception:
							pass

						u = int(key) % M
						u = (M if (u == 0 and int(key) != 0) else u)
						v = int(inner_key) % M
						v = (M if (v == 0 and int(inner_key) != 0) else v)

						space_cost = edges_with_costs.get((u, v), [-1, -1])[1]
						cost = cost_override if cost_override is not None else space_cost
						result = inner_value * cost
						f.write(f"a {key} {inner_key} 0 + {result} = {result}\n")

	# -------- Helpers --------
	def _get_ids(self, start, end):
		start_id = start if isinstance(start, int) else start.id
		end_id = end if isinstance(end, int) else end.id
		return start_id, end_id

	def _ensure_buckets(self, start_id, end_id):
		adj = self.graph.adjacency_list
		if start_id not in adj:
			adj[start_id] = []
		if end_id not in adj:
			adj[end_id] = []

	def _ensure_nodes(self, start_id, end_id, start, end):
		nodes = self.graph.nodes
		if start_id not in nodes or nodes[start_id] is None:
			start_node = start if isinstance(start, Node) else self.find_node(start)
			nodes[start_id] = start_node
		if end_id not in nodes or nodes[end_id] is None:
			end_node = end if isinstance(end, Node) else self.find_node(end)
			nodes[end_id] = end_node

	def _get_ts_edge_cost(self, ts_u: int, ts_v: int):
		"""Trả về chi phí (weight) của cạnh thời-gian (ts_u -> ts_v) nếu tìm thấy trong self.ts_edges; ngược lại None."""
		edges = getattr(self, 'ts_edges', None)
		if not isinstance(edges, list) or not edges:
			return None
		for e in edges:
			u_id = getattr(getattr(e, 'start_node', None), 'id', None) if hasattr(e, 'start_node') else (e[0] if isinstance(e, (list, tuple)) and len(e) >= 2 else None)
			v_id = getattr(getattr(e, 'end_node', None), 'id', None) if hasattr(e, 'end_node') else (e[1] if isinstance(e, (list, tuple)) and len(e) >= 2 else None)
			if u_id == ts_u and v_id == ts_v:
				if hasattr(e, 'weight'):
					return getattr(e, 'weight', None)
				elif isinstance(e, (list, tuple)) and len(e) >= 5:
					return e[4]
		return None