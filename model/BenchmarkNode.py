from model.Node import Node

class BenchmarkNode(Node):
    def __init__(self, id, label=None):
        super().__init__(id, label)
        
    def __repr__(self):
        cls = self.__class__.__name__
        lbl = getattr(self, "label", cls)
        tmp = getattr(self, "temporary", False)
        return f"{cls}(id={self.id}, label='{lbl}', temporary={tmp})"

class TopBulbNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "TopBulb")

class BottomBulbNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "BottomBulb")

class BottleneckNode(BenchmarkNode):
    def __init__(self, id):
        super().__init__(id, "Bottleneck")