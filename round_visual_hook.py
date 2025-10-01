import os
from model.Event import Event
from model.AGV import AGV
from visualization.renderer import Visualizer

def render_round(graph_processor, round_id, show=False):
    # Get M (number of columns in the grid)
    try:
        M = Event.getValue("number_of_nodes_in_space_graph")
        if not M or M <= 0:
            M = getattr(graph_processor, "M", None) or 1
    except Exception:
        M = getattr(graph_processor, "M", None) or 1

    def node_to_xy(node_id):
        # Default grid mapping:
        x = float(node_id % M)
        y = float(node_id // M)
        return x, y

    def draw_background(ax):
        ax.set_xlim(-1, M + 1)
        try:
            max_id = getattr(graph_processor.graph, "numberOfNodes", M*M)  # fallback
        except Exception:
            max_id = M*M
        rows = max(1, int(max_id // M) + 1)
        ax.set_ylim(-1, rows + 1)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.2)

    visualizer = Visualizer(node_to_xy=node_to_xy, draw_background=draw_background, save_dir="outputs/vis")
    agv_list = AGV.all_instances()
    visualizer.show_round_static(agv_list, round_id, show=show)