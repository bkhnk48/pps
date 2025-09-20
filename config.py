import platform
import getpass
import os
import re
import subprocess
import math
solver_choice = 'network-simplex'
started_nodes = []
ID = []
earliness = []
tardiness = []
filepath = ""
H = 0
d = 0
num_max_agvs = 0
numOfAGVs = 0
count = 0
reachingTargetAGVs = 0
haltingAGVs = 0
totalCost = 0
#sfm = False
functions_file = "functions.txt"
totalSolving = 0
timeSolving = 0
level_of_simulation = -1 #-1 - "BIMODAL", 0 - GAUSSIAN, 1 - "Random in the list", 2 - "SFM"
test_automation = 0
draw = 0
M = 0
print_output = False
numOfRestrictedRegions = 0
max_flow_conditions = None
artificial_upper_bound = None
artificial_gamma = None
BIMODAL = -1
GAUSSIAN = 0
count_set_traces = 0

def _try_import(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        return None

psutil = _try_import("psutil")
cpuinfo = _try_import("cpuinfo")

def get_username():
    # “Tên tài khoản chính” hiểu thực tế là user đang đăng nhập
    try:
        return getpass.getuser()
    except Exception:
        # fallback phổ thông
        return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"

def get_os_string():
    uname = platform.uname()
    # Ví dụ: 'Windows 11 (10.0.22631) x86_64', 'macOS 14.5 (arm64)', 'Linux 6.8.0-... (x86_64)'
    system = uname.system
    arch = uname.machine or "unknown-arch"
    if system == "Darwin":
        # macOS
        ver = platform.mac_ver()[0] or "unknown"
        return f"macOS {ver} ({arch})"
    elif system == "Windows":
        rel = uname.release or "unknown"
        ver = uname.version or ""
        return f"Windows {rel} ({ver}) {arch}".strip()
    else:
        # Linux / khác
        rel = uname.release or "unknown"
        return f"{system} {rel} ({arch})"

def get_cpu_model():
    # 1) py-cpuinfo (nếu có): chính xác, đa nền tảng
    if cpuinfo:
        info = cpuinfo.get_cpu_info()
        # thử các key phổ biến
        for k in ("brand_raw", "brand", "arch_string_raw"):
            if info.get(k):
                return info[k]

    # 2) macOS: sysctl
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"])
            return out.decode().strip()
        except Exception:
            pass
        # Apple Silicon đôi lúc hữu ích:
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.model"])
            return out.decode().strip()
        except Exception:
            pass

    # 3) Linux: /proc/cpuinfo
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            m = re.search(r"model name\s*:\s*(.+)", text)
            if m:
                return m.group(1).strip()
        except Exception:
            pass

    # 4) Windows / fallback: platform.processor()
    proc = platform.processor()
    if proc:
        return proc

    return "Unknown CPU"

def get_cpu_core_counts():
    logical = physical = None
    if psutil:
        try:
            logical = psutil.cpu_count(logical=True)
            physical = psutil.cpu_count(logical=False)
        except Exception:
            pass
    # Fallbacks
    if logical is None:
        try:
            logical = os.cpu_count()
        except Exception:
            logical = None
    return logical, physical

def get_ram_bytes():
    # Tổng RAM (bytes)
    if psutil:
        try:
            return psutil.virtual_memory().total
        except Exception:
            pass
    # macOS fallback
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"])
            return int(out.decode().strip())
        except Exception:
            pass
    # Linux fallback
    if platform.system() == "Linux":
        try:
            with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # ví dụ: "MemTotal:       32790192 kB"
                        parts = line.split()
                        kb = int(parts[1])
                        return kb * 1024
        except Exception:
            pass
    return None

def bytes_to_gb_str(nbytes):
    if not nbytes:
        return "Unknown"
    gb = nbytes / (1024**3)
    # in 1 chữ số thập phân, ví dụ “15.9 GB”
    return f"{gb:.1f} GB"

def describe_system():
    os_str = get_os_string()
    user = get_username()
    cpu = get_cpu_model()
    logical, physical = get_cpu_core_counts()
    ram = bytes_to_gb_str(get_ram_bytes())

    # Chuẩn bị chuỗi mô tả ngắn gọn
    core_part = []
    if physical:
        core_part.append(f"{physical} physical")
    if logical:
        core_part.append(f"{logical} logical")
    core_str = ", ".join(core_part) if core_part else "Unknown core count"

    description = (
        f"OS: {os_str}\n"
        f"User: {user}\n"
        f"CPU: {cpu} ({core_str})\n"
        f"RAM: {ram}"
    )
    # Đồng thời trả về cấu trúc dữ liệu nếu bạn muốn dùng tiếp
    info = {
        "os": os_str,
        "user": user,
        "cpu_model": cpu,
        "cpu_cores": {"physical": physical, "logical": logical},
        "ram_total": ram,
    }
    return description, info

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
