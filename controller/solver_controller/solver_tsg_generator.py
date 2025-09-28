from typing_extensions import override
import pdb
import config

#Sẽ được lớp TimeWindowGenerator kế thừa
class SolverTsgGenerator:
    def __init__(self):
        super().__init__() 
    
    def write_tw_declaration(self, target, earliness, tardiness, filename="TSG.txt"):
        if(config.solver_choice == 'solver'):
            pdb.set_trace()
            with open (filename, 'a') as file:
                file.write(f"c tw {target} {earliness} {tardiness}\n")