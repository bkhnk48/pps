from controller.edge_modifier import EdgeModifier
from model.Node import Node


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