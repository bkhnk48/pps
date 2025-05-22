from controller.reading_input_processor import ReadingInputProcessor

class TimeWindowGenerator(ReadingInputProcessor):
    def __init__(self, dm):
        super().__init__(dm) 
        self._ts_edges = []
        
    # Getter và Setter cho ts_edges
    @property
    def ts_edges(self):
        return self._ts_edges
    
    @ts_edges.setter
    def ts_edges(self, value):
        if not isinstance(value, list):
            raise ValueError("ts_edges must be a list")
        self._ts_edges = value

    def add_time_window_first_time(self, num_of_agvs):
        count = 0

        while(count <= num_of_agvs - 1):
            #pdb.set_trace()
            if(isinstance(self.ID, int)):
                self.ID = 3
                self.earliness = 4 if count == 0 else 7
                self.tardiness = 6 if count == 0 else 9
                self.alpha = 1
                self.beta = 1

            self.add_time_windows_constraints()
            assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.tsedges)}"
            count += 1
