
import os
import matplotlib.pyplot as plt

class Visualizer:
    def __init__(self, node_to_xy, draw_background, save_dir="outputs/vis"):
        self.node_to_xy = node_to_xy
        self.draw_background = draw_background
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def show_round_static(self, agv_list, round_id, show=False, filename=None):
        fig, ax = plt.subplots(figsize=(10, 6))
        self.draw_background(ax)

        for agv in agv_list:
            path_dict = getattr(agv, "path", None)
            if not isinstance(path_dict, dict) or not path_dict:
                continue
            # sort by time
            items = sorted(path_dict.items(), key=lambda kv: kv[1])
            xs = []
            ys = []
            for node_id, _t in items:
                x, y = self.node_to_xy(node_id)
                xs.append(x)
                ys.append(y)
            ax.plot(xs, ys, marker="o", linewidth=1, label=f"AGV {getattr(agv, 'id', '?')}")

        ax.set_title(f"Round {round_id}")
        ax.legend(loc="upper right")
        if filename is None:
            filename = os.path.join(self.save_dir, f"round_{int(round_id):02d}.png")
        fig.savefig(filename, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        else:
            plt.close(fig)