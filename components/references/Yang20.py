import numpy as np
import matplotlib.pyplot as plt
from queue import PriorityQueue
import random
from scipy.optimize import linear_sum_assignment
import csv
import json

# ==== MAP LOADER ====
def load_map_from_file(map_file):
    """
    Đọc file .map và chuyển thành lưới nhị phân: 0 là ô trống, 1 là chướng ngại vật
    """
    with open(map_file, 'r') as f:
        lines = f.readlines()
        height = int(lines[1].split()[1])
        width = int(lines[2].split()[1])
        map_data = [list(line.strip()) for line in lines[4:4+height]]
        grid = np.array([[0 if c == '.' else 1 for c in row] for row in map_data])
    return grid

# ==== AGENT GENERATOR ====
def generate_agents(grid, num_agents):
    """
    Chọn ngẫu nhiên các ô trống để đặt start và goal cho từng agent
    """
    free_cells = [(i, j) for i in range(grid.shape[0]) for j in range(grid.shape[1]) if grid[i, j] == 0]
    random.shuffle(free_cells)
    agents = []
    for i in range(num_agents):
        start = free_cells.pop()
        goal = free_cells.pop()
        agents.append({'id': i, 'start': start, 'goal': goal})
    return agents

# ==== STOCHASTIC EDGE COST SIMULATION ====
def simulate_stochastic_costs(grid):
    """
    Gán cho mỗi cạnh trong lưới một chi phí kỳ vọng (mu) và phương sai (sigma^2)
    """
    edge_mu = {}
    edge_var = {}
    for x in range(grid.shape[0]):
        for y in range(grid.shape[1]):
            if grid[x, y] == 0:
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx_, ny_ = x + dx, y + dy
                    if 0 <= nx_ < grid.shape[0] and 0 <= ny_ < grid.shape[1] and grid[nx_, ny_] == 0:
                        mu = np.random.randint(1, 5)
                        var = np.random.uniform(0.1, 1.0)
                        edge_mu[((x,y), (nx_,ny_))] = mu
                        edge_var[((x,y), (nx_,ny_))] = var
    return edge_mu, edge_var

# ==== RISK-AWARE COST FUNCTION ====
def risk_aware_cost(mu, sigma2, lambda_risk):
    """
    Tính chi phí rủi ro theo công thức: chi phí = mu + lambda * sigma^2
    """
    return mu + lambda_risk * sigma2

# ==== RISK-AWARE DIJKSTRA ====
def dijkstra_risk_aware(start, goal, edge_mu, edge_var, lambda_risk):
    """
    Biến thể của Dijkstra để tìm đường đi ngắn nhất theo hàm chi phí risk-aware
    """
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    while not frontier.empty():
        _, current = frontier.get()
        if current == goal:
            break
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            next_cell = (current[0]+dx, current[1]+dy)
            if ((current, next_cell) in edge_mu):
                mu = edge_mu[(current, next_cell)]
                var = edge_var[(current, next_cell)]
                r_cost = risk_aware_cost(mu, var, lambda_risk)
                new_cost = cost_so_far[current] + r_cost
                if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                    cost_so_far[next_cell] = new_cost
                    priority = new_cost
                    frontier.put((priority, next_cell))
                    came_from[next_cell] = current
    # Khôi phục đường đi
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from.get(current)
        if current is None:
            return []
    path.append(start)
    path.reverse()
    return path

# ==== VISUALIZER ====
def draw_map_with_paths(grid, agents, paths):
    """
    Vẽ bản đồ và đường đi của các agent lên đó
    """
    fig, ax = plt.subplots()
    ax.imshow(grid, cmap='gray_r')
    colors = ['r', 'g', 'b', 'c', 'm', 'y']
    for i, agent in enumerate(agents):
        path = paths[i]
        if not path:
            continue
        y, x = zip(*path)
        ax.plot(x, y, marker='o', color=colors[i % len(colors)], label=f'Agent {i}')
        ax.text(agent['start'][1], agent['start'][0], 'S', color='black', ha='center', va='center')
        ax.text(agent['goal'][1], agent['goal'][0], 'G', color='white', ha='center', va='center')
    ax.legend()
    plt.title('MAPF Risk-Aware Path Visualization')
    plt.show()

def auction_assignment(agents, edge_mu, edge_var, lambda_risk):
    """
    Thực hiện phân công nhiệm vụ dựa trên chi phí rủi ro (risk-aware cost).
    Phù hợp với ý tưởng thuật toán đấu giá (auction) trong bài báo:
    - Tính chi phí đến từng goal cho mỗi agent
    - Tối ưu assignment toàn cục bằng giải bài toán gán với hàm mục tiêu có rủi ro
    """
    num_agents = len(agents)
    cost_matrix = np.zeros((num_agents, num_agents))

    for i, agent in enumerate(agents):
        for j, other in enumerate(agents):
            path = dijkstra_risk_aware(agent['start'], other['goal'], edge_mu, edge_var, lambda_risk)
            cost = sum(risk_aware_cost(
                edge_mu.get((path[k], path[k+1]), 0),
                edge_var.get((path[k], path[k+1]), 0),
                lambda_risk
            ) for k in range(len(path)-1))
            cost_matrix[i][j] = cost

    # Hungarian Algorithm – tương ứng với bước giải bài toán gán tối ưu trong bài báo
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assigned = []
    for i in range(num_agents):
        assigned.append({
            'id': i,
            'start': agents[row_ind[i]]['start'],
            'goal': agents[col_ind[i]]['goal']
        })
    return assigned

