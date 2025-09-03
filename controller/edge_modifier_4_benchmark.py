from controller.edge_modifier import EdgeModifier
from model.Node import Node


class EdgeModifier4Benchmark(EdgeModifier):
	def insertEdgesAndNodes(self, start, end, edge):
		fmt = getattr(self, "_input_format", None)

		if fmt == 'benchmark':
			start_id = start if isinstance(start, int) else start.id
			end_id = end if isinstance(end, int) else end.id

			if start_id not in self.graph.adjacency_list:
				self.graph.adjacency_list[start_id] = []
			if end_id not in self.graph.adjacency_list:
				self.graph.adjacency_list[end_id] = []

			# Append the directed edge
			self.graph.adjacency_list[start_id].append((end_id, edge))

			# Resolve Node objects and ensure node dict entries exist
			start_node = start if isinstance(start, Node) else self.find_node(start)
			end_node = end if isinstance(end, Node) else self.find_node(end)

			if start_id not in self.graph.nodes or self.graph.nodes[start_id] is None:
				self.graph.nodes[start_id] = start_node
			if end_id not in self.graph.nodes or self.graph.nodes[end_id] is None:
				self.graph.nodes[end_id] = end_node
		else:
			return super().insertEdgesAndNodes(start, end, edge)