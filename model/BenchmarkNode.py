from model.Node import Node

class BenchmarkNode(Node):
    def __init__(self, id, label=None):
        super().__init__(id, label)
        
class TopBulbNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "TopBulb")

class BottomBulbNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "BottomBulb")

class BottleneckNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "Bottleneck")