# ==== VARIANCE–MEAN PARETO PLOT ====
def plot_variance_mean_plane(agents, edge_mu, edge_var, lambda_vals):
    """
    Vẽ mặt phẳng Pareto: thể hiện trade-off giữa chi phí kỳ vọng (mean) và rủi ro (variance)
    - Mỗi điểm biểu diễn kết quả ứng với một giá trị λ (tham số điều chỉnh độ nhạy với rủi ro)
    - Liên hệ trực tiếp với ý tưởng lựa chọn λ trong bài báo để cân bằng giữa tính khả thi và tối ưu
    """
    fig, ax = plt.subplots()
    for lam in lambda_vals:
        total_mu, total_var = 0, 0
        for ag in agents:
            path = dijkstra_risk_aware(ag['start'], ag['goal'], edge_mu, edge_var, lam)
            for k in range(len(path)-1):
                mu = edge_mu.get((path[k], path[k+1]), 0)
                var = edge_var.get((path[k], path[k+1]), 0)
                total_mu += mu
                total_var += var
        ax.scatter(total_mu, total_var, label=f"λ={lam}")
    ax.set_xlabel("Total Mean Cost")
    ax.set_ylabel("Total Variance")
    ax.set_title("Pareto Plane: Variance vs. Mean Cost")
    ax.legend()
    plt.show()
    
# ==== CONFLICT DETECTION ====
def detect_conflicts(paths):
    """
    Phát hiện xung đột: 2 agent đến cùng một ô tại cùng thời điểm.
    """
    time_dict = {}
    for t in range(max(len(p) for p in paths)):
        positions = [p[t] if t < len(p) else p[-1] for p in paths]
        for idx, pos in enumerate(positions):
            if pos in time_dict:
                return f"Conflict between agent {time_dict[pos]} and {idx} at time {t} on {pos}"
            time_dict[pos] = idx
        time_dict.clear()
    return "No conflicts detected."

# ==== EXPORT TO CSV ====
def export_paths_to_csv(paths, filename="paths.csv"):
    """
    Ghi đường đi của từng agent ra file CSV để theo dõi hoặc vẽ bằng công cụ khác.
    """
    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["AgentID", "Step", "X", "Y"])
        for agent_id, path in enumerate(paths):
            for step, (x, y) in enumerate(path):
                writer.writerow([agent_id, step, x, y])

# ==== EXPORT TO JSON ====
def export_to_json(agents, paths, filename="solution.json"):
    """
    Xuất cấu trúc agent và path dưới dạng JSON để dùng lại hoặc chia sẻ.
    """
    data = []
    for agent, path in zip(agents, paths):
        data.append({
            "id": agent['id'],
            "start": agent['start'],
            "goal": agent['goal'],
            "path": path
        })
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


# ==== MAIN DEMO ====
if __name__ == "__main__":
    map_path = "warehouse-10-20-10-2-1.map"
    grid = load_map_from_file(map_path)
    agents = generate_agents(grid, num_agents=3)
    edge_mu, edge_var = simulate_stochastic_costs(grid)
    lambda_risk = 2.0  # hệ số nhạy cảm rủi ro

    # Bước 1: phân công nhiệm vụ bằng đấu giá có xét rủi ro
    assigned_agents = auction_assignment(agents, edge_mu, edge_var, lambda_risk)

    # Bước 2: tìm đường đi cho từng agent theo assignment trên
    paths = [dijkstra_risk_aware(ag['start'], ag['goal'], edge_mu, edge_var, lambda_risk) for ag in assigned_agents]

    # Bước 3: kiểm tra xung đột giữa các agent
    print(detect_conflicts(paths))

    # Bước 4: vẽ bản đồ và đường đi
    draw_map_with_paths(grid, assigned_agents, paths)

    # Bước 5: vẽ mặt phẳng Pareto – lựa chọn λ tối ưu như trong bài báo
    lambda_values = [0.0, 0.5, 1.0, 2.0, 4.0]
    plot_variance_mean_plane(assigned_agents, edge_mu, edge_var, lambda_values)

    # Bước 6: xuất kết quả ra file CSV và JSON
    export_paths_to_csv(paths)
    export_to_json(assigned_agents, paths)
    print("Exported solution to CSV and JSON.")

