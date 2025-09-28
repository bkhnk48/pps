# pathPlanningSimulation

## Instructions

### Prerequisites
- Architecture: x86_64 (Could be run on ARM64 but need to compile the `hallway_simulator_module` repository in that machine architecture)
- Platform: Linux (Recommended: Ubuntu 20.04/Ubuntu 22.04)
- Python version: 3.10 or higher
- OpenGL version: 4.6 or higher

### Clone the repository

Clone the main repository to your local machine using the following command:

```bash
git clone https://github.com/bkhnk48/pathPlanningSimulation.git --branch main
```

Clone the repository for `hallway_simulator_module` to your local machine using the following command:

```bash
git clone https://github.com/LTH3ar/hoangnv-sfm-fork.git --branch main
```

### Install the dependencies

Install the dependencies for the main repository using the following command:

```bash
pip install -r requirements.txt
```

Install the dependencies for the `hallway_simulator_module` repository using the following command:

```bash
# Install the dependencies for the hallway_simulator_module repository

sudo apt install build-essential \
                libglu1-mesa-dev \
                freeglut3-dev \
                mesa-common-dev \
                mesa-utils \
                libgl1-mesa-glx
```

Compile the `hallway_simulator_module` repository using the following command:

```bash
# Change directory to the cloned repository
cd <path to git cloned repository>/hoangnv-sfm-fork

# Compile the repository
make

# copy the compiled file to the main repository
cp app <path to git cloned repository>/pathPlanningSimulation/model/hallway_simulator_module/sim/x86_64/app
```

### Run the code

To run the code:

```bash
python3 main.py
```

The program then askes user to type the name of input file, user could type: `Redundant3x3Wards.txt`

For example:

```bash
python3 main.py

Choose the method for solving:
1 - Use LINK II solver
2 - Use parallel network-simplex
3 - Use NetworkX

Enter your choice (1 or 2 or 3): 

Invalid choice. Defaulting to Network X.

Choose to run sfm or not:

1 - Run sfm

0 - Not run sfm

Enter your choice (1 or 0): 

Invalid choice. Defaulting to run sfm.

Nhap ten file can thuc hien (hint: Redundant3x3Wards.txt): 

Nhap thoi gian can gia lap (default: 10): 900

Nhap time unit (default: 1): 10

Nhap so luong AGV toi da di chuyen trong toan moi truong (default: 4):10
```